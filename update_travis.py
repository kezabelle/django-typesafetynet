#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# based heavily on https://www.dominicrodger.com/tox-and-travis.html
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import os
from tox._config import parseconfig

ENVS = (' - TOX_ENV={value!s}'.format(value=x)
        for x in parseconfig(None, 'tox').envlist)

TEMPLATE = """language: python

sudo: false

notifications:
  email: false

install:
  - pip install --upgrade tox

env:
{envs}

script:
  - tox -e $TOX_ENV
""".format(envs="\n".join(ENVS))


HERE = os.path.abspath(os.path.dirname(__file__))


with open(os.path.join(HERE, '.travis.yml'), mode='w') as f:
    f.write(TEMPLATE)
