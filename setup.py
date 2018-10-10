#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup (
  name="DunderGifflin",
  version="0.1.0",
  packages=["dundergifflin"],
  license="GPLV3",
  long_description=open("README", "r").read(),
  install_requires=["praw", "psycopg2", "six", "importlib"]
)
