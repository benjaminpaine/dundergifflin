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
  """
  A thread that will launch a TCP socket at the host/port specified.

  Will listen for an HTTP request that should come from imgur. It will take the specified URL
  and parse out the authorization code.

  This will likely only need to be done once, though if there is a
  significant time between authentications, it will need to run again.

  Launched from the Imgur client itself, so should not be instantiated directly.

  Parameters
  ----------
  host : string
    The host to listen on. 0.0.0.0 means listen to all connections.
  port : int
    The port to listen on.
  """
  HTTP_RESPONSE = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n{0}"
  def __init__(self, host, port):
    super(AuthorizationListener, self).__init__()
    self.host = host
    self.port = port
    self.code = None
    self.received = threading.Event()

  def run(self):
    """
    The threads "run" method.
    """
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
  """
  A context manager that handles an imgur client.

  This should manage its own authentication.

  Parameters
  ----------
  client_id : string
    The client ID supplied from imgur.
  client_secret : string
    The client secret supplied from imgur.
  authorization_listen_address : string
    When first authorizing, this is where the authorization should redirect to.
    See README for more information.
  authorization_listen_port : int
    When first authorizing, this is where the authorization should redirect to.
    See README for more information.
  refresh_token : string
    If already authorized, this token will allow us to get a new oauth2 bearer token.
  """
  AUTHORIZATION_TIMEOUT = 60
  def __init__(self, client_id, client_secret, authorization_listen_address, authorization_listen_port, refresh_token = None):
    self.client_id = client_id
    self.client_secret = client_secret
    self.authorization_listen_address = authorization_listen_address
    self.authorization_listen_port = authorization_listen_port
    self.refresh_token = refresh_token

  def __enter__(self):
    self.authorize()
    return self

  def __exit__(self, *args):
    pass

  def _post_request(self, url, headers, data):
    """
    Internal. Sends a post request with the specified url, headers, and data. Will throw an exception
    if the response status code is not a 200-range.
    """
    response = requests.post(url, headers = headers, data = data)
    if not (200 <= response.status_code < 300):
      try:
        response_data = response.json()
      except:
        response_data = {}
      raise RequestException(url, response.status_code, response_data.get("data", {}).get("error", "No message supplied."))
    return response
  
  def _get_user_authorization(self):
    """
    Internal. Opens the listening socket for user authorization and listens for the response.
    """
    listener = AuthorizationListener(self.authorization_listen_address, self.authorization_listen_port)
    listener.start()
    print("Direct your browser to {0}?{1}".format(
      url_join(AUTH_ENDPOINT, "authorize"), 
      url_encode(client_id = self.client_id, response_type = "code")
    ))
    start = datetime.datetime.utcnow()
    while not listener.received.is_set():
      if (datetime.datetime.utcnow() - start).total_seconds() > Imgur.AUTHORIZATION_TIMEOUT:
        raise IOError("Timed out waiting for imgur authorization!")
      logger.debug("Waiting on redirect, sleeping for 1.")
      time.sleep(1)
    listener.join()
    return listener.code


  def _authorize(self):
    """
    Internal. Either starts intial authorization, or refreshes using supplied refresh token.
    """
    if getattr(self, "refresh_token", None) is not None:
      try:
        self.refresh()
        return
      except Exception as ex:
        logger.error("Failed getting authorization using refresh token. Will open authentication address.\n{0}(): {1}\n{2}".format(
          type(ex).__name__,
          str(ex),
          traceback.format_exc(ex)
        ))
      
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

  def _refresh(self):
    """
    Internal. Uses the supplied refresh token to re-authenticate.
    """
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
  
  def post_request(self, url, **data):
    """
    Send a POST request with URLEncoded form data.
    
    Parameters
    ----------
    url : string
      The URL to send the data to.
    data: **kwargs
      A set of key/value pairs that are URLEncoded into the POST body.

    Returns
    -------
    requests.Response
      The response from said URL.
    """
    headers = {
      "Content-Type": "application/x-www-form-urlencoded"
    }
    return self._post_request(url, headers, url_encode(**data))

  def authenticated_post_request(self, url, **data):
    """
    Send a POST request with URLEncoded form data and the oauth2 bearer token.
    
    Parameters
    ----------
    url : string
      The URL to send the data to.
    data: **kwargs
      A set of key/value pairs that are URLEncoded into the POST body.

    Returns
    -------
    requests.Response
      The response from said URL.
    """
    if datetime.datetime.utcnow() > self.expires:
      self._refresh()
    headers = {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": "Bearer {0}".format(self.access_token)
    }
    return self._post_request(url, headers, url_encode(**data))

  def upload(self, path, title, description):
    """
    Uploads an image to imgur.

    Will base64 encode the image data.

    Parameters
    ----------
    path : string
      The path to the image file. Can be absolute or relative to the cwd at launch.
    title : string
      The title of the image.
    description : string
      The description of the image.

    Returns
    -------
    string
      The URL to the image, as returned from the imgur API.        
    """
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
