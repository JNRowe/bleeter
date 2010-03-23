#! /usr/bin/python -tt
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""litter - Nasty little twitter client"""
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
import errno
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
import twitter

def format_tweet(text):
    """Format tweet for display

    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("RT @ewornj Populate #sup contacts from #abook")
    '<b>RT</b> <u>@ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("@rachcholmes congrats. London marathon signup closed yet? ;)")
    '<u>@rachcholmes</u> congrats. London marathon signup closed yet? ;)'
    >>> format_tweet("Added terminal support to my vim colour scheme http://bit.ly/9WSw5q, see http://bit.ly/dunMgV")
    'Added terminal support to my vim colour scheme <u>http://bit.ly/9WSw5q</u>, see <u>http://bit.ly/dunMgV</u>'

    :type text: ``str``
    :param api: Tweet content
    :rtype: ``str``
    :return: Tweet content with pretty formatting
    """

    text = escape(text)
    text = re.sub(r'(@\w+)', r'<u>\1</u>', text)
    text = re.sub(r'(#\w+)', r'<i>\1</i>', text)
    text = re.sub(r'(http://[\w\./]+)', r'<u>\1</u>', text)

    if text.startswith("RT "):
        text = "<b>RT</b> " + text[3:]
    return text

def get_icon(user):
    cache_dir = "%s/litter" % glib.get_user_cache_dir()
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    filename = "%s/%s" % (cache_dir, urllib.quote_plus(user.profile_image_url))
    if not os.path.exists(filename):
        urllib.urlretrieve(user.profile_image_url, filename)
    return filename

def process_tweets(api, tweets, seen):
    """Display notifications for unseen tweets

    :type tweets: ``list`` of ``twitter.Status``
    :param api: Twitter status messages
    :type seen: ``list``
    :param seen: Already seen tweets
    """
    for m in reversed(tweets):
        if m.id in seen:
            continue
        else:
            icon = get_icon(m.user)
            n = pynotify.Notification("From %s %s " % (m.user.name,
                                                       m.relative_created_at),
                                      format_tweet(m.text), icon)
            if api._username in m.text:
                n.set_urgency(pynotify.URGENCY_CRITICAL)
            if m.text.startswith("@%s" % api._username):
                n.set_timeout(pynotify.EXPIRES_NEVER)
            if not n.show():
                raise OSError("Notification failed to display!")
            seen.append(m.id)
            time.sleep(4)

def update(api, seen):
    """Fetch updates and display notifications

    :type api: ``twitter.Api``
    :param api: Authenticated ``twitter.Api`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    """

    process_tweets(api, api.GetFriendsTimeline(), seen)
    return True

def update_stealth(api, seen, users):
    """Fetch updates and display notifications for stealth follows

    :type api: ``twitter.Api``
    :param api: Authenticated ``twitter.Api`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    :type users: ``list`` of ``str``
    :param users: Stealth follow user list
    """

    for user in users:
        process_tweets(api, api.GetUserTimeline(user), seen)
    return True

def main(argv):
    """main handler

    :type argv: ``list``
    :param argv: Command line parameters
    """

    if not pynotify.init(argv[0]):
        print "Unable to initialise pynotify!"
        return 1

    config_file = "%s/litter/config.ini" % glib.get_user_config_dir()
    if os.path.exists(config_file):
        conf = configobj.ConfigObj(config_file)
        if conf.has_key("stealth"):
            stealth_users = conf['stealth'].get("users")

    api = twitter.Api(os.getenv("TWEETUSERNAME"), os.getenv("TWEETPASSWORD"))
    api.SetUserAgent("litter/%s +http://github.com/JNRowe/litter/" % __version__)
    if os.path.exists("%s.dat" % argv[0]):
        seen = json.load(open("%s.dat" % argv[0]))
    else:
        seen = []

    def save_state(seen):
        """Seen tweets state saver

        :type seen: ``list``
        :param seen: Already seen tweets
        """
        json.dump(seen, open("%s.dat" % argv[0], "w"), indent=4)
    atexit.register(save_state, seen)

    loop = glib.MainLoop()
    if stealth_users:
        glib.timeout_add_seconds(300, update_stealth, api, seen, stealth_users)
    glib.timeout_add_seconds(300, update, api, seen)
    loop.run()

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))

