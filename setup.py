#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""spawn_oop setup.
"""
from distutils.core import setup
from spawn_oop import __version__

PACKAGES = ['spawn_oop']
PACKAGES_DATA = {}


setup(name='spawn_oop',
      description='Spawn OpenObject methods to child process',
      author='GISCE Enginyeria',
      author_email='devel@gisce.net',
      url='http://www.gisce.net',
      version=__version__,
      license='General Public Licence 2',
      long_description='''Spawn OpenObject methods to child process''',
      provides=['spawn_oop'],
      install_requires=['ooop', 'psutil'],
      packages=PACKAGES,
      package_data=PACKAGES_DATA)
