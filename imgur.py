#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import requests
import socket
import subprocess
import threading
import time
import six
from dundergifflin.util import url_join, logger

HTTP_ENDPOINT = "https://api.imgur.com/3"
AUTH_ENDPOINT = "https://api.imgur.com/oauth2"

class AuthorizationListener(threading.Thread):
  HTTP_RESPONSE = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n{0}"
  def __init__(self, host, port):
    super(AuthorizationListener, self).__init__()
    self.host = host
    self.port = port
    self.code = None
    self.received = threading.Event()

  def run(self):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((self.host, int(self.port)))
    sock.listen(1)
    conn, addr = sock.accept()
    data = conn.recv(1024)
    self.code = data.splitlines()[0].split()[1].split("=")[1]
    conn.send(AuthorizationListener.HTTP_RESPONSE.format("Authorization code {0} received.".format(self.code)))
    sock.close()
    self.received.set()    

class Imgur(object):
  def __init__(self, client_id, client_secret, authorization_listen_address, authorization_listen_port):
    self.client_id = client_id
    self.client_secret = client_secret
    self.authorization_listen_address = authorization_listen_address
    self.authorization_listen_port = authorization_listen_port
    self.auth_url = "{0}?{1}".format(
      url_join(
        AUTH_ENDPOINT,
        "authorize"
      ),
      "&".join([
        "{0}={1}".format(
          k, v
        )
        for k, v in six.iteritems({
          "client_id": self.client_id,
          "response_type": "code"
        })
      ])
    )

  def __enter__(self):
    self.authorize()

  def __exit__(self, *args):
    pass

  def authorize(self):
    logger.info("Opening authorization listening address at {0}:{1}".format(self.authorization_listen_address, self.authorization_listen_port))
    print("Direct your browser to {0}".format(self.auth_url))
    listener = AuthorizationListener(self.authorization_listen_address, self.authorization_listen_port)
    listener.start()
    while not listener.received.is_set():
      logger.debug("Waiting on redirect, sleeping for 1.")
      time.sleep(1)
    listener.join()
    logger.info("Received authorization code {0}".format(listener.code))
    response = requests.post(
      url_join(
        AUTH_ENDPOINT,
        "token"
      ),
      data = "&".join(
        "{0}={1}".format(k, v)
        for k, v in six.iteritems({
          "client_id": self.client_id,
          "client_secret": self.client_secret,
          "grant_type": "authorization_code",
          "code": listener.code
        })
      ),
      headers = {
        "Content-Type": "application/x-www-form-urlencoded"
      }
    )
    response_data = response.json()
    self.access_token = response_data["access_token"]
    self.refresh_token = response_data["refresh_token"]
    self.account_id = response_data["account_id"]
    self.account_username = response_data["account_username"]
    logger.info("Received access token {0}, refresh token {1}, account ID {2}, account name {3}".format(self.access_token, self.refresh_token, self.account_id, self.account_username))
  
