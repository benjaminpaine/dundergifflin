#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
import os
import itertools
import re
import logging

sys.path.insert(1, os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../"))

import dundergifflin
from dundergifflin.ffmpeg import Converter
from dundergifflin.config import Configuration
from dundergifflin.util import Timestamp, logger, debug_variables
from dundergifflin.database import SubtitleDatabase
from dundergifflin.reddit import RedditCrawler
from dundergifflin.imgur import Imgur

body_search_regex = re.compile(r"[«‹»›„‚“‟‘‛”’\"❛❜❟❝❞❮❯⹂〝〞〟＂<>\[\]](.*?)[«‹»›„‚“‟‘‛”’\"❛❜❟❝❞❮❯⹂〝〞〟＂<>\[\]]")
configuration_directory = os.path.join(os.path.expanduser("~"), ".dundergifflin")
logger.setLevel(logging.INFO)

if not os.path.isdir(configuration_directory):
  sys.stderr.write("Configuration directory does not exist at {0}, exiting.\n".format(configuration_directory))
  sys.stderr.flush()
  sys.exit(5)

configuration_file = os.path.join(configuration_directory, "config")
if not os.path.exists(configuration_file):
  sys.stderr.write("Configuration file does not exist at {0}, exiting.\n".format(configuration_file))
  sys.stderr.flush()
  sys.exit(5)

class OfficeConfiguration(Configuration):
  REQUIRED_KEYS = [
    "IMAGE_WIDTH",
    "TEXT_FONT",
    "TEXT_STROKE_WIDTH",
    "TEXT_SIZE_MAX",
    "TEXT_COLOR",
    "TEXT_OFFSET",
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

class OfficeConverter(Converter):
  def __init__(self, season, episode, output_file, start, end, text):
    input_file = os.path.join(configuration_directory, "media", "office", "S{0:02d}".format(season), "E{0:02d}.mkv".format(episode))
    if not os.path.exists(input_file):
      raise Exception("Could not find Season {0}, Episode {1} at {2}. Exiting.".format(season, episode))
    super(OfficeConverter, self).__init__(input_file, output_file)

    self.add_input_flag("-ss", start)
    self.add_output_flag("-t", (end-start).total_seconds())
    self.add_filter(scale = "{0}:-1".format(configuration.IMAGE_WIDTH))

    text_size = int(configuration.TEXT_SIZE_MAX-len(text)/5)

    for line_offset, text_line in enumerate(reversed(text.splitlines())):
      text_offset = int(configuration.TEXT_OFFSET) + (line_offset * text_size)
      for shadowx, shadowy in itertools.product(
        list(
          range(
            -1 * configuration.TEXT_STROKE_WIDTH, 
            configuration.TEXT_STROKE_WIDTH
          )
        ), 
        repeat=2
      ):
        self.add_filter(drawtext = {
          "fontfile": configuration.TEXT_FONT,
          "text": text_line.strip().replace("'", "`"),
          "x": "(w-text_w)/2",
          "y": "(h-text_h-{0})".format(text_offset),
          "fontsize": int(configuration.TEXT_SIZE_MAX-len(text)/5),
          "fontcolor": configuration.TEXT_COLOR,
          "shadowx": shadowx,
          "shadowy": shadowy
        })

def make_gif(text):
  with SubtitleDatabase(configuration.DATABASE_NAME, configuration.DATABASE_USER, configuration.DATABASE_PASSWORD, os.path.join(configuration_directory, "media", "office")) as subtitle_database:
    season, episode, index, start_time, end_time, text, likeness = subtitle_database.find(text)
    print("Found likeness {0}, season {1}, episode {2} {3} --> {4}:\n{5}".format(
      likeness, season, episode, Timestamp.from_string(start_time), Timestamp.from_string(end_time), text
    ))
    if likeness > configuration.REDDIT_MINIMUM_LIKENESS:
      OfficeConverter(season, episode, "test.gif", Timestamp.from_string(str(start_time)), Timestamp.from_string(str(end_time)), text).execute()
    else:
      print("Minimum likeness {0} not found, abandoning.".format(configuration.REDDIT_MINIMUM_LIKENESS))

def main(text):
  with SubtitleDatabase(
    configuration.DATABASE_NAME,
    configuration.DATABASE_USER,
    configuration.DATABASE_PASSWORD,
    os.path.join(configuration_directory, "media", "office")
  ) as subtitle_database:

    def reply_function(body):
      if len(body) < configuration.REDDIT_MINIMUM_LENGTH:
        logger.info("Ignoring text body '{0}': too short.".format(body))
        return
      logger.debug("Checking for text '{0}'.".format(body))
      check_text = body
      subtitle = subtitle_database.find(check_text)
      if not subtitle:
        # Search for text within quotations.
        for match in body_search_regex.findall(body):
          check_text = match
          subtitle = subtitle_database.find(check_text)
          if subtitle:
            break
      if subtitle:
        season, episode, index, start_time, end_time, text, likeness = subtitle
        text = text.decode("utf-8")
        if likeness > configuration.REDDIT_MINIMUM_LIKENESS:
          logger.info("Text: {0}\nLikeness:{1}\nSeason {2}\nEpisode {3}\n{4} --> {5}\n{6}".format(
            check_text,
            likeness,
            season,
            episode,
            Timestamp.from_string(str(start_time)),
            Timestamp.from_string(str(end_time)),
            text
          ))
        
    with RedditCrawler(
      configuration.REDDIT_CLIENT_ID, 
      configuration.REDDIT_CLIENT_SECRET, 
      configuration.REDDIT_USERNAME, 
      configuration.REDDIT_PASSWORD, 
      configuration.REDDIT_USER_AGENT, 
      reply_function,
      *configuration.REDDIT_SUBREDDITS.split(",")
    ) as crawler:
      raw_input("Press enter to stop.")

def main2():
  with Imgur(
    configuration.IMGUR_CLIENT_ID, 
    configuration.IMGUR_CLIENT_SECRET,
    configuration.IMGUR_AUTHORIZATION_LISTEN_ADDRESS,
    configuration.IMGUR_AUTHORIZATION_LISTEN_PORT
  ) as imgur:
    pass

if __name__ == "__main__":
  sys.exit(main2())
