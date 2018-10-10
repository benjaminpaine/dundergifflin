#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import smtplib

class SMTPAlert(object):
  """
  A very small wrapper around SMTPLib that will send an "alert".
  Sends from yourself to yourself, with no subject or attachments.

  Parameters
  ----------
  host : string
    The host of the smtp server.
  port : string
    The port of the smtp server.
  username : string
    The user to login to the smtp server with.
  password : string
    The password to login to the smtp server with.
  use_tls : boolean
    Whether or not to use TLS when communicating with the server.
  """
  def __init__(self, host, port, username, password, use_tls = True):
    self.host = host
    self.port = port
    self.username = username
    self.password = password
    self.use_tls = use_tls

  def send(self, message):
    """
    Sends an alert using the supplied SMTP parameters.

    Parameters
    ----------
    message : string
      The message to send.
    """
    connection = smtplib.SMTP(self.host, self.port)
    if self.use_tls:
      connection.starttls()
    connection.login(self.username, self.password)
    connection.sendmail(self.username, self.username, message)
    connection.quit()
