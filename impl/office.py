#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
import os
import itertools
import re
import time
import traceback
import dundergifflin
import logging

from dundergifflin.ffmpeg import SubtitleConverter
from dundergifflin.config import Configuration
from dundergifflin.util import Timestamp, logger
from dundergifflin.database import DunderDatabase
from dundergifflin.reddit import RedditCrawler
from dundergifflin.imgur import Imgur
from dundergifflin.smtp_alert import SMTPAlert

body_search_regex = re.compile(r"[«‹»›„‚“‟‘‛”’\"❛❜❟❝❞❮❯⹂〝〞〟＂<>\[\]](.*?)[«‹»›„‚“‟‘‛”’\"❛❜❟❝❞❮❯⹂〝〞〟＂<>\[\]]")
comment_search_regex_1 = re.compile(r".*?Season.*?(?P<season>\d+).*?Episode.*?(?P<episode>\d+).*?Line.*?(?P<line>\d+).*?")
comment_search_regex_2 = re.compile(r".*?Season.*?(?P<season>\d+).*?Episode.*?(?P<episode>\d+).*?Lines.*?(?P<line_1>\d+)-(?P<line_2>\d+).*?")

configuration_directory = os.path.join(os.path.expanduser("~"), "dundergifflin")

if not os.path.isdir(configuration_directory):
  sys.stderr.write("Configuration directory does not exist at {0}, exiting.\n".format(configuration_directory))
  sys.stderr.flush()
  sys.exit(5)

configuration_file = os.path.join(configuration_directory, "office_config")
if not os.path.exists(configuration_file):
  sys.stderr.write("Configuration file does not exist at {0}, exiting.\n".format(configuration_file))
  sys.stderr.flush()
  sys.exit(5)

class OfficeConverter(SubtitleConverter):
  def __init__(self, season, episode, output_file, start, end, text):
    super(OfficeConverter, self).__init__(
      os.path.join(configuration_directory, "media", "office", "S{0:02d}".format(season), "E{0:02d}.mkv".format(episode)),
      output_file,
      True,
      start,
      end,
      text,
      configuration.IMAGE_WIDTH,
      configuration.TEXT_FONT,
      configuration.TEXT_COLOR,
      configuration.TEXT_SIZE_MAX,
      configuration.TEXT_OFFSET,
      configuration.TEXT_STROKE_WIDTH
    )

class OfficeConfiguration(Configuration):
  REQUIRED_KEYS = [
    "IMAGE_WIDTH",
    "TEXT_FONT",
    "TEXT_STROKE_WIDTH",
    "TEXT_SIZE_MAX",
    "TEXT_COLOR",
    "TEXT_OFFSET",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "REDDIT_USERNAME",
    "REDDIT_PASSWORD",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
    "REDDIT_SUBREDDITS",
    "REDDIT_MINIMUM_LIKENESS"
  ]
  def __init__(self, configuration_file):
    super(OfficeConfiguration, self).__init__(configuration_file)
    for required_key in OfficeConfiguration.REQUIRED_KEYS:
      if not hasattr(self, required_key):
        raise Exception("Required key '{0}' missing from configuration.".format(required_key))
    
configuration = OfficeConfiguration(configuration_file)

def format_comment(url, text, season, episode, start_index, end_index, comment_count, comment_score, uses, likeness, minimum_likeness, username):
  return """>[{0:s}]({1:s})

>Season {2:02d}, Episode {3:02d}, Line{4:s}

I'm a bot that parses comments for quotes from The Office. I found your comment to contain a quote {5:d}% like this. This quote has been mentioned {6:d} times{7:s}.{8:s}

+ Want me to ignore your comments from now on? Reply **ignore me** to this comment. Have I ignored you accidentally? Shoot me a PM.

+ Should I ignore this quote from now on? Did I make a mistake? Simply **downvote this comment**.

+ I only reply to comments that are >={9:d}% like a quote I found. Want to invoke me to find the closest I can? Start your comment with !{10:s}.

+ Want to make a quote bot for your favorite show? [Check out my source code.](https://github.com/benjaminpaine/dundergifflin). Have suggestions or want me to visit your subreddit? Post in /r/dundergifflin!""".format(
    text,
    url,
    season,
    episode,
    " {0:d}".format(start_index+1) if start_index == end_index else "s {0:d}-{1:d}".format(start_index+1, end_index+1),
    int(likeness*100),
    comment_count,
    ", and has an average score of {0:.2f}".format(comment_score) if comment_score is not None else "",
    " You've used me {0} time{1}!".format(
      uses,
      "s" if uses > 1 else ""
    ) if uses is not None and uses != 0 else "",
    int(minimum_likeness*100),
    username
  )

def main(conn = None, logger = None):
  if logger is None:
    logger = logging.getLogger("dunder-gifflin")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

  alerter = SMTPAlert(
    configuration.EMAIL_ALERT_HOST,
    configuration.EMAIL_ALERT_PORT,
    configuration.EMAIL_ALERT_USERNAME,
    configuration.EMAIL_ALERT_PASSWORD,
    configuration.EMAIL_ALERT_USE_TLS
  )

  try:
    with DunderDatabase(
      configuration.DATABASE_HOST,
      configuration.DATABASE_PORT,
      configuration.DATABASE_NAME,
      configuration.DATABASE_USER,
      configuration.DATABASE_PASSWORD,
      os.path.join(configuration_directory, "media", "office"),
      configuration.DATABASE_CONCATENATION_DEPTH
    ) as database:

      with Imgur(
        configuration.IMGUR_CLIENT_ID, 
        configuration.IMGUR_CLIENT_SECRET,
        configuration.IMGUR_AUTHORIZATION_LISTEN_ADDRESS,
        configuration.IMGUR_AUTHORIZATION_LISTEN_PORT,
        database.get_key("imgur_refresh_token")[0]
      ) as imgur:

        database.upsert_key("imgur_refresh_token", imgur.refresh_token)

        def comment_function(comment):
          if conn is not None:
            conn.send("comment_evaluated")

          try:
            body = comment.body.strip()
            author = comment.author
            if author is not None:
              if database.get_user_ignored(author.name):
                logger.info("Ignoring post from user '{0}'.".format(author.name))
                return
            force = body.startswith("!{0}".format(configuration.REDDIT_USERNAME)) or body.startswith("!{0}".format(configuration.REDDIT_USERNAME.replace("_","\\_")))

            if force:
              body = body[len(configuration.REDDIT_USERNAME.replace("_", "\\_"))+1:].strip()

            if len(body) < configuration.REDDIT_MINIMUM_LENGTH:
              logger.info("Ignoring text body '{0}': too short.".format(body))
              if force:
                return "Sorry{0}, that message is a bit too short. I try to avoid short phrases as they're overly common in subtitles.".format(
                  " /u/{0}".format(author.name) if author is not None else ""
                )
              return

            logger.debug("Checking for text '{0}'.".format(body))
            check_text = body
            subtitles = database.find_subtitles(check_text)
            if not subtitles:
              logger.debug("Nothing found, looking for quotes.")
              # Search for text within quotations.
              for match in body_search_regex.findall(body):
                check_text = match
                subtitles = database.find_subtitles(check_text)
                if subtitles:
                  break
            if subtitles:
              for season, episode, start_index, end_index, start_time, end_time, text, likeness, comment_count, comment_score in subtitles:
                text = text.decode("utf-8")
                if force or (likeness > configuration.REDDIT_MINIMUM_LIKENESS):
                  if not force and (comment_score is not None and comment_score < configuration.REDDIT_IGNORE_THRESHOLD):
                    logger.debug("Skipping season {0}, episode {1}, line {2}-{3} due to ignore threshold.".format(
                      season,
                      episode,
                      start_index,
                      end_index
                    ))
                    continue
                  logger.debug("Text: {0}\nLikeness:{1}\nSeason {2}\nEpisode {3}\nMentions {4}\nScore {5}\n{6} --> {7}\n{8}".format(
                    check_text,
                    likeness,
                    season,
                    episode,
                    comment_count,
                    comment_score,
                    Timestamp.from_string(str(start_time)),
                    Timestamp.from_string(str(end_time)),
                    text
                  ))

                  file_path = "s{0:02d}_e{1:02d}_l{2:d}_l{2:d}.gif".format(season, episode, start_index, end_index)

                  OfficeConverter(
                    season, 
                    episode, 
                    file_path,
                    Timestamp.from_string(str(start_time)), 
                    Timestamp.from_string(str(end_time)), 
                    text
                  ).execute()

                  url = imgur.upload(
                    file_path,
                    "The Office, Season {0:02d}, Episode {1:02d}".format(season, episode),
                    comment.permalink
                  )

                  os.remove(file_path)

                  if author is not None:
                    logger.debug("Incrementing uses for author '{0}'.".format(author.name))
                    database.increment_user_uses(author.name)
                    uses = database.get_user_uses(author.name)
                  else:
                    uses = None
                  if conn is not None:
                    conn.send("comment_made")
                  return format_comment(
                    url, 
                    text, 
                    season, 
                    episode, 
                    start_index,
                    end_index,
                    comment_count,
                    comment_score,
                    uses,
                    likeness,
                    configuration.REDDIT_MINIMUM_LIKENESS, 
                    configuration.REDDIT_USERNAME
                  )
                else:
                  logger.debug("Found likeness {0} for string '{1}' ('{2}'), but does not exceed minimum likeness.".format(
                    likeness,
                    check_text,
                    text
                  ))
                  return
            elif force:
              return "Sorry{0}, I couldn't find any quotes with that phrase.".format(
                " /u/{0}".format(author.name) if author is not None else ""
              )
          except Exception as ex:
            logger.error("Receieved an exception when posting a comment.\n\n{0}(): {1}\n\n{2}".format(
              type(ex).__name__,
              str(ex),
              traceback.format_exc(ex)
            ))
            raise ex

        def vote_function(comment):
          if conn is not None:
            conn.send("vote_evaluated")
          if comment.body.strip().startswith("Sorry"):
            return
          for line in comment.body.splitlines():
            m = comment_search_regex_2.search(line)
            if m:
              season = int(m.group("season"))
              episode = int(m.group("episode"))
              line_1 = int(m.group("line_1")) - 1
              line_2 = int(m.group("line_2")) - 1
              logger.info("Upserting comment ID '{0}' into comment database. (season {1}, episode {2}, lines {3}-{4}, score {5})".format(comment, season, episode, line_1, line_2, comment.score))
              database.upsert_comment(str(comment), comment.score, season, episode, line_1, line_2)
              return
            m = comment_search_regex_1.search(line)
            if m:
              season = int(m.group("season"))
              episode = int(m.group("episode"))
              line = int(m.group("line")) - 1
              logger.info("Upserting comment ID '{0}' into comment database. (season {1}, episode {2}, line {3}, score {4})".format(comment, season, episode, line, comment.score))
              database.upsert_comment(str(comment), comment.score, season, episode, line, line)
              return
          logger.error("Could not parse information from comment ID '{0}'. Body:\n{1}".format(comment, comment.body))

        def reply_function(comment):
          if conn is not None:
            conn.send("reply_evaluated")
          if comment.author is not None:
            if comment.body.lower().find("ignore me") != -1:
              if conn is not None:
                conn.send("user_ignored")
              logger.info("Ignoring user '{0}' by request.".format(comment.author.name))
              database.ignore_user(comment.author.name)
            
        with RedditCrawler(
          configuration.REDDIT_CLIENT_ID, 
          configuration.REDDIT_CLIENT_SECRET, 
          configuration.REDDIT_USERNAME, 
          configuration.REDDIT_PASSWORD, 
          configuration.REDDIT_USER_AGENT, 
          comment_function,
          vote_function,
          reply_function,
          *configuration.REDDIT_SUBREDDITS.split(",")
        ) as crawler:
          while True:
            time.sleep(60)

  except Exception as ex:
    logger.error("Receieved an exception during normal operation.\n\n{0}(): {1}\n\n{2}".format(
      type(ex).__name__,
      str(ex),
      traceback.format_exc(ex)
    ))
  else:
    logger.error("Reddit bot has stopped!")

if __name__ == "__main__":
  main()
