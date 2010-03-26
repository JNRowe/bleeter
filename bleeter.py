#! /usr/bin/python -tt
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""bleeter - Nasty little twitter client"""
# Copyright (C) 2010  James Rowe <jnrowe@gmail.com>
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

__version__ = "0.1.0"
__date__ = "2010-03-23"
__author__ = "James Rowe <jnrowe@gmail.com>"
__copyright__ = "Copyright (C) 2010 James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

from email.utils import parseaddr

__doc__ += """.

A simple little twitter client that display notifications for new tweets and
nothing more.

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import atexit
import datetime
import json
import os
import re
import sys
import time
import urllib

from xml.sax.saxutils import escape

import configobj
import glib
import pynotify
import tweepy

def relative_time(timestamp):
    """Format a relative time

    >>> now = datetime.datetime.now()
    >>> relative_time(now - datetime.timedelta(days=365))
    'a year ago'
    >>> relative_time(now - datetime.timedelta(days=70))
    '2 months ago'
    >>> relative_time(now - datetime.timedelta(days=21))
    '3 weeks ago'
    >>> relative_time(now - datetime.timedelta(days=4))
    '4 days ago'
    >>> relative_time(now - datetime.timedelta(hours=5))
    '5 hours ago'
    >>> relative_time(now - datetime.timedelta(minutes=6))
    '6 minutes ago'
    >>> relative_time(now - datetime.timedelta(seconds=7))
    '7 seconds ago'

    """

    matches = [
        (60 * 60 * 24 * 365, "year"),
        (60 * 60 * 24 * 28, "month"),
        (60 * 60 * 24 * 7, "week"),
        (60 * 60 * 24, "day"),
        (60 * 60, "hour"),
        (60, "minute"),
        (1, "second"),
    ]

    delta = datetime.datetime.now() - timestamp
    seconds = delta.days * 86400 + delta.seconds
    for scale, name in matches:
        i = seconds // scale
        if i:
            break
    return "%s %s%s ago" % (i if i > 1 else "a", name, "s" if i > 1 else "")


def format_tweet(text):
    """Format tweet for display

    >>> pynotify.get_server_caps = lambda: ["body-markup"]
    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("RT @ewornj Populate #sup contacts from #abook")
    '<b>RT</b> <u>@ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("@rachcholmes London marathon signup closed yet? ;)")
    '<u>@rachcholmes</u> London marathon signup closed yet? ;)'
    >>> format_tweet("Updated my vim colour scheme see http://bit.ly/dunMgV")
    'Updated my vim colour scheme see <u>http://bit.ly/dunMgV</u>'
    >>> pynotify.get_server_caps = lambda: []
    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate #sup contacts from #abook'

    :type text: ``str``
    :param api: Tweet content
    :rtype: ``str``
    :return: Tweet content with pretty formatting
    """

    text = escape(text)
    if "body-markup" in pynotify.get_server_caps():
        text = re.sub(r'(@\w+)', r'<u>\1</u>', text)
        text = re.sub(r'(#\w+)', r'<i>\1</i>', text)
        text = re.sub(r'(http://[\w\./]+)', r'<u>\1</u>', text)

        if text.startswith("RT "):
            text = "<b>RT</b> " + text[3:]
    return text


def get_icon(user):
    """Get icon location for user

    :type user: ``tweepy.models.User``
    :param user: Tweet user reference
    :rtype: ``str``
    :return: Location of the icon file
    """

    cache_dir = "%s/bleeter" % glib.get_user_cache_dir()
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    filename = "%s/%s" % (cache_dir, urllib.quote_plus(user.profile_image_url))
    if not os.path.exists(filename):
        try:
            urllib.urlretrieve(user.profile_image_url, filename)
        except IOError:
            # Fallback to generic icon, if it exists
            filename = "%s/bleeter.png" % cache_dir
    return filename


def process_tweets(api, tweets, seen):
    """Display notifications for unseen tweets

    :type tweets: ``list`` of ``tweepy.models.Status``
    :param api: Twitter status messages
    :type seen: ``list``
    :param seen: Already seen tweets
    """
    for tweet in reversed(tweets):
        if tweet.id in seen:
            continue
        else:
            note = pynotify.Notification("From %s about %s"
                                         % (tweet.user.name,
                                            relative_time(tweet.created_at)),
                                         format_tweet(tweet.text),
                                         get_icon(tweet.user))
            if api.auth.username in tweet.text:
                note.set_urgency(pynotify.URGENCY_CRITICAL)
            if tweet.text.startswith("@%s" % api.auth.username):
                note.set_timeout(pynotify.EXPIRES_NEVER)
            if not note.show():
                raise OSError("Notification failed to display!")
            seen.append(tweet.id)
            time.sleep(4)


def update(api, seen):
    """Fetch updates and display notifications

    :type api: ``twitter.Api``
    :param api: Authenticated ``tweepy.api.API`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    """

    process_tweets(api, api.friends_timeline(), seen)
    return True


def update_stealth(api, seen, users):
    """Fetch updates and display notifications for stealth follows

    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    :type users: ``list`` of ``str``
    :param users: Stealth follow user list
    """

    for user in users:
        process_tweets(api, api.user_timeline(user), seen)
    return True


def main(argv):
    """main handler

    :type argv: ``list``
    :param argv: Command line parameters
    """

    if not pynotify.init(argv[0]):
        print "Unable to initialise pynotify!"
        return 1

    state_file = "%s/bleeter/state.db" % glib.get_user_config_dir()
    config_file = "%s/bleeter/config.ini" % glib.get_user_config_dir()
    conf = configobj.ConfigObj(config_file)
    stealth_users = conf.get("stealth")

    user = conf.get("user", os.getenv("TWEETUSERNAME"))
    if not user:
        print "No user set in %s and $TWEETUSERNAME not set" % config_file
        return 1
    password = conf.get("password", os.getenv("TWEETPASSWORD"))
    if not password:
        print "No password set in %s and $TWEETPASSWORD not set" % config_file
        return 1

    auth = tweepy.BasicAuthHandler(user, password)
    api = tweepy.API(auth)
    if os.path.exists(state_file):
        seen = json.load(open(state_file))
    else:
        seen = []

    def save_state(seen):
        """Seen tweets state saver

        :type seen: ``list``
        :param seen: Already seen tweets
        """
        json.dump(seen, open(state_file, "w"), indent=4)
    atexit.register(save_state, seen)

    loop = glib.MainLoop()
    if stealth_users:
        glib.timeout_add_seconds(300, update_stealth, api, seen, stealth_users)
    glib.timeout_add_seconds(300, update, api, seen)
    loop.run()

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
