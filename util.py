#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import logging
import sys
import hashlib

logger = logging.getLogger("dunder-gifflin")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

class Timestamp(object):
  def __init__(self, milliseconds = 0, seconds = 0, minutes = 0, hours = 0):
    if milliseconds > 1000:
      seconds += milliseconds // 1000
      milliseconds = milliseconds % 1000
    if seconds > 60:
      minutes += seconds // 60
      seconds = seconds % 60
    if minutes > 60:
      hours += minutes // 60
      minutes = minutes % 60
    self.milliseconds = milliseconds
    self.seconds = seconds
    self.minutes = minutes
    self.hours = hours

  @staticmethod
  def from_string(string):
    seconds = 0
    minutes = 0
    hours = 0
    milliseconds = 0
    string = str(string)

    if string.count(":") == 0:
      if string.find(".") != -1:
        seconds, milliseconds = [int(part) for part in string.split(".")]
      else:
        seconds = int(string)
    else:
      for i, second_part in enumerate(reversed(string.split(":"))):
        if i == 0:
          if second_part.find(".") != -1:
            seconds, milliseconds = [int(part) for part in second_part.split(".")]
          else:
            seconds = int(second_part)
        elif i == 1:
          minutes = int(second_part)
        elif i == 2:
          hours = int(second_part)
    return Timestamp(milliseconds, seconds, minutes, hours)

  def total_seconds(self):
    return float(self.seconds + (self.minutes * 60) + (self.hours * 60 * 60)) + float(self.milliseconds / 1000.00)

  def __add__(self, b):
    total_difference = self.total_seconds() + b.total_seconds()
    sec_part = int(total_difference)
    ms_part = int((float(total_difference) - total_difference) * 1000)
    return Timestamp(ms_part, sec_part)

  def __sub__(self, b):
    total_difference = self.total_seconds() - b.total_seconds()
    if total_difference < 0:
      return Timestamp()
    sec_part = int(total_difference)
    ms_part = int((float(total_difference) - total_difference) * 1000)
    return Timestamp(ms_part, sec_part)

  def __repr__(self):
    return "{0:02d}:{1:02d}:{2:02d}.{3:<04d}".format(
      self.hours,
      self.minutes,
      self.seconds,
      self.milliseconds
    )

def debug_variables(*args):
  return ", ".join(type(arg).__name__ for arg in args)
  return u", ".join([
    u"{0}({1})".format(
      type(arg),
      unicode(arg).encode("utf-8")
    )
    for arg in args
  ])

def flatten(*lists):
  return_value = []
  for l in lists:
    if isinstance(l, list):
      return_value.extend(flatten(*l))
    else:
      return_value.append(l)
  return return_value

def md5sum(path):
  md5_hash = hashlib.md5()
  with open(path, "rb") as handler:
    for chunk in iter(lambda: handler.read(4096), b""):
      md5_hash.update(chunk)
  return md5_hash.hexdigest()

def url_join(*args):
  return "/".join([a.strip("/") for a in args])
