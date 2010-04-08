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

__version__ = "0.3.0"
__date__ = "2010-04-07"
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
import collections
import datetime
import errno
import operator
import optparse
import os
import re
import shutil
import sys
import urllib
import warnings
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json

import configobj
import glib
import pynotify
import tweepy
import validate

import pygtk
pygtk.require('2.0')
import gtk

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

# OAuth design FTL!
OAUTH_KEY = "WJ3RGn3aMN98b41b3pJQ"
OAUTH_SECRET = "PU0b7yrBOcdpbSrD1pcQq1kfA9ZVmPQoD0fqtg1bQBQ"
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

    def check_value(option, opt_str, value, parser):
        """Check frequency value is within bounds"""

        # pylint: disable-msg=W0613

        if "--frequency" in opt_str:
            if value < 60:
                raise optparse.OptionValueError("%s must be at least 60"
                                                % opt_str)
        elif "--timeout" in opt_str:
            if value < 1:
                raise optparse.OptionValueError("%s must be at least 60"
                                                % opt_str)
        else:
            raise optparse.BadOptionError("%s unknown option to check"
                                          % opt_str)

    config_spec = [
        "timeout = integer(min=1, default=10)",
        "frequency = integer(min=60, default=300)",
        "token = list(default=list('', ''))",
        "stealth = list(default=list('ewornj'))",
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
                        token=config.get("token"),
                        stealth=config.get("stealth"))

    parser.add_option("-t", "--timeout", action="callback", type="int",
                      metavar=config["timeout"],
                      callback=check_value,
                      help="Timeout for notification popups in seconds")
    parser.add_option("-f", "--frequency", action="callback", type="int",
                      metavar=config["frequency"],
                      callback=check_value,
                      help="Update frequency in in seconds")
    parser.add_option("-r", "--token", action="store",
                      metavar="<key>,<secret>",
                      help="OAuth token for twitter")
    parser.add_option("-g", "--get-token", action="store_true",
                      help="Generate a new OAuth token for twitter")
    parser.add_option("-s", "--stealth", action="store",
                      metavar=",".join(config.get("stealth")),
                      help="Users to watch without following(comma separated)")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", help="Produce verbose output")
    parser.add_option("-q", "--quiet", action="store_false",
                      dest="verbose",
                      help="Output only matches and errors")

    options = parser.parse_args()[0]
    if isinstance(options.stealth, basestring):
        options.stealth = options.stealth.split(",")

    return options


def relative_time(timestamp):
    """Format a relative time

    >>> now = datetime.datetime.utcnow()
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

    delta = datetime.datetime.utcnow() - timestamp
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
        except IOError:
            # Fallback to application icon
            if not os.path.exists("%s/bleeter.png" % cache_dir):
                shutil.copy("%s/bleeter.png" % sys.path[0], cache_dir)
            filename = "%s/bleeter.png" % cache_dir
        icon = gtk.gdk.pixbuf_new_from_file(filename)
        if not (icon.get_width(), icon.get_height()) == (48, 48):
            icon = icon.scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
            icon.save(filename)

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


def method_tweet(tweet, method):
    """"Create Status method wrapper function

    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to favourite
    :type method: ``str``
    :param method: Method to wrap
    :rtype: ``FunctionType``
    :return: Wrapper to tweet method
    """

    def wrapper(notification, action):  # pylint: disable-msg=W0613
        """Mark tweet as favourite

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        getattr(tweet, method)()
    return wrapper


def update(tweets, api, seen, users):
    """Fetch new tweets

    :type tweets: ``collections.deque``
    :param tweets: Tweets awaiting display
    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type seen: ``dict``
    :param seen: Last seen status
    :type users: ``list`` of ``str``
    :param users: Stealth follow user list
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue
    """

    headers = {"User-Agent": USER_AGENT}

    old_seen = seen["fetched"]
    try:
        new_tweets = api.home_timeline(since_id=old_seen, headers=headers)
        new_tweets.extend(api.mentions(since_id=old_seen, headers=headers))
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
            new_tweets.extend(api.user_timeline(user, since_id=old_seen,
                                                headers=headers))
        except tweepy.TweepError, e:
            error = pynotify.Notification("Fetching user data failed",
                                          "Data for `%s' not available" % user,
                                          "error")
            if not error.show():
                raise OSError("Notification failed to display!")
            warnings.warn("Stealth data fetch failed: %s" % e.reason)
            # Still return True, so we re-enter the loop
            return True

    if new_tweets:
        new_tweets = sorted(new_tweets, key=operator.attrgetter("id"))

        tweets.extend(new_tweets)
        seen["fetched"] = new_tweets[-1].id

    return True


NOTIFICATIONS = {}
def display(me, tweets, seen, timeout):
    """Display notifications for new tweets

    :type me: ``tweepy.models.User``
    :param me: Authenticated user object
    :type tweets: ``collections.deque``
    :param tweets: Tweets awaiting display
    :type seen: ``dict``
    :param seen: Last seen status
    :type timeout: ``tweepy.api.API``
    :param timeout: Timeout for notifications in seconds
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue
    """

    try:
        tweet = tweets.popleft()
    except IndexError:
        # No tweets awaiting display
        return True

    note = pynotify.Notification("From %s about %s"
                                 % (tweet.user.name,
                                    relative_time(tweet.created_at)),
                                 format_tweet(tweet.text),
                                 get_icon(tweet.user))
    if "actions" in NOTIFY_SERVER_CAPS:
        note.add_action("default", " ", open_tweet(tweet))
        note.add_action("mail-forward", "retweet",
                        method_tweet(tweet, "retweet"))
        # In case this has been seen in another client
        if not tweet.favorited:
            note.add_action("bookmark", "Fave",
                            method_tweet(tweet, "favorite"))
        # Keep a reference for handling the action.
        NOTIFICATIONS[hash(note)] = note
        note.connect_object("closed", NOTIFICATIONS.pop, hash(note))
    note.set_timeout(timeout * 1000)
    note.set_category("im.received")
    if me.name in tweet.text:
        note.set_urgency(pynotify.URGENCY_CRITICAL)
    if tweet.text.startswith("@%s" % me.name):
        note.set_timeout(pynotify.EXPIRES_NEVER)
    if not note.show():
        # Fail hard at this point, recovery has little value.
        raise OSError("Notification failed to display!")
    seen["displayed"] = tweet.id
    return True


def tooltip(icon, tweets):
    """Update statusicon tooltip

    :type icon: ``gtk.StatusIcon``
    :param icon: Status icon to update
    :type tweets: ``collections.deque``
    :param tweets: Tweets pending display
    """

    icon.set_tooltip("%i tweets awaiting display" % len(tweets))
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
    options = process_command_line(config_file)

    state_file = "%s/bleeter/state.db" % glib.get_user_config_dir()
    lock_file = "%s.lock" % state_file

    if os.path.exists(lock_file):
        print fail("Another instance is running, or `%s' is stale" % lock_file)
        return errno.EBUSY
    lock = open(lock_file, "w")
    lock.write("locked")

    atexit.register(os.unlink, lock_file)

    auth = tweepy.OAuthHandler(OAUTH_KEY, OAUTH_SECRET)
    if options.get_token:
        try:
            print "Visit `%s' to fetch the new OAuth token" \
                % auth.get_authorization_url()
        except tweepy.TweepError:
            print fail("Talking to twitter failed.  "
                       "Is twitter or your network down?")
            return errno.EIO
        while True:
            verifier = raw_input("Input verifier? ")
            if verifier:
                break
            print fail("You must supply a verifier")
        try:
            token = auth.get_access_token(verifier.strip())
        except tweepy.TweepError:
            print fail("Fetching token failed")
            return errno.EIO
        conf = configobj.ConfigObj(config_file)
        conf['token'] = [token.key, token.secret]
        conf.write()
        print success("Token set!")
        return 0

    if not options.token or not all(options.token):
        message = "Use `%s --get-token' from the command line to set it" \
            % sys.argv[0]
        print fail(message)
        error = pynotify.Notification("No OAuth token for bleeter", message,
                                      "error")
        error.set_timeout(options.timeout * 1000)
        if not error.show():
            raise OSError("Notification failed to display!")
        return errno.EPERM

    auth.set_access_token(*options.token)
    api = tweepy.API(auth)
    me = api.me()

    if os.path.exists(state_file):
        seen = json.load(open(state_file))
        # Reset displayed, so we don't miss pending tweets from a previous run
        seen['fetched'] = seen["displayed"]
    else:
        seen = {"displayed": 1, "fetched": 1}

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
                                     "%s/bleeter.png" % sys.path[0])
        note.set_timeout(options.timeout * 1000)
        note.set_urgency(pynotify.URGENCY_LOW)
        if not note.show():
            raise OSError("Notification failed to display!")

    tweets = collections.deque(maxlen=options.frequency / (options.timeout + 1))

    loop = glib.MainLoop()
    icon = gtk.status_icon_new_from_file("%s/bleeter.png" % sys.path[0])
    icon.set_tooltip("Initial update in progress")

    # Make sure icon is set up, before entering update()
    ctx = loop.get_context()
    while ctx.pending():
        ctx.iteration()

    update(tweets, api, seen, options.stealth)
    glib.timeout_add_seconds(options.frequency, update, tweets, api, seen,
                             options.stealth)
    glib.timeout_add_seconds(options.timeout + 1, display, me, tweets, seen,
                             options.timeout)
    glib.timeout_add_seconds(options.timeout // 2, tooltip, icon, tweets)
    loop.run()

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[:]))
    except KeyboardInterrupt:
        pass
