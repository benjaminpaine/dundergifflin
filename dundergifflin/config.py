#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import re

class Configuration(object):
  """
  Reads a configuration file of key=value pairs.

  Ignores lines starting with # (comments)
  Will convert values into types, if possible.
  
  Parameters
  ----------
  configuration_filename : string
    The location of a configuration file. Can be relative or absolute.
  """
  def __init__(self, configuration_filename):
    for line in open(configuration_filename, "r").readlines():
      line = line.strip()
      if line.startswith("#") or not line:
        continue
      key, value = line.split("=")[0], "=".join(line.split("=")[1:])
      if re.match(r"^[0-9\-]+$", value):
        value = int(value)
      elif re.match(r"^[0-9.\-]+$", value) and value.count(".") == 1:
        value = float(value)
      elif value.lower() == "true":
        value = True
      elif value.lower() == "false":
        value = False
      if hasattr(self, key):
        if type(getattr(self, key)) is not list:
          setattr(self, key [getattr(self, key)])
        setattr(self, key, getattr(self, key) + [value])
      else:
        setattr(self, key, value)
