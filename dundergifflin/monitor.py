#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import sys
import signal
import time
import logging
import logging.handlers
import multiprocessing
from dundergifflin.util import process_is_alive

logger = logging.getLogger("dunder-gifflin")
logger.setLevel(logging.DEBUG)

try:
  logger.addHandler(logging.handlers.SysLogHandler(facility = "local0"))
except:
  logger.addHandler(logging.StreamHandler(sys.stdout))
  logger.error("Could not add syslog handler for facility local0, directing to stdout instead.")

def import_bot(bot_path):
  """
  Imports a module using its path.

  Will (hopefully) obscure import methods for python 2/3.

  Parameters
  ----------
  bot_path : string
    The path to a .py file to run as a bot.
  
  Returns
  -------
  module
    The imported module.
  """
  module_name = os.path.splitext(os.path.basename(bot_path))[0]
  logger.info("Importing bot, module name {0}, path {1}.".format(module_name, bot_path))
  try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, bot_path)
    bot = importlib.util.module_from_spec(spec)
    spec.load.exec_module(bot)
    return bot
  except ImportError:
    try:
      from importlib.machinery import SourceFileLoader
      bot = SourceFileLoader(module_name, bot_path).load_module()
      return bot
    except ImportError:
      import imp
      bot = imp.load_source(module_name, bot_path)
      return bot

class BotProcess(multiprocessing.Process):
  """
  A process ran by the monitor.

  Parameters
  ----------
  bot_path : string
    The path to a .py file to run as a bot.
  """
  def __init__(self, bot_path):
    super(BotProcess, self).__init__()
    self.bot = import_bot(bot_path)
    if not hasattr(self.bot, "main"):
      raise ImportError("Imported bot does not have a 'main' function.")
    logger.info("Bot {0} imported successfully.".format(bot_path))
    self.daemon = False

  def run(self):
    if os.fork() != 0:
      return
    self.bot.main()
    logger.info("Bot {0} exited.".format(self.bot.__name__))
    sys.exit(0)

class BotProcessMonitor(multiprocessing.Process):
  """
  A monitoring process to run bots.

  A .pid file exists that should be used to ensure only one monitoring process runs.
  A .cfg file exists where individual bot paths are placed.

  Use command-line tools to interact with the process monitor.

  Parameters
  ----------
  directory : string
    The location to store the .pid and .cfg files.
  """
  MONITOR_INTERVAL = 15

  def __init__(self, directory = os.path.expanduser("~")):
    super(BotProcessMonitor, self).__init__()
    self.directory = directory
    self.pidfile = os.path.join(self.directory, ".dundergifflin.pid")
    self.configfile = os.path.join(self.directory, ".dundergifflin.cfg")
    self.processes = []
    self.daemon = False
    self.stopped = False

  def read_bots(self):
    """
    Read the bot paths in the config file.
    """
    if not os.path.exists(self.configfile):
      logger.info("No configuration file present at '{0}'.".format(self.configfile))
    else:
      for line in open(self.configfile, "r").readlines():
        bot_path = line.strip()
        bot_name = os.path.splitext(os.path.basename(bot_path))[0]
        yield bot_name, bot_path
    
  def process_exists(self, bot_name):
    """
    Determine if a name bot exists.

    Parameters
    ---------
    bot_name : string
      The name of a bot.

    Returns
    -------
    boolean
      Whether or not the named bot exists.
    """
    return bot_name in [process[0] for process in self.processes]

  def find_process(self, bot_name):
    """
    Returns a process found by name.

    Parameters
    ----------
    bot_name : string
      The name of a bot.

    Returns
    -------
    dundergifflin.monitor.BotProcess
    """
    return [process[1] for process in self.processes if process[0] == bot_name][0]

  def process_is_alive(self, bot_name):
    """
    Determine if a process is alive.

    Parameters
    ----------
    bot_name : string
      The name of a bot.
    
    Returns
    -------
    boolean
      Whether or not the process is alive.
    """
    if self.process_exists(bot_name):
      process = self.find_process(bot_name)
      return process.is_alive()
    return False

  def remove_process(self, bot_name):
    """
    Remove a process from the managed processes.

    Parameters
    ----------
    bot_name : string
      The name of a bot.
    """
    for process_name, bot_process in self.processes:
      if process_name == bot_name and bot_process.is_alive():
        bot_process.terminate()
    self.processes = [process for process in self.processes if process[0] != bot_name]

  def spawn_process(self, bot_path):
    """
    Attempts to spawn a process using a path.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to launch as a bot.

    Returns
    -------
    dundergifflin.monitor.BotProcess
      The process. Returns None if it could not be launched.
    """
    try:
      process = BotProcess(bot_path)
      process.start()
      return process
    except Exception as ex:
      logger.error("Could not spawn process at '{0}': {1}() {2}".format(bot_path, type(ex).__name__, str(ex)))
      return None

  def check_bots(self, *args):
    """
    Checks the list of processes and compares it against the configuration.

    If a process doesn't exist, adds it.
    If a process exists but is dead, respawns it.
    If a process exists but isn't in the configuration, removes it.
    """
    for bot_name, bot_path in self.read_bots():
      if self.process_exists(bot_name) and not self.process_is_alive(bot_name):
        logger.error("Bot name '{0}' died, resurrecting.".format(bot_name))
        self.remove_process(bot_name)
      elif not self.process_exists(bot_name):
        logger.info("Spawning new bot '{0}'.".format(bot_name))
      else:
        continue
      process = self.spawn_process(bot_path)
      if process is None:
        logger.error("Could not spawn bot '{0}'.".format(bot_name))
      else:
        self.processes.append((bot_name, process))
    for bot_name, process in self.processes in bot_name not in [bot[0] for bot in self.read_bots()]:
      logger.info("Removing non-configured bot '{0}'.".format(bot_name))
      self.remove_process(bot_name)

  def shutdown(self, *args):
    """
    Shuts down the process monitor.
    """
    self.stopped = True
    logger.info("Shutting down process monitor.")
    for bot_name, process in self.processes:
      if process.is_alive():
        logger.info("Shutting down bot '{0}'.".format(bot_name))
        process.terminate()
        process.join()
      else:
        logger.info("Bot '{0}' already shut down.".format(bot_name))
        process.join()
    
  def run(self):
    """
    The process to run. Will fork from the shell when creating.

    Traps SIGINT and SIGTERM to shutdown gracefully.
    Traps SIGHUP to force a configuration reload.
    """
    logger.info("Monitor process starting.")
    if os.fork() != 0:
      return
    open(self.pidfile, "w").write(str(os.getpid()))

    signal.signal(signal.SIGINT, self.shutdown)
    signal.signal(signal.SIGTERM, self.shutdown)
    signal.signal(signal.SIGHUP, self.check_bots)

    while not self.stopped:
      logger.debug("Checking bots.")
      self.check_bots()
      time.sleep(BotProcessMonitor.MONITOR_INTERVAL)

    self.shutdown()
