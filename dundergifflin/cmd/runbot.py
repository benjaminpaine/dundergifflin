#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import sys
import time
import signal

sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))

from dundergifflin.monitor import BotProcessMonitor
from dundergifflin.util import process_is_alive

def monitor_running(directory = os.path.expanduser("~")):
  pid = get_monitor_pid(directory)
  if pid is None or not process_is_alive(pid):
    return False
  return True

def get_monitor_pid(directory = os.path.expanduser("~")):
  pidfile = os.path.join(directory, ".dundergifflin.pid")
  if not os.path.exists(pidfile):
    return None
  return int(open(pidfile, "r").read())

def launch_monitor(directory = os.path.expanduser("~")):
  if not monitor_running(directory):
    print("Starting...")
    monitor = BotProcessMonitor(directory)
    monitor.start()
    time.sleep(1)

def read_bots(config_file):
  if not os.path.exists(config_file):
    return None
  return open(config_file, "r").readlines()

def write_bots(config_file, *bots):
  open(config_file, "w").write("\n".join(list(bots)))

def add_bot(bot_path, directory = os.path.expanduser("~")):
  launch_monitor()
  config_file = os.path.join(directory, ".dundergifflin.cfg")
  bots = read_bots(config_file)
  if bots is None:
    bots = []
  if bot_path in bots:
    print("Bot already exists.")
    return
  else:
    bots.append(bot_path)
  write_bots(config_file, *bots)
  os.kill(get_monitor_pid(directory), signal.SIGHUP)
  print("Bot added!")

if __name__ == "__main__":
  add_bot(sys.argv[1])
