#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import six

class Color(object):
  ATTRIBUTE_RESET = 0
  ATTRIBUTE_BRIGHT = 1
  ATTRIBUTE_DIM = 2
  ATTRIBUTE_UNDELINE = 3
  ATTRIBUTE_BLINK = 4
  ATTRIBUTE_REVERSE = 7
  ATTRIBUTE_HIDDEN = 8
  COLOR_BLACK = 0
  COLOR_RED = 1
  COLOR_GREEN = 2
  COLOR_YELLOW = 3
  COLOR_BLUE = 4
  COLOR_MAGENTA = 5
  COLOR_CYAN = 6
  COLOR_WHITE = 7

  @staticmethod
  def find_var(search_key, value):
    values = dict([
      (k.split("_")[1].lower(), v)
      for k, v in six.iteritems(dict(vars(Color)))
      if k.startswith(search_key)
    ])
    if isinstance(value, int):
      if value in values.values():
        return value
      raise ValueError("Unknown {0} {1}.".format(search_key.lower(), value))
    elif isinstance(value, str) or isinstance(value, unicode):
      if value.lower() in values.keys():
        return values[value.lower()]
      raise ValueError("Unknown {0} {1}".format(search_key.lower(), value))

  @staticmethod
  def find_color(color):
    return Color.find_var("COLOR", color)

  @staticmethod
  def find_attribute(attribute):
    return Color.find_var("ATTRIBUTE", attribute)

  @staticmethod
  def color_string(attribute, foreground, text):
    return "{0}{1}{2}".format(
      Color(attribute, foreground),
      text,
      Color(Color.ATTRIBUTE_BRIGHT, Color.COLOR_WHITE)
    )

  def __init__(self, attribute, foreground, background = None):
    self.attribute = Color.find_attribute(attribute)
    self.foreground = Color.find_color(foreground)
    if background is not None:
      self.background = Color.find_color(background)
    else:
      self.background = background

  def __repr__(self):
    return str(self)

  def __str__(self):
    if self.background is not None:
      return "{0:c}[{1:d};{2:d};{3:d}m".format(0x1B, self.attribute, self.foreground + 30, self.background + 40)
    return "{0:c}[{1:d};{2:d}m".format(0x1B, self.attribute, self.foreground + 30)
