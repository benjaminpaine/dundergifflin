#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup (
  name="dundergifflin",
  version="0.2.0",
  packages=["dundergifflin"],
  license="GPLV3",
  long_description=open("README.md", "r").read(),
  install_requires=["praw", "psycopg2", "six", "importlib"],
  entry_points = {
    "console_scripts": ["dundergifflin = dundergifflin.cmd:main"]
  }
)
