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
import errno
import operator
import optparse
import os
import re
import sys
import time
import urllib
import warnings
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json

import Image
import configobj
import glib
import pynotify
import tweepy
import validate

try:
    import termstyle
except ImportError:
    termstyle = None  # pylint: disable-msg=C0103

# Select colours if terminal is a tty
if termstyle:
    # pylint: disable-msg=C0103
    termstyle.auto()
    success = termstyle.green
    fail = termstyle.red
    warn = termstyle.yellow
else:
    # pylint: disable-msg=C0103
    success = fail = warn = str


USER_AGENT = "bleeter/%s +http://github.com/JNRowe/bleeter/" % __version__
NOTIFY_SERVER_CAPS = []

# Pull the first paragraph from the docstring
USAGE = __doc__[:__doc__.find('\n\n', 100)].splitlines()[2:]
# Replace script name with optparse's substitution var, and rebuild string
USAGE = "\n".join(USAGE).replace("bleeter", "%prog")


def process_command_line(config_file):
    """Main command line interface

    :type config_file: ``str``
    :param config_file: Location of the configuration file
    :rtype: ``tuple`` of ``optparse`` and ``list``
    :return: Parsed options and arguments
    """

    def check_frequency(option, opt_str, value, parser):
        """Check frequency value is within bounds"""

        if value < 60:
            raise optparse.OptionValueError("%s must be at least 60" % opt_str)

    config_spec = [
        "timeout = integer(default=5)",
        "frequency = integer(min=60, default=60)",
        "user = string(default=os.getenv('LOGNAME'))",
        "password = string",
        "stealth = list",
    ]
    config = configobj.ConfigObj(config_file, configspec=config_spec)
    results = config.validate(validate.Validator())
    if results is not True:
        for key in filter(lambda k: not results[k], results):
            print fail("Config value for `{0}' is invalid".format(key))
        raise SyntaxError("Invalid configuration file")

    parser = optparse.OptionParser(usage="%prog [options...]",
                                   version="%prog v" + __version__,
                                   description=USAGE)

    parser.set_defaults(timeout=config["timeout"],
                        frequency=config["frequency"],
                        user=config["user"],
                        password=config.get("password"),
                        stealth=config.get("stealth"))

    parser.add_option("-t", "--timeout", action="store", type="int",
                      metavar=config["timeout"],
                      help="Timeout for notification popups in seconds")
    parser.add_option("-f", "--frequency", action="callback", type="int",
                      metavar=config["frequency"],
                      callback=check_frequency,
                      help="Update frequency in in seconds")
    parser.add_option("-u", "--user", action="store",
                      metavar=config["user"],
                      help="Twitter user account name")
    parser.add_option("-p", "--password", action="store",
                      metavar="<from config>" if config.get("password") else "",
                      help="Twitter user account password")
    parser.add_option("-s", "--stealth", action="store",
                      metavar=",".join(config.get("stealth")),
                      help="Users to watch without following(comma separated)")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", help="Produce verbose output")
    parser.add_option("-q", "--quiet", action="store_false",
                      dest="verbose",
                      help="Output only matches and errors")

    options, args = parser.parse_args()
    if isinstance(options.stealth, basestring):
        options.stealth = options.stealth.split(",")

    return options, args


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

    :type timestamp: ``datetime.datetime``
    :param timestamp: Event to generate relative timestamp against
    :rtype: ``str``
    :return: Human readable date and time offset
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

    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate #sup contacts from #abook'
    >>> NOTIFY_SERVER_CAPS.append("body-markup")
    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("RT @ewornj Populate #sup contacts from #abook")
    '<b>RT</b> <u>@ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("@rachcholmes London marathon signup closed yet? ;)")
    '<u>@rachcholmes</u> London marathon signup closed yet? ;)'
    >>> format_tweet("Updated my vim colour scheme see http://bit.ly/dunMgV")
    'Updated my vim colour scheme see <u>http://bit.ly/dunMgV</u>'
    >>> NOTIFY_SERVER_CAPS.append("body-hyperlinks")
    >>> format_tweet("See http://bit.ly/dunMgV")
    'See <a href="http://bit.ly/dunMgV">http://bit.ly/dunMgV</a>'

    :type text: ``str``
    :param api: Tweet content
    :rtype: ``str``
    :return: Tweet content with pretty formatting
    """

    text = glib.markup_escape_text(text)
    if "body-markup" in NOTIFY_SERVER_CAPS:
        text = re.sub(r'(@\w+)', r'<u>\1</u>', text)
        text = re.sub(r'(#\w+)', r'<i>\1</i>', text)
        if "body-hyperlinks" in NOTIFY_SERVER_CAPS:
            text = re.sub(r'(http://[\w\./]+)', r'<a href="\1">\1</a>', text)
        else:
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
            # If GTK becomes a dependency this would be better handled with
            # a gtk.gdk.Pixbuf object, until that day PIL is much lighter.
            icon = Image.open(filename)
            if not icon.size == (48, 48):
                icon.resize((48, 48), Image.ANTIALIAS).save(filename)
        except IOError:
            # Fallback to generic icon, if it exists
            filename = "%s/bleeter.png" % cache_dir
    return "file://%s" % filename


def open_tweet(tweet):
    """"Create tweet opening function

    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to open
    :rtype: ``FunctionType``
    :return: Wrapper to open tweet in browser
    """

    def show(notification, action):  # pylint: disable-msg=W0613
        """Open tweet in browser

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        # TODO: Perhaps make the new tab, new window, etc configurable?
        webbrowser.open("http://twitter.com/%s/status/%s"
                        % (tweet.user.screen_name, tweet.id),
                        new=2)
    return show

def fave_tweet(tweet):
    """"Create favouriting function

    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to favourite
    :rtype: ``FunctionType``
    :return: Wrapper to favourite tweet
    """

    def fave(notification, action):  # pylint: disable-msg=W0613
        """Mark tweet as favourite

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        tweet.favorite()
    return fave


NOTIFICATIONS = {}
def update(api, seen, users, timeout, note=None):
    """Fetch updates and display notifications

    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    :type users: ``list`` of ``str``
    :param users: Stealth follow user list
    :type timeout: ``tweepy.api.API``
    :param timeout: Timeout for notifications in seconds
    :type note: ``pynotify.Notification``
    :param note: Note to close once new tweets are fetched
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue
    """

    headers = {"User-Agent": USER_AGENT}
    try:
        tweets = api.home_timeline(headers=headers)
        tweets.extend(api.mentions(headers=headers))
    except tweepy.TweepError, e:
        error = pynotify.Notification("Fetching user data failed", "",
                                      "error")
        if not error.show():
            raise OSError("Notification failed to display!")
        warnings.warn("User data fetch failed: %s" % e.reason)
        # Still return True, so we re-enter the loop
        return True

    for user in users:
        try:
            tweets.extend(api.user_timeline(user, headers=headers))
        except tweepy.TweepError, e:
            error = pynotify.Notification("Fetching user data failed",
                                          "Data for `%s' not available" % user,
                                          "error")
            if not error.show():
                raise OSError("Notification failed to display!")
            warnings.warn("User data fetch failed: %s" % e.reason)
            # Still return True, so we re-enter the loop
            return True
    old_seen = seen.get("latest", 0)
    tweets = filter(lambda x: x.id > old_seen, tweets)

    if note and tweets:
        note.close()

    for tweet in sorted(tweets, key=operator.attrgetter("id")):
        note = pynotify.Notification("From %s about %s"
                                     % (tweet.user.name,
                                        relative_time(tweet.created_at)),
                                     format_tweet(tweet.text),
                                     get_icon(tweet.user))
        if "actions" in NOTIFY_SERVER_CAPS:
            note.add_action("default", " ", open_tweet(tweet))

            # In case this has been seen in another client
            if not tweet.favorited:
                note.add_action("bookmark", "Fave", fave_tweet(tweet))

            # Keep a reference for handling the action.
            NOTIFICATIONS[tweet.id] = note
        note.set_timeout(timeout * 1000)
        note.set_category("im.received")
        if api.auth.username in tweet.text:
            note.set_urgency(pynotify.URGENCY_CRITICAL)
        if tweet.text.startswith("@%s" % api.auth.username):
            note.set_timeout(pynotify.EXPIRES_NEVER)
        if not note.show():
            # Fail hard at this point, recovery has little value.
            raise OSError("Notification failed to display!")
        seen["latest"] = tweet.id
    # We only need to reap references if we're handling actions.
    if "actions" in NOTIFY_SERVER_CAPS:
        for note in NOTIFICATIONS:
            if note <= old_seen:
                NOTIFICATIONS[note].close()
                del NOTIFICATIONS[note]
    return True


def main(argv):
    """Main handler

    :type argv: ``list``
    :param argv: Command line parameters
    :rtype: ``int``
    :return: Shell return value
    """

    if not pynotify.init(argv[0]):
        print fail("Unable to initialise pynotify!")
        return errno.EIO
    NOTIFY_SERVER_CAPS.extend(pynotify.get_server_caps())

    config_file = "%s/bleeter/config.ini" % glib.get_user_config_dir()
    try:
        options, args = process_command_line(config_file)  # pylint: disable-msg=W0612
    except SyntaxError:
        sys.exit(1)

    state_file = "%s/bleeter/state.db" % glib.get_user_config_dir()

    if not options.user:
        print fail("No user set in %s and $TWEETUSERNAME not set" % config_file)
        return errno.EPERM
    if not options.password:
        print fail("No password set in %s and $TWEETPASSWORD not set"
                   % config_file)
        return errno.EPERM

    auth = tweepy.BasicAuthHandler(options.user, options.password)
    api = tweepy.API(auth)
    if os.path.exists(state_file):
        seen = json.load(open(state_file))
    else:
        seen = {}

    def save_state(seen):
        """Seen tweets state saver

        :type seen: ``list``
        :param seen: Already seen tweets
        """
        json.dump(seen, open(state_file, "w"), indent=4)
    atexit.register(save_state, seen)

    if options.verbose:
        # Show a "hello" message, as it can take some time the first real
        # notification
        note = pynotify.Notification("bleeter v%s" % (__version__), "Started",
                                     "%s/bleeter/bleeter.png" % glib.get_user_cache_dir())
        note.set_timeout(options.timeout * 1000)
        if not note.show():
            raise OSError("Notification failed to display!")
    else:
        note = None

    update(api, seen, options.stealth, options.timeout, note)
    if os.getenv("DEBUG_BLEETER"):
        sys.exit(1)

    loop = glib.MainLoop()
    glib.timeout_add_seconds(options.frequency, update, api, seen,
                             options.stealth, options.timeout)
    loop.run()

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[:]))
    except KeyboardInterrupt:
        pass
