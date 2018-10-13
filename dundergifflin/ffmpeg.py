#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from util import logger, flatten

import subprocess
import sys
import os
import itertools
import six

FONT = "/home/thrall/downloads/impact.ttf"

class Converter(object):
  """
  A class to wrap around FFMpeg conversion from video to GIF.
  
  Parameters
  ----------
  input_file : string
    The input file. Can be absolute or relative to the cwd at execution.
  output_file : string
    The output file. Can be absolute or relative to the cwd at execution.
  overwrite : boolean
    Whether or not to overwrite the output file (if it exists). If this is false,
    this will ask for input when the file exists.
  """
  def __init__(self, input_file, output_file, overwrite = False):
    self.input_file = input_file
    self.output_file = output_file
    self.overwrite = overwrite
    self.input_args = {}
    self.output_args = {}

  def add_input_flag(self, flag, value):
    """
    Add an input flag.

    Parameters
    ----------
    flag : string
      The input flag. Will overwrite existing flags.
    value : string
      The flag value to be passed to ffmpeg.
    """
    self.input_args[flag] = value

  def add_output_flag(self, flag, value):
    """
    Add an output flag.

    Parameters
    ----------
    flag : string
      The output flag. Will overwrite existing flags.
    value : string
      The flag value to be passed to ffmpeg.
    """
    self.output_args[flag] = value

  def add_filter(self, **filter_args):
    """
    Add a video filter. This is a special case for add_output_flag where the flag
    is always "-vf". This will allow multiple values for this particular flag.

    Parameters
    ----------
    **kwargs
      key : string
        The name of the filter.
      value : string
        The value passed into the filter.
    """
    for filter_name in filter_args:
      filter_string = "{0}='{1}'".format(
        filter_name,
        filter_args[filter_name] if not isinstance(filter_args[filter_name], dict) else ": ".join([
          "{0}={1}".format(
            filter_option_key, filter_args[filter_name][filter_option_key]
          )
          for filter_option_key in filter_args[filter_name]
        ])
      )
      if "-vf" not in self.output_args:
        self.output_args["-vf"] = []
      self.output_args["-vf"].append(filter_string)

  def execute(self):
    """
    Executes the conversion using the supplied input and output flags.

    Returns
    -------
    string
      The output of the command.
    """
    if os.path.exists(self.output_file):
      if self.overwrite:
        os.remove(self.output_file)
      elif raw_input("Output file {0} exists. Overwrite? (Y/N): ".format(self.output_file)).lower().startswith("y"):
        os.remove(self.output_file)
      else:
        return
    command = [
      str(c) for c in
      [
        "ffmpeg"
      ] + flatten([
        [key, value]
        for key, value in six.iteritems(self.input_args)
      ]) + [
        "-i", self.input_file
      ] + flatten([
        [key, value if not isinstance(value, list) else ", ".join(value)]
        for key, value in six.iteritems(self.output_args)
      ]) + [
        self.output_file
      ]
    ]
    logger.debug("Executing command {0}".format(" ".join(command)))
    p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
      raise IOError("FFMpeg returned an error code. Stderr was:\n{0}".format(err))
    return out

class SubtitleConverter(Converter):
  """
  A subclass of Converter used specifically for writing subtitles.

  Parameters
  ----------
  input_file : string
    The input file. Can be absolute or relative to the cwd at execution.
  output_file : string
    The output file. Can be absolute or relative to the cwd at execution.
  overwrite : boolean
    Whether or not to overwrite the output file (if it exists). If this is false,
    this will ask for input when the file exists.
  start : dundergifflin.util.Timestamp
    The timestamp the start the GIF from.
  end : dundergifflin.util.Timestamp
    The timestamp to end the GIF at.
  text : string
    The text to display.
  image_width : int
    The width of the image to generate. Will scale height proportionately.
  text_font : string
    The path to a .ttf font file to use.
  text_color : string
    The text color to pass into ffmpeg.
  text_size_max : int
    The maximum size of the text. Will attempt to scale text down based on how long it is.
  text_offset : int
    The offset for the base of the text, from the bottom, in pixels.
  text_stroke_width : int
    The thickness of the stroke around the text. Always black.
  """
  def __init__(self, input_file, output_file, overwrite, start, end, text, image_width, text_font, text_color, text_size_max, text_offset, text_stroke_width):
    super(SubtitleConverter, self).__init__(input_file, output_file, overwrite)
    
    self.add_input_flag("-ss", start)
    self.add_output_flag("-t", (end-start).total_seconds())
    self.add_filter(scale = "{0}:-1".format(image_width))

    text_size = int(text_size_max-len(text)/10)

    for line_offset, text_line in enumerate(reversed(text.splitlines())):
      _text_offset = int(text_offset) + (line_offset * text_size)
      for shadowx, shadowy in itertools.product(
        list(
          range(
            -1 * text_stroke_width,
            text_stroke_width
          )
        ), 
        repeat=2
      ):
        self.add_filter(drawtext = {
          "fontfile": text_font,
          "text": text_line.strip().replace("'", "`"),
          "x": "(w-text_w)/2",
          "y": "(h-text_h-{0})".format(_text_offset),
          "fontsize": int(text_size_max-len(text)/5),
          "fontcolor": text_color,
          "shadowx": shadowx,
          "shadowy": shadowy
        })
