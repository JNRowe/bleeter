#! /usr/bin/python -tt
"""setup - distutils info for bleeter"""
# Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import imp

from setuptools import setup

# Hack to import _version file without importing bleeter/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
ver_file = open("bleeter/_version.py")
_version = imp.load_module("_version", ver_file, ver_file.name,
                           (".py", ver_file.mode, imp.PY_SOURCE))

setup(
    name='bleeter',
    version=_version.dotted,
    author="James Rowe",
    author_email="jnrowe@gmail.com",
    url='http://github.com/JNRowe/bleeter',
    license='GPL-3',
    description="Nasty little twitter client",
    long_description=open('README.rst').read(),
    data_files=[
        ("share/pixmaps", ["bleeter.png", ]),
        ("share/applications", ["bleeter.desktop"]),
    ],
    packages=['bleeter', ],
    entry_points={'console_scripts': ['bleeter = bleeter:main', ]},
)
