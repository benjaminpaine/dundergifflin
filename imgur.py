#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import requests
import socket
import subprocess
import threading
import time
import six
import datetime
import base64
import os
import json
from dundergifflin.util import url_join, url_encode, logger
from dundergifflin.exceptions import RequestException

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
    logger.info("Opening authorization listening address at {0}:{1}".format(self.host, self.port))
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

  def __enter__(self):
    self.authorize()
    return self

  def __exit__(self, *args):
    pass

  def _post_request(self, url, headers, data):
    response = requests.post(url, headers = headers, data = data)
    if not (200 <= response.status_code < 300):
      try:
        response_data = response.json()
      except:
        response_data = {}
      raise RequestException(response.status_code, url, response_data.get("data", {}).get("error", "No message supplied."))
    return response

  def post_request(self, url, **data):
    headers = {
      "Content-Type": "application/x-www-form-urlencoded"
    }
    return self._post_request(url, headers, url_encode(**data))

  def authenticated_post_request(self, url, **data):
    if datetime.datetime.utcnow() > self.expires:
      self.refresh()
    headers = {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": "Bearer {0}".format(self.access_token)
    }
    return self._post_request(url, headers, url_encode(**data))

  def _get_user_authorization(self):
    listener = AuthorizationListener(self.authorization_listen_address, self.authorization_listen_port)
    listener.start()
    print("Direct your browser to {0}?{1}".format(
      url_join(AUTH_ENDPOINT, "authorize"), 
      url_encode(client_id = self.client_id, response_type = "code")
    ))
    while not listener.received.is_set():
      logger.debug("Waiting on redirect, sleeping for 1.")
      time.sleep(1)
    listener.join()
    return listener.code

  def authorize(self):
    authorization_code = self._get_user_authorization()
    response = self.post_request(
      url_join(AUTH_ENDPOINT, "token"), 
      client_id = self.client_id, 
      client_secret = self.client_secret, 
      grant_type = "authorization_code", 
      code = authorization_code
    )
    response_data = response.json()

    self.access_token = response_data["access_token"]
    self.refresh_token = response_data["refresh_token"]
    self.account_id = response_data["account_id"]
    self.account_username = response_data["account_username"]
    self.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds = response_data["expires_in"])

    logger.info("Imgur client authenticated.")

  def refresh(self):
    logger.info("Refreshing imgur authorization.")
    response = self.post_request(
      url_join(AUTH_ENDPOINT, "token"), 
      client_id = self.client_id, 
      client_secret = self.client_secret, 
      grant_type = "refresh_token", 
      refresh_token = self.refresh_token
    )
    response_data = response.json()
    self.access_token = response_data["access_token"]
    self.refresh_token = response_data["refresh_token"]
    self.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds = response_data["expires_in"])

  def upload(self, path, title, description):
    with open(path, "rb") as image_file:
      encoded_image = base64.b64encode(image_file.read())

    response = self.authenticated_post_request(
      url_join(HTTP_ENDPOINT, "image"),
      name = os.path.basename(path), 
      description = description, 
      title = title, 
      image = encoded_image, 
      type = "base64"
    )

    response_data = response.json()
    return response_data["data"]["link"]
