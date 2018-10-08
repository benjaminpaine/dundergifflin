#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from dundergifflin.util import Timestamp

class Subtitles(object):
  """
  Reads a .srt subtitle file into a dictionary of three-tuples.
  Each three-tuple contains (start_time, end_time, text).

  This will read the entire .srt file into memory, so be careful
  with particularly large files - though even several-hour-long
  movies still have fairly small subtitles.

  Does not understand SSA / ASS. Does not remove tags or anything
  of the sort.

  Parameters
  ----------
  srt_filename : string
    The location of a .srt file. Can be relative or absolute.
  """
  def __init__(self, srt_filename):
    self.subtitles = []
    lines = [line.strip() for line in open(srt_filename, "r").readlines()]
    i = 0
    while i < len(lines):
      index = int(lines[i])
      i += 1
      start_time, end_time = [ts.replace(",", ".") for ts in lines[i].split(" --> ")]
      i += 1
      text = ""
      try:
        while lines[i]:
          if text:
            text += "\n"
          text += lines[i]
          i += 1
          if i >= len(lines) - 1:
            break
      except IndexError:
        if text:
          self.subtitles.append(Subtitles.Subtitle(start_time, end_time, text))
        return
      self.subtitles.append(Subtitles.Subtitle(start_time, end_time, text))
      if i >= len(lines) - 1:
        break
      while not lines[i]:
        i += 1

  class Subtitle(object):
    """
    A small sub-class to hold subtitle objects.

    Parameters
    ----------
    start : string
      The start time of a timestamp. Should be in the format HH:MM:SS,FF
    end : string
      The end time of a timestamp. Should be in the format HH:MM:SS,FF
    text : string
      The text in the subtitle itself.
    """
    def __init__(self, start, end, text):
      self.start = Timestamp.from_string(start)
      self.end = Timestamp.from_string(end)
      self.text = text
