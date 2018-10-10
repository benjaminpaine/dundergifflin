#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import psycopg2
import re
import os
import traceback
from dundergifflin.util import md5sum, logger
from dundergifflin.srt import Subtitles

class Database(object):
  """
  A small database wrapper around a PostgreSQL database.

  Builds only one database connection, not a pool.
  Uses a context manager to open/close the connection on enter/exit.

  Parameters
  ----------
  host : string
    The host of the database. If deployed on the same machine, localhost.
  port : int
    The port to access the database. The default PostgreSQL port is 5432.
  database_name : string
    The name of the database to connect to.
  username : string
    The username of the user. Should be a superuser of the target database.
  password : string
    The password for said user.
  """
  def __init__(self, host, port, database_name, username, password):
    self.database_name = database_name
    self.username = username
    self.password = password

  def test_connection(self):
    """
    Tests a connection by executing a simple query.
    
    Returns
    -------
    boolean
      Whether or not the connection is working.
    """
    try:
      cursor = self.connection.cursor()
      cursor.execute("SELECT 1")
      row = cursor.fetchone()
      assert row[0] == 1
    except:
      return False
    return True

  def get_connection(self):
    """
    Retrieve a connection to the database.

    Will test the connection if one already exists, or recreate it if it has been closed.

    Returns
    -------
    psycopg2.connection
      A psycopg2 connection object to the database.
    """
    if hasattr(self, "connection") and not self.connection.closed:
      if self.test_connection():
        return self.connection
    self.connection = psycopg2.connect(
      dbname = self.database_name, 
      user = self.username, 
      password = self.password, 
      host = self.host, 
      port = int(self.port)
    )
    return self.connection

  def __enter__(self):
    return self

  def __exit__(self, *args):
    try:
      self.connection.close()
    except:
      pass

class DunderDatabase(Database):
  """
  A wrapper around a subtitle database.

  Will ensure the database is migrated, then crawl the configured directory for .srt files.
  If the .srt file is not in the database, or has changed since the last crawl, will upsert its data.

  Parameters
  ----------
  host : string
    The host of the database. If deployed on the same machine, localhost.
  port : int
    The port to access the database. The default PostgreSQL port is 5432.
  database_name : string
    The name of the database to connect to.
  username : string
    The username of the user. Should be a superuser of the target database.
  password : string
    The password for said user.
  directory : string
    The directory in which to find .srt files. There is an expected structure
    of the directory:
      -- <top_directory>
         +-- S<n>
             +-- E<m>.srt
    For each S<n>, a "season" will be parsed, and each E<m> represents an episode.
  concatenation_depth : int
    Determines how deep to concatenate lines into the database. 
    
    Concatenating lines will take multiple subtitles and concatenate them together (with newlines),
    then set the start time to be the start of the first line, and the end time to the end of
    the last time.

    This will multiply the storage required and lookup time of each episode by the number
    passed in.
  """
  SUBTITLE_MIGRATION = """
  BEGIN;

  SET search_path = public, pg_catalog;

  CREATE EXTENSION IF NOT EXISTS pg_trgm;

  CREATE TABLE IF NOT EXISTS subtitles (
    season SMALLINT NOT NULL,
    episode SMALLINT NOT NULL,
    start_index INT NOT NULL,
    end_index INT NOT NULL,
    start_time NUMERIC,
    end_time NUMERIC,
    subtitle TEXT,
    PRIMARY KEY (season, episode, start_index, end_index)
   );

  CREATE TABLE IF NOT EXISTS srt (
    path VARCHAR NOT NULL,
    md5sum VARCHAR NOT NULL,
    PRIMARY KEY (path)
  );

  CREATE TABLE IF NOT EXISTS users (
    username VARCHAR NOT NULL,
    ignore BOOLEAN NOT NULL DEFAULT FALSE,
    uses INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (username)
  );

  CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR NOT NULL,
    score INTEGER NOT NULL DEFAULT 1,
    season SMALLINT NOT NULL,
    episode SMALLINT NOT NULL,
    start_index INT NOT NULL,
    end_index INT NOT NULL,
    PRIMARY KEY (comment_id)
  );

  CREATE TABLE IF NOT EXISTS kv_store (
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    mod_time TIMESTAMP DEFAULT NOW(),
    exp_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (key)
  );

  DO $$
  BEGIN
    IF NOT EXISTS (
      SELECT 1
      FROM pg_constraint
      WHERE conname = 'comments_subtitles_fkey'
    ) THEN
      ALTER TABLE ONLY comments
      ADD CONSTRAINT comments_subtitles_fkey
      FOREIGN KEY (season, episode, start_index, end_index)
      REFERENCES subtitles (season, episode, start_index, end_index)
      ON DELETE RESTRICT;
    END IF;
  END;
  $$ LANGUAGE plpgsql;

  CREATE INDEX IF NOT EXISTS trigram_index ON subtitles USING GIST (subtitle gist_trgm_ops);

  COMMIT;
  """
  def __init__(self, host, port, database_name, username, password, directory, concatenation_depth = 2):
    super(DunderDatabase, self).__init__(host, port, database_name, username, password)
    self.directory = directory
    self.concatenation_depth = concatenation_depth
    self._migrate()
    self._crawl_subtitles()

  def find_subtitles(self, text, limit = 10):
    """
    Find the closest subtitles to a line of text.

    Returns in descending order of likeness, where likeness is 1 minus the pg_trgrm operation "<->".
    A likeness of 1 represents a 100% match (excluding punctuation and capitalization).

    Parameters
    ----------
    text : string
      The text to search for.
    limit : int
      The number of rows to return.

    Returns
    -------
    list
      season : int
        The season this subtitle is from.
      episode : int
        The episode this subtitle is from.
      start_index : int
        The starting index of the line.
      end_index : int
        The ending index of the line.
      start_time : string
        The start time of the line, in the form HH:MM:SS.ff
      end_time : string
        The end time of the line, in the form HH:MM:SS.ff
      subtitle : string
        The actual subtitle, including punctuation.
      likeness : float
        The likeness of this line, between 1 (~exact match) and 0 (no match).
      comment_count : int
        The number of times this/these line(s) has/have been referenced.
      comment_score : float
        The average comment score of this/these line(s).
    
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT subtitles.season, 
             subtitles.episode, 
             subtitles.start_index, 
             subtitles.end_index,
             subtitles.start_time,
             subtitles.end_time,
             subtitles.subtitle,
             (1 - (subtitles.subtitle <-> %s)) AS likeness,
             COUNT(comments.comment_id) AS comment_count,
             AVG(comments.score) AS comment_score
      FROM subtitles
      LEFT OUTER JOIN comments
      ON comments.season = subtitles.season
      AND comments.episode = subtitles.episode
      AND comments.start_index = subtitles.start_index
      AND comments.end_index = subtitles.end_index
      WHERE subtitles.subtitle %% %s 
      GROUP BY subtitles.season, 
               subtitles.episode, 
               subtitles.start_index, 
               subtitles.end_index, 
               subtitles.start_time, 
               subtitles.end_time, 
               subtitles.subtitle
      ORDER BY subtitles.subtitle <-> %s ASC
      LIMIT {0}
      """.format(limit), (text, text, text)
    )
    return cursor.fetchall()

  def get_user_ignored(self, username):
    """
    Get whether or not a user has requested to be ignored.

    Parameters
    ----------
    username : string
      The username of the requested user.

    Returns
    -------
    boolean
      Whether or not the user has requested to be ignored.      
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT ignore
      FROM users
      WHERE username = %s
      """, (username,)
    )
    row = cursor.fetchone()
    if not row:
      return False
    return row[0]
  
  def get_user_uses(self, username):
    """
    Get the number of time a user has used the service.

    Parameters
    ----------
    username : string
      The username of the requested user.

    Returns
    -------
    int
      How many times the user has used the service.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT uses
      FROM users
      WHERE username = %s
      """, (username,)
    )
    row = cursor.fetchone()
    if not row:
      return 0
    return row[0]

  def ignore_user(self, username):
    """
    Set a user to be ignored.

    Parameters
    ----------
    username : string
      The username of the requested user.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT EXISTS (
        SELECT 1
        FROM users
        WHERE username = %s
      )
      """, (username,)
    )
    if cursor.fetchone()[0]:
      cursor.execute(
        """
        UPDATE users
        SET ignore = TRUE
        WHERE username = %s
        """, (username,)
      )
      self.get_connection().commit()
    else:
      cursor.execute(
        """
        INSERT INTO users (username, ignore)
        VALUES (%s, TRUE)
        """, (username,)
      )
      self.get_connection().commit()

  def increment_user_uses(self, username):
    """
    Increment a users' uses of the service.

    Parameters
    ----------
    username : string
      The username of the requested user.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT EXISTS (
        SELECT 1
        FROM users
        WHERE username = %s
      )
      """, (username,)
    )
    if cursor.fetchone()[0]:
      cursor.execute(
        """
        UPDATE users
        SET uses = uses + 1
        WHERE username = %s
        """, (username,)
      )
      self.get_connection().commit()
    else:
      cursor.execute(
        """
        INSERT INTO users (username)
        VALUES (%s)
        """, (username,)
      )
      self.get_connection().commit()

  def get_key(self, key):
    """
    Get the value from the key/value store.

    Parameters
    ----------
    key : string
      An unbounded key to search against.

    Returns
    -------
    list
      value : string
        The value stored in the database. Can be None.
      exp_time : datetime.datetime
        The expiration time, if set. Can be None.
      mod_time : datetime.datetime
        The last time this value was modified. Can be None.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT value,
             exp_time,
             mod_time
      FROM kv_store
      WHERE key = %s
      """, (key,)
    )
    row = cursor.fetchone()
    if not row:
      return [None, None, None]
    return row

  def upsert_key(self, key, value, exp_time = None):
    """
    Set a key/value pair in the key/value store.

    Parameters
    ----------
    key : string
      An unbounded key - the primary key.
    value : string
      An unbounded value - what to store.
    exp_time : datetime.datetime:
      The time to expire this key. Purely for informational purposes, does not
      influence the store itself. Can be None.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT EXISTS (
        SELECT 1 
        FROM kv_store
        WHERE key = %s
      )
      """, (key,)
    )
    if cursor.fetchone()[0]:
      cursor.execute(
        """
        UPDATE kv_store
        SET value = %s,
            mod_time = NOW(),
            exp_time = %s
        WHERE key = %s
        """, (value, exp_time, key)
      )
      self.get_connection().commit()
    else:
      cursor.execute(
        """
        INSERT INTO kv_store (
          key,
          value,
          mod_time
        ) VALUES (
          %s, 
          %s, 
          %s
        )
        """, (key, value, mod_time)
      )
      self.get_connection().commit()
  
  def upsert_comment(self, comment_id, score, season, episode, start_index, end_index):
    """
    Insert or update a comment into the comment database.

    Parameters
    ----------
    comment_id : string
      The comment ID returned from Reddit. Primary key.
    score : int
      The score of the comment from Reddit.
    season : int
      The season of the responded image / comment.
    episode : int
      The episode of the responded image / comment.
    start_index : int
      The starting line index of the responded image / comment.
    end_index : int
      The ending line index of the responded image / comment.
    """
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT EXISTS (
        SELECT 1 
        FROM comments 
        WHERE comment_id = %s
      )
      """, (comment_id,)
    )
    if cursor.fetchone()[0]:
      cursor.execute(
        """
        UPDATE comments
        SET score = %s
        WHERE comment_id = %s
        """, (score, comment_id)
      )
      self.get_connection().commit()
    else:
      cursor.execute(
        """
        INSERT INTO comments (
          comment_id,
          season,
          episode,
          start_index,
          end_index,
          score
        ) VALUES (
          %s, 
          %s, 
          %s, 
          %s, 
          %s,
          %s
        )
        """, (comment_id, season, episode, start_index, end_index, score)
      )
      self.get_connection().commit()

  def _migrate(self):
    """
    Runs the default migration against the database. Checked on instantiation.
    """
    logger.debug("Checking database migration.")
    cursor = self.get_connection().cursor()
    cursor.execute(DunderDatabase.SUBTITLE_MIGRATION)
    self.get_connection().commit()
    self.get_connection().close()

  def _crawl_subtitles(self):
    """
    Crawl through the directory for subtitles and update the database accordingly. Called on instantiation.
    """
    cursor = self.get_connection().cursor()
    for season in os.listdir(self.directory):
      if season.lower().startswith("s") and os.path.isdir(os.path.join(self.directory, season)):
        season_directory = os.path.join(self.directory, season)
        try:
          season_number = int(re.sub(r"\D", "", season))
          for filename in os.listdir(season_directory):
            if filename.endswith(".srt") and filename.lower().startswith("e"):
              subtitle_path = os.path.join(season_directory, filename)
              try:
                md5 = md5sum(subtitle_path)
                episode_number = int(re.sub(r"\D", "", filename))
                cursor.execute("SELECT md5sum FROM srt WHERE path = %s", (subtitle_path,))
                row = cursor.fetchone()
                if not row or row[0] != md5:
                  logger.info("New or changed subtitle file '{0}' found (season {1}, episode {2}), crawling.".format(
                    subtitle_path,
                    season_number,
                    episode_number
                  ))
                  cursor.execute(
                    """
                    DELETE FROM subtitles 
                    WHERE season = %s 
                    AND episode = %s
                    """, (season_number, episode_number)
                  )
                  cursor.execute(
                    """
                    DELETE FROM srt 
                    WHERE path = %s
                    """, (subtitle_path,)
                  )
                  self.get_connection().commit()
                  subtitles = Subtitles(subtitle_path)
                  for j in range(self.concatenation_depth):
                    for i in range(len(subtitles.subtitles) - j):
                      start_subtitle = subtitles.subtitles[i]
                      end_subtitle = subtitles.subtitles[i+j]
                      text = " ".join([
                        subtitle.text 
                        for subtitle 
                        in subtitles.subtitles[i:i+j+1]
                      ])
                      cursor.execute(
                        """
                        INSERT INTO subtitles (
                          season, 
                          episode, 
                          start_index, 
                          end_index,
                          start_time, 
                          end_time, 
                          subtitle
                        ) VALUES (
                          %s, 
                          %s, 
                          %s, 
                          %s, 
                          %s, 
                          %s,
                          %s
                        )""", (
                          season_number, 
                          episode_number, 
                          i, 
                          i + j,
                          start_subtitle.start.total_seconds(),
                          end_subtitle.end.total_seconds(),
                          text
                        )
                      )
                  cursor.execute(
                    """
                    INSERT INTO srt (
                      path, 
                      md5sum
                    ) VALUES (
                      %s, 
                      %s
                    )""", (subtitle_path, md5)
                  )
                  self.get_connection().commit()
              except Exception as ex:
                logger.error("Could not parse SRT file at path '{0}', reason: {1}(): {2}".format(
                  subtitle_path,
                  type(ex).__name__,
                  str(ex)  
                ))
                logger.error(traceback.format_exc(ex))
                cursor = self.get_connection().cursor()
                continue
        except Exception as ex:
          logger.error("Could not find season number in directory '{0}', continuing.".format(season_directory))
          cursor = self.get_connection().cursor()
          continue
