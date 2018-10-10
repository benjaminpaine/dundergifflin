#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from dundergifflin.util import logger
import praw
import threading
import time
import traceback
import multiprocessing

class CommentCrawler(multiprocessing.Process):
  """
  A process that will crawl through comments on a given subreddit.

  Parameters
  ----------
  reddit : praw.Reddit
    The reddit instance.
  subreddit_name : string
    The name of the subreddit (without /r/).
  comment_function : function(praw.Comment) returns string
    The function to call against a new comment. If the function returns a string, 
    a reply will be sent with that string.
  reply_function : function(praw.Comment)
    The function to call when a comment is a reply to a comment made by the bot.
  vote_function : function(praw.Comment)
    The function to call when a comment is one made by the bot. Effectively this will
    only be called once, when the reddit crawler finds it's own comment immediately
    after it is posted.
  """
  def __init__(self, reddit, subreddit_name, comment_function, reply_function, vote_function):
    super(CommentCrawler, self).__init__()
    logger.debug("Creating comment crawler process for subreddit '{0}'.".format(subreddit_name))
    self.reddit = reddit
    self.subreddit_name = subreddit_name
    self.comment_function = comment_function
    self.reply_function = reply_function
    self.vote_function = vote_function
    self.user = self.reddit.user.me()
  
  def run(self):
    """
    The processes "run" function. The subreddit stream, on initialization, will return the
    the last ~100 comments made in the subreddit, then iterate infinitely.

    If a comment is made by the bot, it will call vote_function.
    If a comment is a response to a comment made by the bot, it will call both reply_function and comment_function.
    If a comment is new, it will call comment_function.

    comment_function will not be ran against a comment if the bot has already replied to this comment.
    """
    logger.debug("Starting comment crawler on subreddit '{0}'.".format(self.subreddit_name))
    subreddit = self.reddit.subreddit(self.subreddit_name)
    for comment in subreddit.stream.comments():
      try:
        logger.debug("Parsing comment ID {0} on subreddit '{1}'.".format(comment, self.subreddit_name))
        if comment.author is not None and comment.author.name == self.user.name:
          self.vote_function(comment)
          continue
        comment.refresh()
        if self.user.name in [reply.author.name for reply in comment.replies if reply.author is not None]:
          continue
        parent = comment.parent()
        if parent.author is not None and parent.author.name == self.user.name:
          self.reply_function(comment)
        reply = self.comment_function(comment)
        if reply:
          logger.info("Replying to comment ID '{0}'.".format(comment))
          comment.reply(reply)
      except Exception as ex:
        logger.error("Caught exception handling comment ID '{0}' on subreddit '{1}'.\n{2}(): {3}\n{4}".format(
          comment,
          self.subreddit_name,
          type(ex).__name__,
          str(ex),
          traceback.format_exc(ex)
        ))
        continue

class VoteCrawler(multiprocessing.Process):
  """
  A process that will periodically get the bots' comments.

  Does not specify a limit, but reddit API has its own limit of 1000. So, effectively,
  this will get the last 1,000 comments and then call the vote_function on them.

  Parameters
  ----------
  reddit : praw.Reddit
    The reddit instance.
  vote_function : function(praw.Comment)
    The function to call against each comment.
  """
  EVALUATION_INTERVAL = 60 * 60
  def __init__(self, reddit, vote_function):
    super(VoteCrawler, self).__init__()
    logger.debug("Creating vote crawler process.")
    self.reddit = reddit
    self.vote_function = vote_function

  def run(self):
    """
    The processes "run" method. Grabs comments in order of creation (descending),
    then calls the supplied vote_function on them.
    """
    logger.info("Vote crawler processing executing.")
    for comment in self.reddit.user.me().comments.new(limit = None):
      logger.debug("Evaluating own comment ID '{0}'.".format(comment))
      self.vote_function(comment)
    time.sleep(VoteCrawler.EVALUATION_INTERVAL)

class CrawlerMonitor(threading.Thread):
  """
  A class that monitors the various processes used in a crawler, and restarts them
  if they die.

  Parameters
  ----------
  crawler : RedditCrawler
    The crawler to monitor on.
  """
  MONITOR_INTERVAL = 2

  def __init__(self, crawler):
    super(CrawlerMonitor, self).__init__()
    self.crawler = crawler
    self.restarts = {}
    logger.debug("Creating monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    self._stop = threading.Event()

  def stopped(self):
    """
    Internal. Whether or not the monitor thread has stopped.
    """
    return self._stop.is_set()

  def stop(self):
    """
    Internal. Stop the monitor thread.
    """
    logger.debug("Stopping monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    self._stop.set()

  def run(self):
    """
    The threads "run" method. Monitors the processes on the crawler.
    """
    logger.debug("Starting monitor for reddit client ID '{0}'.".format(self.crawler.client_id))
    while not self.stopped():
      if not self.crawler.vote_crawler.is_alive():
        logger.error("Vote crawler on client ID '{0}' stopped, restarting.".format(self.crawler.client_id))
        self.crawler.vote_crawler = VoteCrawler(self.crawler.reddit, self.crawler.vote_function)
        self.crawler.vote_crawler.start()
      for i, (subreddit_name, process) in enumerate(self.crawler.comment_crawlers):
        if not process.is_alive():
          logger.error("Comment crawler for subreddit '{0} on client ID '{1}' stopped, restarting.".format(subreddit_name, self.crawler.client_id))
          self.crawler.comment_crawlers[i] = (subreddit_name, CommentCrawler(self.crawler.reddit, subreddit_name, self.crawler.comment_function, self.crawler.reply_function, self.crawler.vote_function))
          self.crawler.comment_crawlers[i][1].start()
      time.sleep(CrawlerMonitor.MONITOR_INTERVAL)
    

class RedditCrawler(object):
  """
  The reddit crawler that a user should instantiate.

  Parametrs
  ---------
  client_id : string
    The client ID, as specified by reddit.
  client_secret : string
    The client secret, as specified by reddit.
  username : string
    The username to log into reddit with.
  password : string
    The password to log into reddit with.
  user_agent : string
    The user agent to instantiate the reddit instance with. Not useful, but required.
  comment_function : function(praw.Comment) returns string
    The function to call against new comments. If a string is returned, a comment will be made as a reply to this comment.
  vote_function : function(praw.Comment)
    The function to call against own comments. Likely _should_ update the local database.
  reply_function : function(praw.Comment)
    The function to call against replies to your comments.
  subreddits : *list
    All of the subreddits to monitor.
  """
  def __init__(self, client_id, client_secret, username, password, user_agent, comment_function, vote_function, reply_function, *subreddits):
    logger.debug("Creating reddit crawler for client ID '{0}'.".format(client_id))
    self.username = username
    self.password = password
    self.client_id = client_id
    self.client_secret = client_secret
    self.user_agent = user_agent
    self.comment_function = comment_function
    self.vote_function = vote_function
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
    self.comment_crawlers = [
      (subreddit, CommentCrawler(self.reddit, subreddit, self.comment_function, self.reply_function, self.vote_function))
      for subreddit in self.subreddits
    ]
    for subreddit_name, process in self.comment_crawlers:
      process.start()
    self.vote_crawler = VoteCrawler(self.reddit, self.vote_function)
    self.vote_crawler.start()
    self.monitor = CrawlerMonitor(self)
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
    try:
      self.vote_crawler.terminate()
    except Exception as ex:
      logger.error("Caught exception when closing vote crawler process for '{0}' on client ID '{1}':\n{2}(): {3}\n{4}".format(
        subreddit_name,
        self.client_id,
        type(ex).__name__,
        str(ex),
        traceback.format_exc(ex)
      ))
      pass
    for subreddit_name, process in self.comment_crawlers:
      try:
        process.terminate()
      except Exception as ex:
        logger.error("Caught exception when closing comment crawler process for '{0}' on client ID '{1}':\n{2}(): {3}\n{4}".format(
          subreddit_name,
          self.client_id,
          type(ex).__name__,
          str(ex),
          traceback.format_exc(ex)
        ))
        pass
