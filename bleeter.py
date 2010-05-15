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

__version__ = "0.4.1"
__date__ = "2010-04-21"
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
import hashlib
import operator
import optparse
import os
import re
import shutil
import sys
import subprocess
import urllib
import webbrowser
import warnings

from xml.sax import saxutils

try:
    import json
except ImportError: # pragma: no cover
    import simplejson as json

import configobj
import glib
import pynotify
import tweepy
import validate

try:
    import Image
except ImportError:
    pass

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except ImportError: # pragma: no cover
    gtk = False  # pylint: disable-msg=C0103

try:
    from reverend.thomas import Bayes
except ImportError: # pragma: no cover
    Bayes = None

try:
    import urlunshort
except ImportError: # pragma: no cover
    urlunshort = None

try:
    import termstyle
except ImportError: # pragma: no cover
    termstyle = None  # pylint: disable-msg=C0103

# Select colours if terminal is a tty
if termstyle:
    # pylint: disable-msg=C0103
    termstyle.auto()
    success = termstyle.green
    fail = termstyle.red
    warn = termstyle.yellow
else: # pragma: no cover
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


def mkdir(dir):
    """Create dir, including parents

    :type dir: ``str``
    :param dir: Directory to create
    :raise OSError: Unable to create directory

    """

    try:
        os.makedirs(os.path.expanduser(dir))
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def open_browser(url):
    """Open URL in user's browser

    :type uri: ``str``
    :param uri: URL to open

    """

    try:
        subprocess.call(["xdg-open", url])
    except OSError:
        try:
            webbrowser.open(url, new=2)
        except webbrowser.Error:
            message = "Failed to open link"
            print fail(message)
            error = pynotify.Notification("bleeter", message, "error")
            if not error.show():
                raise OSError("Notification failed to display!")
            return errno.EPERM


def find_app_icon(uri=True):
    """Find suitable bleeter application icon

    :type uri: ``bool``
    :param uri: Return a URI for the path
    :rtype: ``str``
    :return: Path to the application icon

    """
    icon_locations = [
        "%s/share/pixmaps/bleeter.png" % sys.prefix,
        "%s/bleeter/bleeter.png" % glib.get_user_cache_dir(),
        "%s/bleeter.png" % os.path.abspath(sys.path[0]),
        None,
    ]
    for icon in icon_locations:
        if os.path.exists(icon):
            break
    if not icon:
        raise EnvironmentError("Can't find application icon!")
    return "%s%s" % ("file://" if uri else "", icon)


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
                raise optparse.OptionValueError("%s must be at least 1"
                                                % opt_str)
        else:
            raise optparse.BadOptionError("%s unknown option to check"
                                          % opt_str)

    config_spec = [
        "timeout = integer(min=1, default=10)",
        "frequency = integer(min=60, default=300)",
        "token = list(default=list('', ''))",
        "stealth = list(default=list('ewornj'))",
        "ignore = list(default=list('#nowplaying'))",
        "tray = boolean(default=True)",
        "bayes = boolean(default=False)",
        "expand = boolean(default=False)",
    ]
    config = configobj.ConfigObj(config_file, configspec=config_spec)
    results = config.validate(validate.Validator())
    if results is not True:
        for key in filter(lambda k: not results[k], results):
            print fail("Config value for `%s' is invalid" % key)
        raise SyntaxError("Invalid configuration file")

    parser = optparse.OptionParser(usage="%prog [options...]",
                                   version="%prog v" + __version__,
                                   description=USAGE)

    parser.set_defaults(timeout=config["timeout"],
                        frequency=config["frequency"],
                        token=config.get("token"),
                        stealth=config.get("stealth"),
                        ignore=config.get("ignore"),
                        tray=config.get("tray"),
                        bayes=config.get("bayes"),
                        expand=config.get("expand"))

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
    parser.add_option("-i", "--ignore", action="store",
                      metavar=",".join(config.get("ignore")),
                      help="Keywords to ignore in tweets(comma separated)")
    parser.add_option("--no-tray", action="store_false",
                      dest="tray", help="Disable systray icon")
    parser.add_option("-b", "--bayes", action="store_true",
                      help="Enable Bayesian timeout adjustment")
    parser.add_option("-e", "--expand", action="store_true",
                      help="Expand links in tweets")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", help="Produce verbose output")
    parser.add_option("-q", "--quiet", action="store_false",
                      dest="verbose",
                      help="Output only matches and errors")

    options = parser.parse_args()[0]
    if isinstance(options.stealth, basestring):
        options.stealth = options.stealth.split(",")
    if isinstance(options.ignore, basestring):
        options.ignore = options.ignore.split(",")

    return options


def relative_time(timestamp):
    """Format a relative time

    >>> now = datetime.datetime.utcnow()
    >>> relative_time(now - datetime.timedelta(days=365))
    'last year'
    >>> relative_time(now - datetime.timedelta(days=70))
    'two months ago'
    >>> relative_time(now - datetime.timedelta(days=30))
    'last month'
    >>> relative_time(now - datetime.timedelta(days=21))
    'three weeks ago'
    >>> relative_time(now - datetime.timedelta(days=4))
    'four days ago'
    >>> relative_time(now - datetime.timedelta(days=1))
    'yesterday'
    >>> relative_time(now - datetime.timedelta(hours=5))
    'five hours ago'
    >>> relative_time(now - datetime.timedelta(hours=1))
    'an hour ago'
    >>> relative_time(now - datetime.timedelta(minutes=6))
    'six minutes ago'
    >>> relative_time(now - datetime.timedelta(seconds=12))
    '12 seconds ago'

    :type timestamp: ``datetime.datetime``
    :param timestamp: Event to generate relative timestamp against
    :rtype: ``str``
    :return: Human readable date and time offset
    """

    numstr = ". a two three four five six seven eight nine ten".split()

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
    if i == 1 and name in ("year", "month", "week"):
        result = "last %s" % name
    elif i == 1 and name == "day":
        result = "yesterday"
    elif i == 1 and name == "hour":
        result = "an hour ago"
    else:
        result = "%s %s%s ago" % (i if i > 10 else numstr[i], name,
                                  "s" if i > 1 else "")
    return result

# Keep a cache for free handling of retweets and such.
URLS = {}
def url_expand(m):
    """Generate links with expanded URLs

    >>> NOTIFY_SERVER_CAPS.extend(["body-markup", "body-hyperlinks"])
    >>> URLS["http://bit.ly/dunMgV"] = "http://jnrowe.github.com/vim-jnrowe/terminal.png"
    >>> format_tweet("See http://bit.ly/dunMgV",
    ...              True)
    'See <a href="http://jnrowe.github.com/vim-jnrowe/terminal.png">http://jnrowe.github.com/vim-jnrowe/terminal.png</a>'
    >>> NOTIFY_SERVER_CAPS[:] = []

    :type m: ``SRE_Match``
    :param m: Regular expression match object
    :rtype: ``str``
    :return: HTML formatted link for URL
    """
    url = m.group()
    if not url in URLS:
        if urlunshort.is_shortened(url):
            URLS[url] = urlunshort.resolve(url)
        else:
            URLS[url] = url
    return '<a href="%s">%s</a>' % (URLS[url], URLS[url])


def format_tweet(text, expand=False):
    """Format tweet for display

    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate #sup contacts from #abook'
    >>> NOTIFY_SERVER_CAPS.append("body-markup")
    >>> format_tweet("Populate #sup contacts from #abook")
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("RT @ewornj Populate #sup contacts from #abook")
    '<b>RT</b> @<u>ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet("@rachcholmes London marathon signup closed yet? ;)")
    '@<u>rachcholmes</u> London marathon signup closed yet? ;)'
    >>> format_tweet("Updated my vim colour scheme see http://bit.ly/dunMgV")
    'Updated my vim colour scheme see <u>http://bit.ly/dunMgV</u>'
    >>> NOTIFY_SERVER_CAPS.append("body-hyperlinks")
    >>> format_tweet("See http://bit.ly/dunMgV")
    'See <a href="http://bit.ly/dunMgV">http://bit.ly/dunMgV</a>'
    >>> format_tweet("@someone with a @someone/list")
    '@<a href="http://twitter.com/someone">someone</a> with a @<a href="http://twitter.com/someone/list">someone/list</a>'
    >>> format_tweet("See http://example.com/url-hyphen?and=parms")
    'See <a href="http://example.com/url-hyphen?and=parms">http://example.com/url-hyphen?and=parms</a>'
    >>> format_tweet("Handle ampersands & win")
    'Handle ampersands &amp; win'
    >>> format_tweet("entity test, & \\" ' < >")
    'entity test, &amp; &quot; &apos; &lt; &gt;'
    >>> NOTIFY_SERVER_CAPS[:] = []

    :type text: ``str``
    :param api: Tweet content
    :type expand: ``bool``
    :param expand: Expand links in tweet text
    :rtype: ``str``
    :return: Tweet content with pretty formatting
    """

    # Sanitize entity escaping for input
    text = glib.markup_escape_text(saxutils.unescape(text))

    # re is smart enough to use pre-cached versions
    url_match = re.compile(r'(http://[\w\.?=\+/_-]+)')
    user_match = re.compile(r'@(\w+(/\w+)?)')
    hashtag_match = re.compile(r'(#\w+)')

    if "body-markup" in NOTIFY_SERVER_CAPS:
        if "body-hyperlinks" in NOTIFY_SERVER_CAPS:
            if expand:
                text = url_match.sub(url_expand, text)
            else:
                text = url_match.sub(r'<a href="\1">\1</a>', text)
            text = user_match.sub(r'@<a href="http://twitter.com/\1">\1</a>',
                                  text)
            text = hashtag_match.sub(r'<a href="http://twitter.com/search?q=\1">\1</a>',
                                     text)
        else:
            text = url_match.sub(r'<u>\1</u>', text)
            text = user_match.sub(r'@<u>\1</u>', text)
            text = hashtag_match.sub(r'<i>\1</i>', text)

        if text.startswith("RT "):
            text = "<b>RT</b> " + text[3:]
    return text


def get_user_icon(user):
    """Get icon location for user

    :type user: ``tweepy.models.User``
    :param user: Tweet user reference
    :rtype: ``str``
    :return: Location of the icon file
    """

    cache_dir = "%s/bleeter" % glib.get_user_cache_dir()
    mkdir(cache_dir)
    filename = "%s/%s" % (cache_dir,
                          hashlib.md5(user.profile_image_url).hexdigest())
    if not os.path.exists(filename):
        try:
            urllib.urlretrieve(user.profile_image_url, filename)
        except IOError:
            # Fallback to application icon
            if not os.path.exists("%s/bleeter.png" % cache_dir):
                shutil.copy(find_app_icon(), cache_dir)
            filename = "%s/bleeter.png" % cache_dir
        if gtk:
            icon = gtk.gdk.pixbuf_new_from_file(filename)
            if not (icon.get_width(), icon.get_height()) == (48, 48):
                icon = icon.scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
                icon.save(filename, "png")
        else:
            icon = Image.open(filename)
            if not icon.size == (48, 48):
                icon = icon.resize((48, 48), Image.ANTIALIAS)
                icon.save(filename, "png")

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

        open_browser("http://twitter.com/%s/status/%s"
                     % (tweet.user.screen_name, tweet.id))
    return show


def open_geo(tweet):
    """"Create tweet opening function for location

    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to open
    :rtype: ``FunctionType``
    :return: Wrapper to open tweet location in browser
    """

    def show(notification, action):  # pylint: disable-msg=W0613
        """Open tweet location in browser

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        latlon = ",".join(map(str, tweet.geo['coordinates']))

        # TODO: Perhaps make the new tab, new window, etc configurable?
        open_browser("http://maps.google.com/maps?q=%s@%s&sll=%s&z=16"
                     % (tweet.user.screen_name, latlon, latlon))
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

def train_bayes(guesser, bucket, tweet):
    """"Create tweet opening function for location

    :type guesser: ``Bayes`` or ``None``
    :param guesser: Tweet Bayesian database, if available
    :type bucket: ``str``
    :param bucket: Bucket to adjust
    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to open
    :rtype: ``FunctionType``
    :return: Wrapper to update the Bayesian database
    """

    def train(notification, action):  # pylint: disable-msg=W0613
        """Open tweet location in browser

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        guesser.train(bucket, tweet.text.lower())
    return train


def skip_check(ignore):
    """"Create tweet skip testing wrapper function

    >>> filt = skip_check(["#nowplaying", "@boring"])
    >>> tweet = tweepy.models.Status()
    >>> tweet.text = "This is a test"
    >>> filt(tweet)
    True
    >>> tweet.text = "This is a test #nowplaying"
    >>> filt(tweet)
    False
    >>> tweet.text = "Reply to @boring"
    >>> filt(tweet)
    False

    :type ignore: ``list`` of ``str``
    :param ignore: List of words to trigger tweet skipping
    :rtype: ``FunctionType``
    :return: Wrapper to scan tweets
    """

    def wrapper(tweet):
        """Filter tweets containing user selected words

        :type tweet: ``tweepy.models.Status``
        :param tweet: Twitter status message to scan for selected words
        :rtype: ``bool``
        :return: True if tweet is clean
        """

        # Not just \W, because of the special case of # and @ in tweets
        word_match = re.compile("[^a-zA-Z0-9_#@]")

        return not any(map(ignore.__contains__, re.split(word_match,
                                                         tweet.text)))
    return wrapper


def update(tweets, api, seen, users, ignore):
    """Fetch new tweets

    :type tweets: ``collections.deque``
    :param tweets: Tweets awaiting display
    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type seen: ``dict``
    :param seen: Last seen status
    :type users: ``list`` of ``str``
    :param users: Stealth follow user list
    :type ignore: ``list`` of ``str``
    :param ignore: List of words to trigger tweet skipping
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
        seen["fetched"] = new_tweets[-1].id
        tweets.extend(filter(skip_check(ignore), new_tweets))

    return True


NOTIFICATIONS = {}
def display(me, tweets, seen, timeout, guesser, expand):
    """Display notifications for new tweets

    :type me: ``tweepy.models.User``
    :param me: Authenticated user object
    :type tweets: ``collections.deque``
    :param tweets: Tweets awaiting display
    :type seen: ``dict``
    :param seen: Last seen status
    :type timeout: ``tweepy.api.API``
    :param timeout: Timeout for notifications in seconds
    :type guesser: ``Bayes`` or ``None``
    :param guesser: Tweet Bayesian database, if available
    :type expand: ``bool``
    :param expand: Whether to expand links in tweet text
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue

    """

    try:
        tweet = tweets.popleft()
    except IndexError:
        # No tweets awaiting display
        return True

    # tweets are sorted at this point, so this is a simple duplicate filter
    if tweet.id <= seen["displayed"]:
        return True

    note = pynotify.Notification("From %s about %s"
                                 % (tweet.user.name,
                                    relative_time(tweet.created_at)),
                                 format_tweet(tweet.text, expand),
                                 get_user_icon(tweet.user))
    if "actions" in NOTIFY_SERVER_CAPS:
        note.add_action("default", " ", open_tweet(tweet))
        note.add_action("mail-forward", "retweet",
                        method_tweet(tweet, "retweet"))
        # In case this has been seen in another client
        if not tweet.favorited:
            note.add_action("bookmark", "Fave",
                            method_tweet(tweet, "favorite"))
        if tweet.geo:
            note.add_action("find", "Geo", open_geo(tweet))
        if guesser is not None:
            note.add_action("up", "Like", train_bayes(guesser, "like", tweet))
            note.add_action("down", "Dislike",
                            train_bayes(guesser, "dislike", tweet))
        # Keep a reference for handling the action.
        NOTIFICATIONS[hash(note)] = note
        note.connect_object("closed", NOTIFICATIONS.pop, hash(note))
    if guesser is not None:
        result = collections.defaultdict(int)
        result.update(guesser.guess(tweet.text.lower()))
        mult = result["like"] - result["dislike"]
        note.set_timeout(timeout * 1000 * (mult if mult > 1 else 1))
    else:
        note.set_timeout(timeout * 1000)
    note.set_category("im.received")
    if me.screen_name in tweet.text:
        note.set_urgency(pynotify.URGENCY_CRITICAL)
    if tweet.text.startswith(("@%s" % me.screen_name, ".@%s" % me.screen_name)):
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

    n = len(tweets)

    icon.set_visible(n)
    icon.set_tooltip("%i tweets awaiting display" % n)
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

    state_file = "%s/bleeter/state.db" % glib.get_user_data_dir()
    lock_file = "%s.lock" % state_file

    # Create directory for state storage
    mkdir(os.path.dirname(lock_file))
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
        mkdir(os.path.dirname(config_file))
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

    if Bayes and options.bayes:
        bayes_db = "%s/bleeter/bayes.db" % glib.get_user_data_dir()
        guesser = Bayes()
        if os.path.exists(bayes_db):
            guesser.load(bayes_db)
    else:
        guesser = None
    if not Bayes and options.bayes:
        message = "Bayes support requires the reverend module"
        print warn(message)
        note = pynotify.Notification("bleeter v%s" % (__version__), message,
                                     "stock_dialog-warning")
        note.set_urgency(pynotify.URGENCY_LOW)
        if not note.show():
            raise OSError("Notification failed to display!")

    if not urlunshort and options.expand:
        message = "Link expansion support requires the urlunshort module"
        print warn(message)
        note = pynotify.Notification("bleeter v%s" % (__version__), message,
                                     "stock_dialog-warning")
        note.set_urgency(pynotify.URGENCY_LOW)
        if not note.show():
            raise OSError("Notification failed to display!")
        options.expand = False

    auth.set_access_token(*options.token)
    api = tweepy.API(auth)

    if os.path.exists(state_file):
        seen = json.load(open(state_file))
        # Reset displayed, so we don't miss pending tweets from a previous run
        seen['fetched'] = seen["displayed"]
    else:
        seen = {"displayed": 1, "fetched": 1}

    def save_state(seen, guesser):
        """Seen tweets state saver

        :type seen: ``list``
        :param seen: Already seen tweets
        :type guesser: ``Bayes`` or ``None``
        :param guesser: Tweet Bayesian database

        """
        json.dump(seen, open(state_file, "w"), indent=4)
        if guesser:
            guesser.save(bayes_db)

    atexit.register(save_state, seen, guesser)

    if options.verbose or not options.tray:
        # Show a "hello" message, as it can take some time the first real
        # notification
        note = pynotify.Notification("bleeter v%s" % (__version__), "Started",
                                     find_app_icon())
        note.set_timeout(options.timeout * 1000)
        note.set_urgency(pynotify.URGENCY_LOW)
        if not note.show():
            raise OSError("Notification failed to display!")

    tweets = collections.deque(maxlen=options.frequency / (options.timeout + 1))

    loop = glib.MainLoop()
    if options.tray:
        if not gtk:
            message = "`pygtk' is required for systray support"
            print fail(message)
            error = pynotify.Notification("Missing pygtk", message,
                                          "error")
            error.set_timeout(options.timeout * 1000)
            if not error.show():
                raise OSError("Notification failed to display!")
            return errno.EPERM

        icon = gtk.status_icon_new_from_file(find_app_icon(uri=False))
        icon.set_tooltip("Initial update in progress")
        icon.connect("activate", lambda x: open_browser("http://twitter.com/"))

        # Make sure icon is set up, before entering update()
        ctx = loop.get_context()
        while ctx.pending():
            ctx.iteration()

    try:
        me = api.me()
    except tweepy.TweepError:
        message = "Talking to twitter failed.  Is twitter or your network down?"
        print fail(message)
        error = pynotify.Notification("Network error", message,
                                      "error")
        error.set_timeout(options.timeout * 1000)
        if not error.show():
            raise OSError("Notification failed to display!")
        return errno.EIO
    update(tweets, api, seen, options.stealth, options.ignore)

    glib.timeout_add_seconds(options.frequency, update, tweets, api, seen,
                             options.stealth, options.ignore)
    glib.timeout_add_seconds(options.timeout + 1, display, me, tweets, seen,
                             options.timeout, guesser, options.expand)
    if options.tray:
        glib.timeout_add_seconds(options.timeout // 2, tooltip, icon, tweets)
    loop.run()

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[:]))
    except KeyboardInterrupt:
        pass
