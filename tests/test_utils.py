#
"""test_utils - Test utility functions."""
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
#

from datetime import datetime, timedelta
from re import match

from hiro import Timeline
from pytest import mark, raises

from bleeter import utils


def test_create_lockfile(monkeypatch, tmpdir):
    monkeypatch.setattr('atexit.register', lambda *args, **kwargs: True)
    monkeypatch.setattr('bleeter.utils.GLib.get_user_data_dir',
                        lambda: tmpdir.strpath)
    monkeypatch.setattr('bleeter.utils.usage_note',
                        lambda *args: True)

    utils.create_lockfile()
    assert tmpdir.join('bleeter/lock').exists()

    with raises(IOError, match="Another instance is running"):
        utils.create_lockfile()


def test_find_app_icon(monkeypatch):
    monkeypatch.setattr('bleeter.utils.GLib.get_user_cache_dir',
                        lambda: 'tests/data/xdg_cache_home')
    monkeypatch.setattr('sys.prefix', '')
    monkeypatch.setattr('sys.path', ['non-existent-path', ])

    assert utils.find_app_icon() == \
        'file://tests/data/xdg_cache_home/bleeter/bleeter.png'
    assert utils.find_app_icon(False) == \
        'tests/data/xdg_cache_home/bleeter/bleeter.png'


def test_find_app_icon_personal(monkeypatch):
    monkeypatch.setattr('bleeter.utils.GLib.get_user_cache_dir', lambda: 'None')
    monkeypatch.setattr('sys.path', ['non-existent-path', ])

    with raises(EnvironmentError, match='Can’t find application icon!'):
        utils.find_app_icon()


def test_find_app_icon_local(monkeypatch):
    monkeypatch.setattr('bleeter.utils.GLib.get_user_cache_dir', lambda: 'None')
    monkeypatch.setattr('sys.path', ['', ])

    assert utils.find_app_icon().endswith('/bleeter/bleeter.png')


@mark.parametrize('delta, result', [
    (timedelta(days=365), 'last year'),
    (timedelta(days=70), 'about two months ago'),
    (timedelta(days=30), 'last month'),
    (timedelta(days=21), 'about three weeks ago'),
    (timedelta(days=4), 'about four days ago'),
    (timedelta(days=1), 'yesterday'),
    (timedelta(hours=5), 'about five hours ago'),
    (timedelta(hours=1), 'about an hour ago'),
    (timedelta(minutes=6), 'about six minutes ago'),
    (timedelta(seconds=12), 'about 12 seconds ago'),
])
def test_relative_time(delta, result):
    with Timeline().freeze():
        now = datetime.utcnow()
        assert utils.relative_time(now - delta) == result


def test_url_expand(monkeypatch):
    monkeypatch.setitem(utils.URLS, 'http://bit.ly/dunMgV', 'terminal.png')
    m = match('.*', 'http://bit.ly/dunMgV')

    assert utils.url_expand(m) == '<a href="terminal.png">terminal.png</a>'
