#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import argparse
import sys
import os
import socket
import signal
import datetime
import time
import threading

from dundergifflin.config import Configuration
from dundergifflin.util import process_is_alive
from dundergifflin.monitor import BotMonitor
from dundergifflin.color import Color

def color_success(msg):
  """
  Returns a message colored green.
  """
  return Color.color_string(
    Color.ATTRIBUTE_BRIGHT,
    Color.COLOR_GREEN,
    msg
  )

def color_failure(msg):
  """
  Returns a message colored red.
  """
  return Color.color_string(
    Color.ATTRIBUTE_BRIGHT,
    Color.COLOR_RED,
    msg
  )

def color_warn(msg):
  """
  Returns a message colored yellow.
  """
  return Color.color_string(
    Color.ATTRIBUTE_BRIGHT,
    Color.COLOR_YELLOW,
    msg
  )

def color_info(msg):
  """
  Returns a message colored cyan.
  """
  return Color.color_string(
    Color.ATTRIBUTE_BRIGHT,
    Color.COLOR_CYAN,
    msg
  )

class MessageSender(threading.Thread):
  """
  A small thread that will send a message over a socket,
  and timeout if one is passed.
  """
  def __init__(self, configuration_file, *message):
    super(MessageSender, self).__init__()
    self._received = threading.Event()
    configuration = Configuration(configuration_file)
    self.host = configuration.LISTENER_HOST
    self.port = configuration.LISTENER_PORT
    self.message = " ".join(message)

  def kill(self):
    try:
      self.sock.close()
    except:
      pass

  def received(self):
    return self._received.is_set()

  def run(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.host, int(self.port)))
    self.sock.send(self.message)
    self.data = self.sock.recv(1024)
    self.sock.close()
    self._received.set()

def send_message(configuration_file, timeout, *message):
  """
  Uses the MessageSender to send a message to a TCP socket.
  """
  sender = MessageSender(configuration_file, *message)
  start = datetime.datetime.now()
  sender.start()
  if timeout != 0:
    while not sender.received():
      time.sleep(0.125)
      if (datetime.datetime.now() - start).total_seconds() > timeout:
        sender.kill()
        raise IOError("No response in time.")
    return sender.data

def monitor_running(configuration_file):
  """
  Return whether or not the monitor is running.
  """
  configuration = Configuration(configuration_file)
  if not os.path.exists(configuration.PIDFILE):
    return False
  try:
    pid = int(open(configuration.PIDFILE, "r").read())
    return process_is_alive(pid)
  except ValueError:
    return False

def start_monitor(configuration_file):
  """
  Starts the monitor.
  """
  bot_monitor = BotMonitor(configuration_file)
  bot_monitor.start()

def start(args):
  """
  Start the monitor, then start a bot.
  """
  if not args.script:
    if monitor_running(args.config):
      print(color_warn("No script provided, monitor already running."))
    else:
      start_monitor(args.config)
      print(color_success("Bot monitor started."))
  else:
    if not monitor_running(args.config):
      start_monitor(args.config)
      print(color_success("Bot monitor started."))
      time.sleep(0.25)
    try:
      response = send_message(args.config, 5, "start", os.path.abspath(args.script))
      print("{0}: {1}".format(color_success("Response received"), response))
    except IOError:
      print(color_warn("Timed out waiting for response."))

def stop(args):
  """
  Stop a bot.
  """
  if not monitor_running(args.config):
    print(color_error("Bot monitor not running."))
  else:
    try:
      response = send_message(args.config, 5, "stop", os.path.abspath(args.script))
      print("{0}: {1}".format(color_success("Response received"), response))
    except IOError:
      print(color_warn("Timed out waiting for response."))

def status(args):
  """
  Return the status of the monitor and all bots.
  """
  response_lines = []
  if monitor_running(args.config):
    response_lines += ["process monitor: {0}".format(color_success("running"))]
    try:
      status_response = send_message(args.config, 5, "status")
      response_lines += ["  message receiver: {0}".format(color_success("running"))]
      for bot_line in status_response.splitlines():
        try:
          bot_name, bot_status, bot_events = eval(bot_line)
          response_lines += [
            "  {0}: {1}".format(
              bot_name, 
              color_success("running") if bot_status else color_failure("stopped")
            )
          ] + [
            "     {0:s}{1:20s}{2:s} {3:>8d} total {4:>8d} / hr".format(
              Color(Color.ATTRIBUTE_BRIGHT, Color.COLOR_CYAN),
              event_name,
              Color(Color.ATTRIBUTE_BRIGHT, Color.COLOR_WHITE),
              event_count,
              hour_count
            )
            for event_name, event_count, hour_count
            in bot_events
          ]
        except Exception as ex :
          response_lines += [color_failure("  could not parse response {0}: {1}() {2}".format(bot_line, type(ex).__name__, str(ex)))]
    except IOError:
      response_lines += ["  message receiver: {0}".format(color_failure("stopped"))]
  else:
    response_lines += ["process monitor: {0}".format(color_failure("stopped"))]
  print("\n".join(response_lines))

def restart(args):
  """
  Restart a bot.
  """
  if not monitor_running(args.config):
    print(color_error("Bot monitor not running."))
  else:
    try:
      response = send_message(args.config, 5, "restart", os.path.abspath(args.script))
      print("{0}: {1}".format(color_success("Response received"), response))
    except IOError:
      print(color_warn("Timed out waiting for response."))

def destroy(args):
  """
  Destroy a bot.
  """
  if not monitor_running(args.config):
    print(color_error("Bot monitor not running."))
  else:
    try:
      response = send_message(args.config, 5, "destroy", os.path.abspath(args.script))
      print("{0}: {1}".format(color_success("Response received"), response))
    except IOError:
      print(color_warn("Timed out waiting for response."))

def shutdown(args):
  """
  Shutdown all bots and the monitor.
  """
  if not monitor_running(args.config):
    print(color_error("Bot monitor not running."))
  else:
    send_message(args.config, 0, "shutdown")
    start = datetime.datetime.now()
    while monitor_running(args.config):
      time.sleep(0.125)
      if (datetime.datetime.now() - start).total_seconds() > 5:
        print(color_warn("Monitor did not shut down, sending SIGKILL."))
        configuration = Configuration(args.config)
        os.kill(signal.SIGKILL, int(open(configuration.PIDFILE, "r").read()))
        return
    print(color_success("Bot monitor stopped."))
        
parser = argparse.ArgumentParser(description = "Starts, stops, and monitors dundergifflin-configured reddit bots.")
parser.add_argument("-c", "--config", help="The configuration file for the bot monitor. Defaults to $HOME/dundergifflin.cfg.", default = os.path.join(os.path.expanduser("~"), "dundergifflin.cfg"))

subparsers = parser.add_subparsers()

subparser_start = subparsers.add_parser("start", description = "Starts the bot monitor. If a script is passed, will start that script. If not, will start the monitor only, and any autostart scripts.")
subparser_start.add_argument("script", type=str, help="The script to execute as a reddit bot.", nargs = "?", default = None)
subparser_start.set_defaults(func=start)

subparser_stop = subparsers.add_parser("stop", description = "Stop a bot.")
subparser_stop.add_argument("script", type=str, help="The script to execute as a reddit bot.", default = None)
subparser_stop.set_defaults(func=stop)

subparser_restart = subparsers.add_parser("restart", description = "Restart a bot.")
subparser_restart.add_argument("script", type=str, help="The script to execute as a reddit bot.", default = None)
subparser_restart.set_defaults(func=restart)

subparser_destroy = subparsers.add_parser("destroy", description = "Stop a bot, and remove it from the monitor, deleting all stored event records.")
subparser_destroy.add_argument("script", type=str, help="The script to execute as a reddit bot.")
subparser_destroy.set_defaults(func=destroy)

subparser_shutdown = subparsers.add_parser("shutdown", description = "Stop the bot monitor and all bots.")
subparser_shutdown.set_defaults(func=shutdown)

subparser_status = subparsers.add_parser("status", description = "Retrieve the status of the monitor and any bot scripts, as well as the peg count for each script.")
subparser_status.set_defaults(func=status)

def main():
  args = parser.parse_args(sys.argv[1:])
  args.func(args)

if __name__ == "__main__":
  main()
