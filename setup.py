#! /usr/bin/env python3
"""setup - distutils info for bleeter"""
# Copyright (C) 2010-2012  James Rowe <jnrowe@gmail.com>
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

from importlib.util import module_from_spec, spec_from_file_location

from setuptools import setup


def import_file(package, fname):
    mod_name = fname.rstrip('.py')
    spec = spec_from_file_location(mod_name, '{}/{}'.format(package, fname))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Hack to import _version file without importing bleeter/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
_version = import_file('bleeter', '_version.py')


with open('README.rst') as f:
    long_description = f.read()

setup(
    name='bleeter',
    version=_version.dotted,
    author='James Rowe',
    author_email='jnrowe@gmail.com',
    url='http://github.com/JNRowe/bleeter',
    license='GPL-3',
    description='Nasty little twitter client',
    long_description=long_description,
    data_files=[
        ('share/pixmaps', ['bleeter.png', ]),
        ('share/applications', ['bleeter.desktop']),
    ],
    packages=['bleeter', ],
    entry_points={'console_scripts': ['bleeter = bleeter:main', ]},
)
