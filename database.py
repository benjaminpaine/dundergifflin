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
  def __init__(self, database_name, username, password):
    self.database_name = database_name
    self.username = username
    self.password = password

  def test_connection(self):
    try:
      cursor = self.connection.cursor()
      cursor.execute("SELECT 1")
      row = cursor.fetchone()
      assert row[0] == 1
    except:
      return False
    return True

  def get_connection(self):
    if hasattr(self, "connection") and not self.connection.closed:
      if self.test_connection():
        return self.connection
    self.connection = psycopg2.connect("dbname={0} user={1} password={2} host='127.0.0.1'".format(
      self.database_name,
      self.username,
      self.password
    ))
    return self.connection

  def __enter__(self):
    return self

  def __exit__(self, *args):
    try:
      self.connection.close()
    except:
      pass

class SubtitleDatabase(Database):
  SUBTITLE_MIGRATION = """
  BEGIN;

  SET search_path = public, pg_catalog;

  CREATE EXTENSION IF NOT EXISTS pg_trgm;

  CREATE TABLE IF NOT EXISTS subtitles (
    season SMALLINT NOT NULL,
    episode SMALLINT NOT NULL,
    index BIGINT NOT NULL,
    start_time NUMERIC,
    end_time NUMERIC,
    subtitle TEXT,
    PRIMARY KEY (season, episode, index)
   );

  CREATE TABLE IF NOT EXISTS srt (
    path VARCHAR NOT NULL,
    md5sum VARCHAR NOT NULL,
    PRIMARY KEY (path)
  );

  CREATE TABLE IF NOT EXISTS ignore (
    text VARCHAR NOT NULL,
    mentions INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (text)
  );

  CREATE INDEX IF NOT EXISTS trigram_index ON subtitles USING GIST (subtitle gist_trgm_ops);

  COMMIT;
  """
  def __init__(self, database_name, username, password, directory):
    super(SubtitleDatabase, self).__init__(database_name, username, password)
    self.directory = directory
    self.migrate()
    self.crawl()

  def ignored(self, text):
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT mentions
      FROM ignore
      WHERE text %% %s
      AND (1 - (text <-> %s)) > 0.90
      ORDER BY text <-> %s ASC
      LIMIT 1
      """, (text, text, text)
    )
    row = cursor.fetchone()
    if not row:
      return 0
    return row[0]

  def find(self, text, maximum_ignored_mentions = 5):
    ignored_mentions = self.ignored(text)
    if ignored_mentions > maximum_ignored_mentions:
      logger.info("Ignoring text '{0}' due to {1} mentions to ignore.".format(text, ignored_mentions))
      return
    cursor = self.get_connection().cursor()
    cursor.execute(
      """
      SELECT season, episode, index, 
      start_time, end_time, subtitle, 
      (1 - (subtitle <-> %s)) AS likeness 
      FROM subtitles 
      WHERE subtitle %% %s 
      ORDER BY subtitle <-> %s ASC 
      LIMIT 1
      """, (text, text, text)
    )
    row = cursor.fetchone()
    if row:
      return row

  def migrate(self):
    logger.debug("Checking database migration.")
    cursor = self.get_connection().cursor()
    cursor.execute(SubtitleDatabase.SUBTITLE_MIGRATION)
    self.get_connection().commit()
    self.get_connection().close()

  def crawl(self):
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
                  cursor.execute("DELETE FROM subtitles WHERE season = %s AND episode = %s", (season_number, episode_number))
                  cursor.execute("DELETE FROM srt WHERE path = %s", (subtitle_path,))
                  self.get_connection().commit()
                  
                  subtitles = Subtitles(subtitle_path)
                  for i, subtitle in enumerate(subtitles.subtitles):
                    cursor.execute("INSERT INTO subtitles (season, episode, index, start_time, end_time, subtitle) VALUES (%s, %s, %s, %s, %s, %s)", (season_number, episode_number, i, subtitle.start.total_seconds(), subtitle.end.total_seconds(), subtitle.text))
                  cursor.execute("INSERT INTO srt (path, md5sum) VALUES (%s, %s)", (subtitle_path, md5))
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
