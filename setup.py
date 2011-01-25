#! /usr/bin/python -tt
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
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

from distutils.core import setup
from email.utils import parseaddr

import bleeter

aname, aemail = parseaddr(bleeter.__author__)
setup(
    name='bleeter',
    version=bleeter.__version__,
    author=aname,
    author_email=aemail,
    scripts=['bleeter.py', ],
    url='http://github.com/JNRowe/bleeter',
    license='GPL-3',
    description=bleeter.__doc__.splitlines ()[0].split("-", 1)[1][1:],
    long_description=open('README.rst').read(),
    data_files=[
        ("share/pixmaps", ["bleeter.png", ]),
        ("share/applications", ["bleeter.desktop"]),
    ],
)
