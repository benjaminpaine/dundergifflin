#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import types
import datetime
import traceback
import os
import sys
import signal
import time
import logging
import logging.handlers
import multiprocessing
import threading
import socket
from dundergifflin.util import process_is_alive
from dundergifflin.config import Configuration

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

class MonitorConfiguration(Configuration):
  """
  A metaclass for the monitor configuration that checks for required configuration keys.
  """
  REQUIRED_KEYS = [
    "PIDFILE",
    "LISTENER_HOST",
    "LISTENER_PORT"
  ]
  def __init__(self, configuration_filename):
    super(MonitorConfiguration, self).__init__()
    for key in MonitorConfiguration.REQUIRED_KEYS:
      if not hasattr(self, key):
        raise KeyError("Required key '{0}' not found in configuration.".format(key))

class BotMonitor(multiprocessing.Process):
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

  def __init__(self, configuration_file = os.path.join(os.path.expanduser("~"), "dundergifflin.cfg")):
    super(BotMonitor, self).__init__()
    if not os.path.exists(configuration_file):
      raise IOError("Could not find configuration file at '{0}'.".format(configuration_file))
    self.configuration_file = configuration_file
    self.configuration = Configuration(self.configuration_file)
    self.bots = []
    self.daemon = False
    self.stopped = False
    self.killed = False

    self.logger = logging.getLogger("dunder-gifflin")
    if hasattr(self.configuration, "LOG_HANDLER"):
      try:
        if hasattr(self.configuration, "LOG_FORMAT"):
          formatter = logging.Formatter(self.configuration.LOG_FORMAT)
        else:
          formatter = logging.Formatter("%(levelname)8s %(process)05d: %(message)s")

        log_handler = self.configuration.LOG_HANDLER
        if log_handler == "syslog":
          if hasattr(self.configuration, "LOG_FACILITY"):
            handler = logging.handlers.SysLogHandler(facility = self.configuration.LOG_FACILITY)
          else:
            handler = logging.handlers.SysLogHandler()
        elif log_handler == "file":
          if hasattr(self.configuration, "LOG_FILE"):
            handler = logging.handler.FileHandler(self.configuration.LOG_FILE)
          else:
            raise IOError("No LOG_FILE passed.")
        elif log_handler == "stream":
          if hasattr(self.configuration, "LOG_STREAM"):
            handler = logging.StreamHandler(eval(self.configuration.LOG_STREAM))
          else:
            handler = logging.StreamHandler()
        else:
          raise ValueError("Unknown handler type '{0}'.".format(log_handler))
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
      except Exception as ex:
        sys.stderr.write("Exception found while trying to build logger. No logger will be used.\n{0}() {1}\n".format(type(ex).__name__, str(ex)))
        sys.stderr.flush()
    else:
      sys.stderr.write("No LOG_HANDLER configuration found, not using logging.\n")
      sys.stderr.flush()

  def shutdown(self, *args):
    """
    Triggers the process monitor to exit its loop.
    """
    self.logger.info("Shutting down process monitor.")
    self.stopped = True

  def kill(self, *args):
    """
    Shuts down the monitor and all bots.
    """
    self.logger.info("Shutting down process monitor.")
    self.stopped = True
    self.killed = True
    for bot in self.bots:
      try:
        bot.stop()
        bot.join()
      except:
        pass
    try:
      pid = self.listener.pid
      self.listener.stop()
      self.listener.socket.close()
      self.listener.terminate()
      self.listener.join()
      os.kill(pid, 9)
    except:
      pass
    self.logger.info("Process monitor stopped.")

  def check(self, *args):
    """
    Runs each bots' "check" function.
    """
    if not self.stopped:
      for bot in self.bots:
        bot.check()
      if not self.listener.is_alive() and not self.stopped and not self.listener.stopped:
        self.logger.error("Bot monitor listener stopped, restarting.")
        self.listener = BotMonitor.RequestListener(
          self.logger, 
          self.configuration.LISTENER_HOST, 
          self.configuration.LISTENER_PORT, 
          self.child_pipe
        )
        self.listener.start()

  def find_named_bot(self, bot_name):
    """
    Find a bot by name.
    
    Parameters
    ----------
    bot_name : string
      The name of a bot.

    Returns
    -------
    BotMonitor.Bot
    """
    if not any([bot.name == bot_name for bot in self.bots]):
      return None
    return [bot for bot in self.bots if bot.name == bot_name][0]

  def bot_status(self):
    """
    Get the status of all bots and their peg counts.

    Returns
    -------
    string
      The status of the monitor, all bots, and their peg counts.
    """
    return "\n".join([
      str([
        bot.name,
        bot.status(),
        list(bot.sink.get_events())
      ])
      for bot in self.bots
    ])

  def start_bot(self, bot_path = None):
    """
    Start a bot if it doesn't exist. If it exists and is stopped, restart it.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.
  
    Returns
    -------
    string
      The status of the command.
    """
    if bot_path is None:
      return "No path received."
    self.logger.debug("Received request to start bot at path {0}.".format(bot_path))
    bot_name = os.path.splitext(os.path.basename(bot_path))[0]
    existing_bot = self.find_named_bot(bot_name)
    if existing_bot:
      if existing_bot.stopped:
        existing_bot.restart()
        return "Bot '{0}' restarted.".format(bot_name)
      else:
        return "Bot '{0}' already exists.".format(bot_name)
    bot = BotMonitor.Bot(bot_name, bot_path, self.logger)
    self.bots.append(bot)
    bot.start()
    return "Bot '{0}' started.".format(bot_name)

  def stop_bot(self, bot_path = None):
    """
    Stop a bot, but keep it to be restarted later.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.
  
    Returns
    -------
    string
      The status of the command.
    """
    if bot_path is None:
      return "No path received."
    bot_name = os.path.splitext(os.path.basename(bot_path))[0]
    existing_bot = self.find_named_bot(bot_name)
    if not existing_bot:
      return "Bot '{0}' does not exist.".format(bot_name)
    if existing_bot.stopped:
      return "Bot '{0}' already stopped.".format(bot_name)
    existing_bot.stop()
    return "Bot '{0}' stopped.".format(bot_name)

  def destroy_bot(self, bot_path = None):
    """
    Stop a bot and remove it from the monitor.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.
  
    Returns
    -------
    string
      The status of the command.
    """
    if bot_path is None:
      return "No path received."
    bot_name = os.path.splitext(os.path.basename(bot_path))[0]
    existing_bot = self.find_named_bot(bot_name)
    if not existing_bot:
      return "Bot '{0}' does not exist.".format(bot_name)
    try:
      existing_bot.stop()
    except:
      pass
    self.bots = [bot for bot in self.bots if bot.name != bot_name]
    return "Bot '{0}' destroyed.".format(bot_name)
  
  def restart_bot(self, bot_path = None):
    """
    Restart a bot by path.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.
  
    Returns
    -------
    string
      The status of the command.
    """
    if bot_path is None:
      return "No path received."
    bot_name = os.path.splitext(os.path.basename(bot_path))[0]
    existing_bot = self.find_named_bot(bot_name)
    if not existing_bot:
      return "Bot named '{0}' does not exist.".format(bot_name)
    existing_bot.restart()
    return "Bot '{0}' restarted.".format(bot_name)

  def dispatch_command(self, *command):
    """
    Receive a command from the request listener, and attempt to dispatch it.

    Parameters
    ----------
    *command : *string
      The command, followed by arguments.
    """
    if not command:
      return "No command received."
    command, args = command[0], command[1:]
    if not hasattr(self, command) or not callable(getattr(self, command)):
      return "Unknown command '{0}'.".format(command)
    try:
      self.pipe.send(getattr(self, command)(*args))
    except Exception as ex:
      self.pipe.send("Exception: {0}(): {1}".format(type(ex).__name__, str(ex)))

  def run(self):
    """
    The process to run. Will fork from the shell when creating.

    Traps SIGINT and SIGTERM to shutdown gracefully.
    Traps SIGHUP to force a configuration reload.
    """
    self.logger.info("Launching bot monitor.")
    if os.fork() != 0:
      self.logger.info("Bot monitor launched, exiting parent process.")
      return
    self.pipe, self.child_pipe = multiprocessing.Pipe()
    self.logger.info("Starting bot monitor.")
    self.listener = BotMonitor.RequestListener(
      self.logger, 
      self.configuration.LISTENER_HOST, 
      self.configuration.LISTENER_PORT, 
      self.child_pipe
    )
    self.listener.start()

    open(self.configuration.PIDFILE, "w").write(str(os.getpid()))

    while not self.stopped:
      self.check()
      if self.pipe.poll():
        self.pipe.send(self.dispatch_command(*self.pipe.recv()))
      time.sleep(0.5)
      if self.stopped:
        break
    if not self.killed:
      self.kill()
    try:
      os.kill(os.getpid(), 9)
    except:
      pass
    sys.exit(0)

  class RequestListener(multiprocessing.Process):
    OPERATIONS = {
      "stop": "stop_bot",
      "start": "start_bot",
      "restart": "restart_bot",
      "destroy": "destroy_bot",
      "status": "bot_status",
      "shutdown": "shutdown"
    }
    """
    A thread that opens a socket for reading and writing to the monitor.

    Parameters
    ----------
    monitor : BotMonitor
      The parent monitor.
    host : string
      The host to listen on.
    port : int
      The port to listen on.
    """
    def __init__(self, logger, host, port, pipe):
      super(BotMonitor.RequestListener, self).__init__()
      self.logger = logger
      self.host = host
      self.port = port
      self.pipe = pipe
      self.stopped = False

    def stop(self):
      """
      Triggers the listener to stop itself.
      """
      self.stopped = True

    def dispatch_request(self, op, *args):
      """
      Based upon the operation and arguments, perform an action.

      Parameters
      ----------
      op : string
        The operation to perform.
      *args : list<string>
        The arguments to the operation. Will come through as a list of strings, the
        intended operation should cast appropriately.

      Returns
      -------
      string
        A response to send to the requestor.
      """

      if op in BotMonitor.RequestListener.OPERATIONS:
        try:
          self.pipe.send([BotMonitor.RequestListener.OPERATIONS[op]] + list(args))
          if op == "shutdown":
            self.stop()
            return
          start = datetime.datetime.now()
          response = None
          while response is None:
            while not self.pipe.poll():
              time.sleep(0.25)
              if (datetime.datetime.now() - start).total_seconds() > 10:
                break
            if self.pipe.poll():
              response = self.pipe.recv()
            if (datetime.datetime.now() - start).total_seconds() > 10:
              break
          if response is None:
            return "Request timed out.".format(op)
          else:
            return response
        except Exception as ex:
          self.logger.debug(traceback.format_exc(ex))
          return "An exception occurred: {0}() {1}".format(type(ex).__name__, str(ex))
      return "Unknown operation '{0}'.".format(op)
  
    def run(self):
      """
      The main "run" function that loops indefinitely.
      """
      self.logger.info("Launching bot monitor request listener.")
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.socket.bind((self.host, int(self.port)))
      self.socket.listen(1)
      while not self.stopped:
        try:
          conn, addr = self.socket.accept()
          data = conn.recv(1024)
          self.logger.debug("Received data: {0}".format(data))
          try:
            data_split = data.split(" ")
            op, args = data_split[0], data_split[1:]
            response = self.dispatch_request(op, *args)
            if self.stopped:
              conn.close()
              time.sleep(5)
              break
            if not response:
              conn.send("Your request was received, but no response was generated.")
            else:
              conn.send(response)
            conn.close()
          except Exception as ex:
            self.logger.error("Received exception when parsing received data, ignoring request: {0}() {1}".format(type(ex).__name__, str(ex)))
            pass
          
        except Exception as ex:
          self.logger.error("Received exception when reading from socket: {0}() {1}".format(type(ex).__name__, str(ex)))
          break

  class EventSink(object):
    """
    A "sink" class that tracks events and their timings.

    Passed into the bots "main" function when executing, so the bot
    can report back occurrences.
    """
    def __init__(self):
      self.events = {}

    def _clean_events(self):
      """
      Removes stale events.
      """
      for key in self.events:
        self.events[key]["event_times"] = [
          time for time in self.events[key]["event_times"] 
          if time >= (datetime.datetime.now() - datetime.timedelta(hours = 1))
        ]

    def add_event(self, event_name):
      """
      Add an event to the sink.

      Parameters
      ----------
      event_name : string
        The name of the event.
      """
      self._clean_events()
      if event_name not in self.events:
        self.events[event_name] = {
          "event_count": 0,
          "event_times": []
        }
      self.events[event_name]["event_count"] += 1
      self.events[event_name]["event_times"].append(datetime.datetime.now())

    def get_events(self):
      """
      Gets the events that have occurred in this sink.

      Returns
      -------
      tuple
        key : string
          The name of the event.
        total : int
          The total number of this event.
        past_hour : int
          The total number of events over the past hour.
      """
      self._clean_events()
      for key in self.events:
        yield key, self.events[key]["event_count"], len(self.events[key]["event_times"])

  class BotProcess(multiprocessing.Process):
    """
    A process ran by the monitor.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.
    sink : BotMonitor.EventSink
      An event sink to pass into the main() function.
    self.logger : logging.Logger
      A self.logger to send to the main() function for use by the bot.
    """
    def __init__(self, bot_path, conn, bot_logger):
      super(BotMonitor.BotProcess, self).__init__()
      self.conn = conn
      self.logger = bot_logger
      self.bot = import_bot(bot_path)
      self.daemon = False
      if not hasattr(self.bot, "main"):
        raise ImportError("Imported bot does not have a 'main' function.")
      self.logger.info("Bot {0} imported successfully.".format(bot_path))

    def run(self):
      self.bot.main(self.conn, self.logger)

  class Bot(object):
    """
    A holder class for a bot.

    Parameters
    ----------
    name : string
      The name of this bot.
    bot_path : string
      The path to a .py file to run as a bot.
    self.logger : logging.Logger
      A self.logger to send to the main() function for use by the bot.
    """
    def __init__(self, name, bot_path, bot_logger):
      self.name = name
      self.bot_path = bot_path
      self.sink = BotMonitor.EventSink()
      self.conn, self.child_conn = multiprocessing.Pipe()
      self.logger = bot_logger
      self.stopped = False
      self.process = BotMonitor.BotProcess(self.bot_path, self.child_conn, self.logger)

    def start(self):
      """
      Starts the bot.
      """
      self.stopped = False
      self.logger.info("Starting named bot '{0}'".format(self.name))
      self.process.start()

    def stop(self):
      """
      Terminates a bot.
      """
      self.stopped = True
      self.logger.info("Stopping named bot '{0}'".format(self.name))
      pid = self.process.pid
      self.process.terminate()
      self.process.join()
      try:
        os.kill(pid, 9)
      except OSError:
        pass

    def restart(self):
      """
      Restart a bot.
      """
      if self.status():
        self.stop()
      self.process = BotMonitor.BotProcess(self.bot_path, self.child_conn, self.logger)
      self.start()

    def status(self):
      """
      Return the status of the bot process.
      """
      return self.process.is_alive()

    def check(self):
      """
      Checks the health of a process, and restarts if necessary.
      """
      if not self.stopped and self.status():
        if self.conn.poll():
          self.logger.debug("Reading events on bot {0}".format(self.name))
          for event in self.conn.recv().split():
            self.logger.debug("Received event on bot {0}: {1}".format(self.name, event))
            self.sink.add_event(event)
        events = list(self.sink.get_events())
      if not self.stopped and not self.status():
        if "exit" in [event[0] for event in events] and [event[2] for event in events if event[0] == "exit"][0] > 5:
          self.logger.error("Named bot '{0}' has exceeded restart limit, not restarting.".format(self.name))
          self.stopped = True
        else:
          self.logger.error("Named bot '{0}' has died, restarting.".format(self.name))
          self.restart()
          self.sink.add_event("exit")
