# coding: utf-8

import sys
from setuptools import setup, find_packages
import ast
import re


with open('README.md') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requires = f.read()


setup(name='jprt', version="0.0.1",
      long_description=long_description,
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      description='printer manager',
      )

