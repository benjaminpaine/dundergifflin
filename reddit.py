#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from dundergifflin.util import logger
import praw
import threading
import time
import traceback
import multiprocessing

class SubredditCrawler(multiprocessing.Process):
  def __init__(self, reddit, subreddit_name, reply_function):
    super(SubredditCrawler, self).__init__()
    logger.debug("Creating subreddit crawler process for subreddit '{0}'.".format(subreddit_name))
    self.reddit = reddit
    self.subreddit_name = subreddit_name
    self.reply_function = reply_function
    self.user = self.reddit.user.me()
  
  def run(self):
    logger.debug("Starting subreddit crawler on subreddit '{0}'.".format(self.subreddit_name))
    subreddit = self.reddit.subreddit(self.subreddit_name)
    for comment in subreddit.stream.comments():
      logger.debug("Parsing comment ID {0} on subreddit '{1}'.".format(comment, self.subreddit_name))
      if comment.author is not None and comment.author.name == self.user.name:
        logger.info("Ignoring own comment ID '{0}' on subreddit '{1}'.".format(comment, self.subreddit_name))
      if self.user.name in [reply.author.name for reply in comment.replies if reply.author is not None]:
        logger.info("Ignoring already-replied comment ID '{0}' on subreddit '{1}'.".format(comment, self.subreddit_id))
      reply = self.reply_function(comment.body)
      if reply:
        logger.info("Replying to comment ID '{0}'.".format(comment))
      else:
        logger.debug("Not replying to comment ID '{0}' - reply function returned nothing.".format(comment))

class SubredditCrawlerMonitor(threading.Thread):
  MONITOR_INTERVAL = 2

  def __init__(self, crawler):
    super(SubredditCrawlerMonitor, self).__init__()
    self.crawler = crawler
    self.restarts = {}
    logger.debug("Creating monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    self._stop = threading.Event()

  def stopped(self):
    return self._stop.is_set()

  def stop(self):
    logger.debug("Stopping monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    self._stop.set()

  def run(self):
    logger.debug("Starting monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    while not self.stopped():
      for i, (subreddit_name, process) in enumerate(self.crawler.processes):
        if not process.is_alive():
          logger.error("Process for subreddit '{0} on client ID '{1}' stopped, restarting.".format(subreddit_name, self.crawler.client_id))
          self.crawler.processes[i] = (subreddit_name, SubredditCrawler(self.crawler.reddit, subreddit_name, self.crawler.reply_function))
          self.crawler.processes[i][1].start()
      time.sleep(SubredditCrawlerMonitor.MONITOR_INTERVAL)
    

class RedditCrawler(object):
  def __init__(self, client_id, client_secret, username, password, user_agent, reply_function, *subreddits):
    logger.debug("Creating reddit crawler for client ID '{0}'.".format(client_id))
    self.username = username
    self.password = password
    self.client_id = client_id
    self.client_secret = client_secret
    self.user_agent = user_agent
    self.reply_function = reply_function
    self.subreddits = list(subreddits)

  def __enter__(self):
    logger.debug("Creating praw instance for client ID '{0}'.".format(self.client_id))
    self.reddit = praw.Reddit(
      client_id = self.client_id,
      client_secret = self.client_secret,
      username = self.username,
      password = self.password,
      user_agent = self.user_agent
    )
    self.processes = [
      (subreddit, SubredditCrawler(self.reddit, subreddit, self.reply_function))
      for subreddit in self.subreddits
    ]
    for subreddit_name, process in self.processes:
      process.start()
    self.monitor = SubredditCrawlerMonitor(self)
    self.monitor.start()
    logger.debug("Monitor started for client ID '{0}'".format(self.client_id))
    return self

  def __exit__(self, *args):
    logger.debug("Exiting subreddit crawler for client ID '{0}'.".format(self.client_id))
    try:
      self.monitor.stop()
    except Exception as ex:
      logger.error("Caught exception when closing monitor thread on client ID '{0}':\n{1}(): {2}\n{3}".format(
        self.client_id,
        type(ex).__name__,
        str(ex),
        traceback.format_exc(ex)
      ))
      pass
    for subreddit_name, process in self.processes:
      try:
        process.terminate()
      except Exception as ex:
        logger.error("Caught exception when closing subreddit process for '{0}' on client ID '{1}':\n{2}(): {3}\n{4}".format(
          subreddit_name,
          self.client_id,
          type(ex).__name__,
          str(ex),
          traceback.format_exc(ex)
        ))
        pass
