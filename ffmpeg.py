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
  def __init__(self, input_file, output_file):
    self.input_file = input_file
    self.output_file = output_file
    self.input_args = {}
    self.output_args = {}

  def add_input_flag(self, flag, value):
    self.input_args[flag] = value

  def add_output_flag(self, flag, value):
    self.output_args[flag] = value

  def add_filter(self, **filter_args):
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
    if os.path.exists(self.output_file):
      # ffmpeg is going to ask for an overwrite, ask here instead
      if raw_input("Output file {0} exists. Overwrite? (Y/N): ".format(self.output_file)).lower().startswith("y"):
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

def create_gif(input_file, output_file, start_time, end_time, output_width, text):
  command = [
    "ffmpeg",
    "-ss",
    str(start_time),
    "-i",
    str(input_file),
    "-vf",
    ", ".join([
      "{0}='{1}'".format(filter_name, filter_args)
      for filter_name, filter_args in [
        ("scale", "{0}:-1".format(output_width)),
      ] + [
        ("drawtext", ": ".join([
          "{0}={1}".format(text_option_key, text_option_value)
          for text_option_key, text_option_value in [
            ("fontfile", FONT),
            ("text", text),
            ("x", "(w-text_w)/2"),
            ("y", "(h-text_h-20)"),
            ("fontsize", int(30-len(text)/5)),
            ("fontcolor", "white"),
            ("shadowx", shadowx),
            ("shadowy", shadowy)
          ]
        ]))
        for shadowx, shadowy in itertools.product(list(range(-1, 1)), repeat = 2)
      ]
    ]),
    "-t",
    str(end_time),
    output_file
  ]
  if os.path.exists(output_file):
    if raw_input("Output file '{0}' exists. Overwrite? (Y/N): ".format(output_file)).lower().startswith("y"):
      os.remove(output_file)
    else:
      print("Exiting.")
      sys.exit(2)
  print("Executing command {0}".format(" ".join(command)))
  subprocess.check_call(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE)


def main():
  create_gif("croods.mp4", "croods.gif", 55, 2, 400, "BOY")

if __name__ == "__main__":
  main()
