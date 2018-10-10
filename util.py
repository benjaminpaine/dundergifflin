#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import logging
import sys
import hashlib
import six

try:
  from urllib import urlencode
except ImportError:
  # Python 3.x
  from urllib.parse import urlencode

logger = logging.getLogger("dunder-gifflin")
logger.setLevel(logging.DEBUG)

class Timestamp(object):
  """
  A "timestamp" object, similar to datetime.time.
  Permits addition and subtraction of timestampts to get durations.

  Parameters
  ----------
  milliseconds : int
    The number of milliseconds in this timestamp.
  seconds : int
    The number of seconds in this timestamp.
  minutes : int
    The number of minutes in this timestamp.
  hours : int
    The number of hours in this timestamp.
  """
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
    """
    Builds a timestamp object from a string.

    Parameters
    ----------
    string : string
      A string in the form of "HH:MM:SS.ff". Can omit from right to left.
    """
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
    """
    The total seconds in a timestamp.
  
    Returns
    -------
    float
      The total number of seconds represented by a timestamp.
    """
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

def flatten(*lists):
  """
  Flattens multiple lists into one list.

  Parameters
  ----------
  *lists : list<T>
    A list of items. If any item is a list, will recursively call flatten().
  
  Returns
  -------
  list
    All items in the list, flattened into one list.
  """
  return_value = []
  for l in lists:
    if isinstance(l, list):
      return_value.extend(flatten(*l))
    else:
      return_value.append(l)
  return return_value

def md5sum(path):
  """
  Determine the md5sum of a file.

  Parameters
  ----------
  path : string
    The path to the file. Can be absolute or relative to the cwd at execution.
  
  Returns
  -------
  string
    The hex string that is the md5 hash of the file.
  """
  md5_hash = hashlib.md5()
  with open(path, "rb") as handler:
    for chunk in iter(lambda: handler.read(4096), b""):
      md5_hash.update(chunk)
  return md5_hash.hexdigest()

def url_join(*args):
  """
  Joins arguments together into a URL. Similar to os.path.join.

  Parameters
  ----------
  *args : list<string>
    A list of arguments to join into a URL.

  Returns
  -------
  string
    The joined URL.
  """
  return "/".join([str(a).strip("/") for a in args])

def url_encode(**kwargs):
  """
  Encodes keys and values into form / parameter strings.

  Obscures python 2/3 implementations.

  Parameters
  ----------
  **kwargs
    Key/value pairs.

  Returns
  -------
  string
    The URL-encoded string of all kwargs.
  """
  return urlencode(kwargs)
