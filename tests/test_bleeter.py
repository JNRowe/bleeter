#
"""test_bleeter - Test main functions."""
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

from datetime import timedelta

from tweepy.models import Status

from hiro import Timeline
from pytest import mark, raises

from bleeter import State, format_tweet, skip_check


def test_State(monkeypatch):
    monkeypatch.setattr('atexit.register', lambda *args, **kwargs: True)
    monkeypatch.setattr('bleeter.GLib.get_user_data_dir',
                        lambda: 'tests/data/xdg_data_home')

    state = State()
    assert state.fetched['self-status'] == 16460438496


def test_State_no_config(monkeypatch):
    monkeypatch.setattr('atexit.register', lambda *args, **kwargs: True)
    monkeypatch.setattr('bleeter.GLib.get_user_data_dir', lambda: 'None')

    state = State()
    assert state.fetched['self-status'] == 1


def test_format_tweet_plain(monkeypatch):
    monkeypatch.setattr('bleeter.Notify.get_server_caps', lambda: [])
    assert format_tweet('Populate #sup contacts from #abook') == \
        'Populate #sup contacts from #abook'


@mark.parametrize('text, formatted', [
    ('Populate #sup contacts from #abook',
     'Populate <i>#sup</i> contacts from <i>#abook</i>'),
    ('RT @ewornj Populate #sup contacts from #abook',
     '<b>RT</b> @<u>ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'),
    ('@rachcholmes London marathon signup closed yet? ;)',
     '@<u>rachcholmes</u> London marathon signup closed yet? ;)'),
    ('Updated my vim colour scheme see http://bit.ly/dunMgV',
     'Updated my vim colour scheme see <u>http://bit.ly/dunMgV</u>'),
])
def test_format_tweet_body_markup(text, formatted, monkeypatch):
    monkeypatch.setattr('bleeter.Notify.get_server_caps',
                        lambda: ['body-markup', ])
    assert format_tweet(text) == formatted


@mark.parametrize('text, formatted', [
    ('See http://bit.ly/dunMgV',
     'See <a href="http://bit.ly/dunMgV">http://bit.ly/dunMgV</a>'),
    ('b123 https://example.com/dunMgV',
     'b123 <a href="https://example.com/dunMgV">https://example.com/dunMgV</a>'),
    ('A list @someone/list',
     'A list @<a href="https://twitter.com/someone/list">someone/list</a>'),
    ('See http://url-hyphen/?and=parm',
     'See <a href="http://url-hyphen/?and=parm">http://url-hyphen/?and=parm</a>'),
    ('Handle ampersands & win', 'Handle ampersands &amp; win'),
    ("""entity test, & " ' < >""",
     'entity test, &amp; &quot; &apos; &lt; &gt;'),
])
def test_format_tweet_body_markup_hyperlinks(text, formatted, monkeypatch):
    monkeypatch.setattr('bleeter.Notify.get_server_caps',
                        lambda: ['body-markup', 'body-hyperlinks'])
    assert format_tweet(text) == formatted


def test_skip_check():
    filt = skip_check([])
    tweet = Status()
    tweet.text = 'This is a test #nowplaying'
    assert filt(tweet) is True


@mark.parametrize('text, passed', [
    ('This is a test', True),
    ('This is a test #nowplaying', False),
    ('Reply to @boring', False),
])
def test_skip_check_custom(text, passed):
    filt = skip_check(['#nowplaying', '@boring'])
    tweet = Status()
    tweet.text = text
    assert filt(tweet) is passed
