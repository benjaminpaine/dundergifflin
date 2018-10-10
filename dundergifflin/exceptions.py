#!/usr/bin/env python
# -*- coding: utf-8 -*-

class RequestException(Exception):
  def __init__(self, url, status_code, msg = "No message supplied."):
    super(RequestException, self).__init__("A response code of {0} was received at URL {1}. The message was '{2}'.".format(
      status_code,
      url,
      msg
    ))
    self.status_code = status_code
    self.url = url
