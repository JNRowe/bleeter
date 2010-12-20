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

from __future__ import print_function

__version__ = "0.8.0-git"
__date__ = "2010-12-20"
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
import copy
import collections
import datetime
import errno
import hashlib
import optparse
import os
import re
import shutil
import sys
import subprocess
import time
import urllib
import webbrowser

from xml.sax import saxutils

import json

import configobj
import glib
import pynotify
import tweepy
import validate

import pygtk
pygtk.require('2.0')
import gtk

try:
    import urlunshort  # pylint: disable-msg=F0401
except ImportError:  # pragma: no cover
    urlunshort = None  # pylint: disable-msg=C0103

try:
    from termcolor import colored
except ImportError:  # pragma: no cover
    colored = None  # pylint: disable-msg=C0103

# Select colours if terminal is a tty
if colored and sys.stdout.isatty():
    success = lambda s: colored(s, "green")
    fail = lambda s: colored(s, "red")
    warn = lambda s: colored(s, "yellow")
else:  # pragma: no cover
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


class State(object):
    """Bleeter state handling"""

    _version = 1

    def __init__(self, users=None, lists=None, searches=None):
        """Initialise a new ``State`` object

        # Test mocks
        >>> atexit.register = lambda *args, **kwargs: True
        >>> glib.get_user_data_dir = lambda: "test/xdg_data_home"

        >>> state = State()
        >>> state.fetched["self-status"]
        16460438496

        # Test no config
        >>> glib.get_user_data_dir = lambda: "None"
        >>> state = State()
        >>> state.fetched["self-status"]
        1

        :type users: ``list``
        :param users: Stealth users to watch
        :type lists: ``list``
        :param lists: Authenticated user's lists
        :type searches: ``list``
        :param lists: Authenticated user's saved searches
        """
        self.state_file = "%s/bleeter/state.db" % glib.get_user_data_dir()

        self.users = users if users else []
        self.lists = lists if lists else []
        self.searches = searches if searches else []

        # Hold previous state, for save handling
        self._data = {"fetched": {}}

        self.displayed = collections.defaultdict(lambda: 1)
        self.fetched = collections.defaultdict(lambda: 1)
        if os.path.exists(self.state_file):
            data = json.load(open(self.state_file))
            # Keep loaded data, this keeps state data we're not using on this
            # run
            self._data = data
            if data.get("version", 1) == 1:
                self.fetched.update(data["fetched"])
                self.displayed.update(data["fetched"])
                if "user" in data and data["user"] in self.users:
                    for i in range(self.users.index(data["user"])):
                        self.get_user()
                if "list" in data and data["list"] in self.lists:
                    for i in range(self.lists.index(data["list"])):
                        self.get_list()
                if "search" in data and data["search"] in self.searches:
                    for i in range(self.searches.index(data["search"])):
                        self.get_search()
            else:
                raise NotImplementedError("Unsupported state file format")

        atexit.register(self.save_state, force=True)
        # Shutdown can take a long time, especially with lots of lists or
        # stealth follows.
        atexit.register(sys.stderr.write, warn("Shutting down\n"))

    def get_user(self):
        """Return next stealth user to update

        :rtype: ``str``
        :return: Next stealth user to update
        :raise IndexError: When user list is empty
        """
        user = self.users[0]
        # Rotate users list
        self.users.append(self.users.pop(0))
        return user

    def get_list(self):
        """Return next list to update

        :rtype: ``tweepy.models.List``
        :return: Next list to update
        :raise IndexError: When user lists are empty
        """
        list_ = self.lists[0]
        # Rotate user's lists
        self.lists.append(self.lists.pop(0))
        return list_

    def get_search(self):
        """Return next saved search to update

        :rtype: ``tweepy.models.SavedSearch``
        :return: Next saved search to update
        :raise IndexError: When user's saved searches are empty
        """
        search = self.searches[0]
        # Rotate user's lists
        self.searches.append(self.searches.pop(0))
        return search

    def save_state(self, force=False):
        """Seen tweets state saver

        We store displayed, not fetched, info so we don't miss pending tweets
        from a previous run

        :type force: ``bool``
        :param force: Force update, even if data hasn't changed for mtime
            promotion
        """
        data = copy.deepcopy(self._data)
        data["fetched"].update(self.displayed)
        if self.users:
            data["user"] = self.get_user()
        if self.lists:
            data["list"] = self.get_list().name
        if self.searches:
            data["search"] = self.get_search().name

        # Store state version
        data["version"] = self._version
        if force or not data == self._data:
            state_dump = json.dumps(data, indent=4)
            open(self.state_file, "w").write(state_dump)

        self._data = data


class Tweets(dict):
    """Object for holding tweets pending display

    Using a dictionary subclass affords us a free ID-based duplicate filter
    """
    def popitem(self):
        """Pop tweet with oldest ID

        :rtype: ``tweepy.models.Status``
        :return: Oldest tweet
        :raise KeyError: Tweets is empty
        """
        if not self:
            raise KeyError('popitem(): object is empty')
        return self.pop(min(self.keys()))

    def add(self, tweets):
        """Add new tweets to the store

        :type tweets: ``list``
        :param tweets: Tweets to add store
        """
        for tweet in tweets:
            self[tweet.id] = tweet


def mkdir(directory):
    """Create directory, including parents

    :type directory: ``str``
    :param directory: Directory to create
    :raise OSError: Unable to create directory

    """

    try:
        os.makedirs(os.path.expanduser(directory))
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def create_lockfile():
    """Create lockfile handler

    # Test mocks
    >>> atexit.register = lambda *args, **kwargs: True
    >>> glib.get_user_data_dir = lambda: "test/xdg_data_home"

    # Make sure there isn't a stale lock from a previous run
    >>> if os.path.exists("%s/bleeter/lock" % glib.get_user_data_dir()):
    ...     os.unlink("%s/bleeter/lock" % glib.get_user_data_dir())

    >>> create_lockfile()
    >>> os.path.exists("%s/bleeter/lock" % glib.get_user_data_dir())
    True
    >>> try:
    ...     create_lockfile()
    ... except IOError:
    ...     pass
    Another instance is running or `test/xdg_data_home/bleeter/lock' is stale
    >>> os.unlink("%s/bleeter/lock" % glib.get_user_data_dir())

    """
    lock_file = "%s/bleeter/lock" % glib.get_user_data_dir()

    # Create directory for state storage
    mkdir(os.path.dirname(lock_file))
    if os.path.exists(lock_file):
        message = "Another instance is running or `%s' is stale" \
            % lock_file
        usage_note(message)
        raise IOError(message)
    open(lock_file, "w").write(str(os.getpid()))
    atexit.register(os.unlink, lock_file)


def usage_note(message, title=None, level=warn, icon=None):
    """Display a usage notification

    :type message: ``str``
    :param message: Message to display
    :type title: ``str`` or ``None`
    :param title: Title for notification popup
    :type level: ``func``
    :param level: Function to display text message with
    :type icon: ``str``
    :param iconL: Icon to use for notification popup
    """

    message = message.replace("%prog", sys.argv[0])
    if not title:
        title = "%%prog %s" % __version__
    title = title.replace("%prog", sys.argv[0])
    print(level(message))
    if not icon:
        if level == success:
            icon = find_app_icon()
        elif level == warn:
            icon = "stock_dialog-warning"
        elif level == fail:
            icon = "error"
    # pylint: disable-msg=E1101
    note = pynotify.Notification(title, message, icon)
    if level == warn:
        note.set_urgency(pynotify.URGENCY_LOW)
    elif level == fail:
        note.set_urgency(pynotify.URGENCY_CRITICAL)
        note.set_timeout(pynotify.EXPIRES_NEVER)
    # pylint: enable-msg=E1101
    if not note.show():
        raise OSError("Notification failed to display!")
    return errno.EPERM


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
            usage_note("Failed to open link", level=fail)


def find_app_icon(uri=True):
    """Find suitable bleeter application icon

    # Test mocks
    >>> sys.prefix = ""
    >>> sys.path[0] = "non-existent-path"
    >>> glib.get_user_cache_dir = lambda: "test/xdg_cache_home"

    >>> find_app_icon()
    'file://test/xdg_cache_home/bleeter/bleeter.png'
    >>> find_app_icon(False)
    'test/xdg_cache_home/bleeter/bleeter.png'

    # Test with no personal icon
    >>> glib.get_user_cache_dir = lambda: "None"
    >>> find_app_icon()
    Traceback (most recent call last):
        ...
    EnvironmentError: Can't find application icon!

    # Test with local icon
    >>> sys.path[0] = ""
    >>> find_app_icon() #doctest: +ELLIPSIS
    'file://.../bleeter/bleeter.png'

    :type uri: ``bool``
    :param uri: Return a URI for the path
    :rtype: ``str``
    :return: Path to the application icon

    """
    icon_locations = [
        "%s/share/pixmaps/bleeter.png" % sys.prefix,
        "%s/bleeter/bleeter.png" % glib.get_user_cache_dir(),
        "%s/bleeter.png" % os.path.abspath(sys.path[0]),
    ]
    for icon in icon_locations:
        if os.path.exists(icon):
            return "%s%s" % ("file://" if uri else "", icon)
    raise EnvironmentError("Can't find application icon!")


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

        if option.dest == "frequency":
            if value < 60:
                raise optparse.OptionValueError("%s must be at least 60"
                                                % opt_str)
        elif option.dest in "timeout":
            if value < 1:
                raise optparse.OptionValueError("%s must be at least 1"
                                                % opt_str)
        elif option.dest == "count":
            if value < 1:
                raise optparse.OptionValueError("%s must be at least 1"
                                                % opt_str)
            if value > 200:
                raise optparse.OptionValueError("%s must be less than 200"
                                                % opt_str)
        else:
            raise optparse.BadOptionError("%s unknown option to check"
                                          % opt_str)

    config_spec = [
        "timeout = integer(min=1, default=10)",
        "frequency = integer(min=60, default=300)",
        "secure = boolean(default=False)",
        "stealth = list(default=list('ewornj'))",
        "ignore = list(default=list('#nowplaying'))",
        "tray = boolean(default=True)",
        "expand = boolean(default=False)",
        "mobile = boolean(default=False)",
        "map_provider = string(default='google')",
        "count = integer(min=1, max=200, default=20)",
        "stealth_count = integer(min=1, max=200, default=20)",
        "search_count = integer(min=1, max=200, default=20)",
        "list_count = integer(min=1, max=200, default=20)",
        "lists = boolean(default=False)",
        "searches = boolean(default=False)",
        "cache = boolean(default=True)",
    ]
    config = configobj.ConfigObj(config_file, configspec=config_spec)
    results = config.validate(validate.Validator())
    if results is not True:
        for key in filter(lambda k: not results[k], results):
            print(fail("Config value for `%s' is invalid" % key))
        raise SyntaxError("Invalid configuration file")

    parser = optparse.OptionParser(usage="%prog [options...]",
                                   version="%prog v" + __version__,
                                   description=USAGE)

    parser.set_defaults(timeout=config["timeout"],
                        frequency=config["frequency"],
                        secure=config.get("secure"),
                        stealth=config.get("stealth"),
                        ignore=config.get("ignore"),
                        tray=config.get("tray"),
                        expand=config.get("expand"),
                        mobile=config.get("mobile"),
                        map_provider=config.get("map_provider"),
                        count=config.get("count"),
                        stealth_count=config.get("stealth_count"),
                        search_count=config.get("search_count"),
                        list_count=config.get("list_count"),
                        lists=config.get("lists"),
                        searches=config.get("searches"),
                        cache=config.get("cache"))

    parser.add_option("-t", "--timeout", action="callback", type="int",
                      metavar=config["timeout"], callback=check_value,
                      help="Timeout for notification popups in seconds")
    parser.add_option("-f", "--frequency", action="callback", type="int",
                      metavar=config["frequency"], callback=check_value,
                      help="Update frequency in in seconds")

    auth_opts = optparse.OptionGroup(parser, "Authentication options")
    parser.add_option_group(auth_opts)
    auth_opts.add_option("-g", "--get-token", action="store_true",
                         help="Generate a new OAuth token for twitter")
    auth_opts.add_option("--secure", action="store_true",
                         help="Use SSL to connect to twitter")
    auth_opts.add_option("--no-secure", action="store_false",
                         dest="secure",
                         help="Don't use SSL to connect to twitter")

    user_opts = optparse.OptionGroup(parser, "User options")
    parser.add_option_group(user_opts)
    user_opts.add_option("-s", "--stealth", action="store",
                         metavar=",".join(config.get("stealth")),
                         help="Users to watch without " \
                            "following(comma separated)")
    user_opts.add_option("--no-stealth", action="store_false",
                         dest="stealth",
                         help="Don't check stealth users for updates")

    tweet_opts = optparse.OptionGroup(parser, "Tweet options")
    parser.add_option_group(tweet_opts)
    tweet_opts.add_option("-i", "--ignore", action="store",
                          metavar=",".join(config.get("ignore")),
                          help="Keywords to ignore in tweets(comma separated)")
    tweet_opts.add_option("--no-ignore", action="store_false",
                          dest="ignore", help="Don't test for ignore keywords")
    tweet_opts.add_option("-e", "--expand", action="store_true",
                          help="Expand links in tweets")
    tweet_opts.add_option("--no-expand", action="store_false",
                          dest="expand", help="Don't expand links in tweets")
    tweet_opts.add_option("-m", "--mobile", action="store_true",
                          help="Open links in lighter mobile versions")
    tweet_opts.add_option("--no-mobile", action="store_false", dest="mobile",
                          help="Don't open links in lighter mobile versions")
    tweet_opts.add_option("--map-provider", action="store",
                          choices=("bing", "google", "google-nojs"),
                          metavar=config.get("map_provider"),
                          help="Open geo links using specified site")
    tweet_opts.add_option("--count", action="callback", type="int",
                          metavar=config["count"], callback=check_value,
                          help="Maximum number of timeline tweets to fetch")
    tweet_opts.add_option("--stealth-count", action="callback", type="int",
                          metavar=config["stealth_count"],
                          callback=check_value,
                          help="Maximum number of stealth tweets to fetch")
    tweet_opts.add_option("--search-count", action="callback", type="int",
                          metavar=config["search_count"], callback=check_value,
                          help="Maximum number of tweets to fetch for searches")
    tweet_opts.add_option("--list-count", action="callback", type="int",
                          metavar=config["list_count"], callback=check_value,
                          help="Maximum number of tweets to fetch for lists")
    tweet_opts.add_option("--lists", action="store_true",
                          help="Fetch user's lists")
    tweet_opts.add_option("--no-lists", action="store_false",
                          dest="lists", help="Don't fetch user's lists")
    tweet_opts.add_option("--searches", action="store_true",
                          help="Fetch user's saved searches")
    tweet_opts.add_option("--no-searches", action="store_false",
                          dest="searches",
                          help="Don't fetch user's saved searches")

    parser.add_option("--no-cache", action="store_false",
                      dest="cache",
                      help="Don't cache twitter communications")
    parser.add_option("--no-tray", action="store_false",
                      dest="tray", help="Disable systray icon")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", help="Produce verbose output")
    parser.add_option("-q", "--quiet", action="store_false",
                      dest="verbose",
                      help="Output only matches and errors")

    options = parser.parse_args()[0]
    if isinstance(options.stealth, basestring):
        options.stealth = options.stealth.split(",")
    elif options.stealth is False:
        options.stealth = []
    options.stealth = sorted(map(str.lower, options.stealth))
    if isinstance(options.ignore, basestring):
        options.ignore = options.ignore.split(",")
    if options.ignore is False:
        options.ignore = []

    return options


def relative_time(timestamp):
    """Format a relative time

    >>> now = datetime.datetime.utcnow()
    >>> relative_time(now - datetime.timedelta(days=365))
    'last year'
    >>> relative_time(now - datetime.timedelta(days=70))
    'about two months ago'
    >>> relative_time(now - datetime.timedelta(days=30))
    'last month'
    >>> relative_time(now - datetime.timedelta(days=21))
    'about three weeks ago'
    >>> relative_time(now - datetime.timedelta(days=4))
    'about four days ago'
    >>> relative_time(now - datetime.timedelta(days=1))
    'yesterday'
    >>> relative_time(now - datetime.timedelta(hours=5))
    'about five hours ago'
    >>> relative_time(now - datetime.timedelta(hours=1))
    'about an hour ago'
    >>> relative_time(now - datetime.timedelta(minutes=6))
    'about six minutes ago'
    >>> relative_time(now - datetime.timedelta(seconds=12))
    'about 12 seconds ago'

    :type timestamp: ``datetime.datetime``
    :param timestamp: Event to generate relative timestamp against
    :rtype: ``str``
    :return: Human readable date and time offset
    """

    numstr = ". a two three four five six seven eight nine ten".split()

    matches = [
        60 * 60 * 24 * 365,
        60 * 60 * 24 * 28,
        60 * 60 * 24 * 7,
        60 * 60 * 24,
        60 * 60,
        60,
        1,
    ]
    match_names = ["year", "month", "week", "day", "hour", "minute", "second"]

    delta = datetime.datetime.utcnow() - timestamp
    seconds = delta.days * 86400 + delta.seconds
    for scale in matches:
        i = seconds // scale
        if i:
            name = match_names[matches.index(scale)]
            break

    if i == 1 and name in ("year", "month", "week"):
        result = "last %s" % name
    elif i == 1 and name == "day":
        result = "yesterday"
    elif i == 1 and name == "hour":
        result = "about an hour ago"
    else:
        result = "about %s %s%s ago" % (i if i > 10 else numstr[i], name,
                                        "s" if i > 1 else "")
    return result

# Keep a cache for free handling of retweets and such.
URLS = {}
def url_expand(m):
    """Generate links with expanded URLs

    >>> NOTIFY_SERVER_CAPS.extend(["body-markup", "body-hyperlinks"])
    >>> URLS["http://bit.ly/dunMgV"] = "terminal.png"
    >>> format_tweet("See http://bit.ly/dunMgV", True)
    'See <a href="terminal.png">terminal.png</a>'
    >>> NOTIFY_SERVER_CAPS[:] = []

    :type m: ``SRE_Match``
    :param m: Regular expression match object
    :rtype: ``str``
    :return: HTML formatted link for URL
    """
    url = m.group()
    if not url in URLS:
        if urlunshort.is_shortened(url):
            URLS[url] = glib.markup_escape_text(urlunshort.resolve(url))
        else:
            URLS[url] = glib.markup_escape_text(url)
    return '<a href="%s">%s</a>' % (URLS[url], URLS[url])


def format_tweet(text, expand=False, mobile=False):
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
    >>> format_tweet("b123 https://example.com/dunMgV")
    'b123 <a href="https://example.com/dunMgV">https://example.com/dunMgV</a>'
    >>> format_tweet("A list @someone/list")
    'A list @<a href="http://twitter.com/someone/list">someone/list</a>'
    >>> format_tweet("See http://url-hyphen/?and=parm")
    'See <a href="http://url-hyphen/?and=parm">http://url-hyphen/?and=parm</a>'
    >>> format_tweet("Handle ampersands & win")
    'Handle ampersands &amp; win'
    >>> format_tweet("entity test, & \\" ' < >")
    'entity test, &amp; &quot; &apos; &lt; &gt;'
    >>> NOTIFY_SERVER_CAPS[:] = []

    :type text: ``str``
    :param api: Tweet content
    :type expand: ``bool``
    :param expand: Expand links in tweet text
    :type mobile: ``bool``
    :param mobile: Open links in twitter's mobile site
    :rtype: ``str``
    :return: Tweet content with pretty formatting
    """

    # Sanitize entity escaping for input
    text = glib.markup_escape_text(saxutils.unescape(text))

    # re is smart enough to use pre-cached versions
    url_match = re.compile(r'(https?://[\w\.?=\+/_-]+)')
    user_match = re.compile(r'@(\w+(/\w+)?)')
    hashtag_match = re.compile(r'(#\w+)')

    if mobile:
        base = "http://mobile.twitter.com"
    else:
        base = "http://twitter.com"

    if "body-markup" in NOTIFY_SERVER_CAPS:
        if "body-hyperlinks" in NOTIFY_SERVER_CAPS:
            if expand:
                text = url_match.sub(url_expand, text)
            else:
                text = url_match.sub(r'<a href="\1">\1</a>', text)
            text = user_match.sub(r'@<a href="%s/\1">\1</a>' % base,
                                  text)
            text = hashtag_match.sub(r'<a href="%s/search?q=\1">\1</a>' % base,
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
    md5 = hashlib.md5(user.profile_image_url)  # pylint: disable-msg=E1101
    filename = "%s/%s" % (cache_dir, md5.hexdigest())
    if not os.path.exists(filename):
        try:
            # twitter results can be Unicode strings, urlretrieve won't work
            # with them.
            urllib.urlretrieve(user.profile_image_url.encode("utf-8"),
                               filename)
        except IOError:
            # Fallback to application icon
            if not os.path.exists("%s/bleeter.png" % cache_dir):
                shutil.copy(find_app_icon(uri=False), cache_dir)
            filename = "%s/bleeter.png" % cache_dir
        icon = gtk.gdk.pixbuf_new_from_file(filename)
        if not (icon.get_width(), icon.get_height()) == (48, 48):
            icon = icon.scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
            icon.save(filename, "png")

    return "file://%s" % filename


def open_tweet(tweet, mobile=False, map_provider="google"):
    """Create tweet opening function

    :type tweet: ``tweepy.models.Status``
    :param tweet: Twitter status message to open
    :type mobile: ``bool``
    :param mobile: Open links in lighter mobile versions
    :type map_provider: ``str``
    :param map_provider: Map provider to open geo links in, if ``mobile`` is
        ``False``
    :rtype: ``FunctionType``
    :return: Wrapper to open tweet in browser
    """

    if mobile:
        twitter_base = "http://mobile.twitter.com"
        map_url = "http://maps.google.com/maps/api/staticmap?zoom=14" \
            "&markers=%(latlon)s&size=500x300&sensor=false"
    else:
        twitter_base = "http://twitter.com"
        if map_provider == "bing":
            map_url = "http://bing.com/maps/default.aspx?where1=%(latlon)s"
        elif map_provider == "google":
            map_url = "http://maps.google.com/maps?q=%(name)s@%(latlon)s" \
                "&sll=%(latlon)s&z=16"
        elif map_provider == "google-nojs":
            map_url = "http://maps.google.com/m?q=@(latlon)s&oi=nojs"


    def show(notification, action):  # pylint: disable-msg=W0613
        """Open tweet in browser

        :type notification: ``pynotify.Notification``
        :param notification: Calling notification instance
        :type action: ``str``
        :param action: Calling action name
        """

        if action == "find":
            latlon = ",".join(map(str, tweet.geo['coordinates']))

            url = map_url % {"name": tweet.user.screen_name, "latlon": latlon}
        else:
            if tweet.from_type == "search":
                name = tweet.from_user
            else:
                name = tweet.user.screen_name
            url = "%s/%s/status/%s" % (twitter_base, name, tweet.id)
        open_browser(url)
    return show


def skip_check(ignore):
    """Create tweet skip testing wrapper function

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
    >>> filt = skip_check([])
    >>> tweet.text = "This is a test #nowplaying"
    >>> filt(tweet)
    True

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


def update(api, ftype, tweets, state, count, ignore):
    """Fetch new tweets and queue them for display

    For stealth, list and search fetches we only fetch a single user, list or
    search on each run, fetching the full timeline for each element on each run
    is a waste of resources

    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type ftype: ``str``
    :param ftype: Type of update to perform
    :type tweets: ``Tweets``
    :param tweets: Tweets awaiting display
    :type state: ``State``
    :param state: Application state
    :type count: ``int``
    :param count: Number of new tweets to fetch
    :type ignore: ``list`` of ``str``
    :param ignore: List of words to trigger tweet skipping
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue
    """

    kwargs = {"count": count}

    if ftype == "user":
        fetch_ref = "self-status"
        methods = [("home_timeline", []), ("mentions", [])]
    elif ftype == "direct":
        fetch_ref = "self-direct"
        methods = [("direct_messages", [])]
    elif ftype == "stealth":
        user = state.get_user()
        fetch_ref = user
        methods = [("user_timeline", [user, ])]
    elif ftype == "list":
        list_ = state.get_list()
        fetch_ref = "list-%s" % list_.name
        methods = [("list_timeline", [api.me().screen_name, list_.slug])]
    elif ftype == "search":
        search = state.get_search()
        fetch_ref = "search-%s" % search.name
        # API is stupidly incompatible for searches
        kwargs["rpp"] = count
        methods = [("search", [search.query, ])]
    else:
        raise ValueError("Unknown fetch type `%s'" % ftype)
    kwargs["since_id"] = state.fetched[fetch_ref]

    try:
        new_tweets = []
        for method, args in methods:
            new_tweets.extend(getattr(api, method)(*args, **kwargs))
    except tweepy.TweepError:
        if ftype == "user":
            msg = "Fetching user data failed"
            title = None
        elif ftype == "direct":
            msg = "Fetching direct messages failed"
            title = None
        elif ftype == "stealth":
            msg = "Data for `%s' not available" % user
            title = "Fetching user data failed"
        elif ftype == "list":
            msg = "Data for `%s' list not available" % list_.name
            title = "Fetching list data failed"
        elif ftype == "search":
            msg = "Data for `%s' search not available" % search.name
            title = "Fetching search data failed"
        usage_note(msg, title, fail)
        # Still return True, so we re-enter the loop
        return True

    if new_tweets:
        state.fetched[fetch_ref] = new_tweets[0].id

        # Add identifier for display() use, and state storage.
        for tweet in new_tweets:
            tweet.from_type = ftype
            if ftype == "list":
                tweet.from_arg = list_.name
            elif ftype == "search":
                tweet.from_arg = search.name

        tweets.add(filter(skip_check(ignore), new_tweets))

    return True


NOTIFICATIONS = {}
def display(api, tweets, state, timeout, expand, mobile, map_provider):
    """Display notifications for new tweets

    :type api: ``tweepy.api.API``
    :param api: Authenticated ``tweepy.api.API`` object
    :type tweets: ``Tweets``
    :param tweets: Tweets awaiting display
    :type state: ``State``
    :param seen: Application state
    :type timeout: ``tweepy.api.API``
    :param timeout: Timeout for notifications in seconds
    :type expand: ``bool``
    :param expand: Whether to expand links in tweet text
    :type mobile: ``bool``
    :param mobile: Links open in lighter mobile versions
    :type map_provider: ``str``
    :param map_provider: Map provider to open geo links in, if ``mobile`` is
        ``False`
    :rtype: ``True``
    :return: Timers must return a ``True`` value for timer to continue

    """

    try:
        tweet = tweets.popitem()
    except KeyError:
        # No tweets awaiting display
        return True

    if tweet.from_type == "direct":
        title = "From %s %s" % (tweet.sender.name,
                                relative_time(tweet.created_at))
        icon = get_user_icon(tweet.sender)
    elif tweet.from_type == "search":
        title = "From %s %s" % (tweet.from_user,
                                relative_time(tweet.created_at))
        icon = get_user_icon(tweet)
    else:
        # Don't re-display already seen tweets
        if tweet.id <= state.displayed[tweet.user.screen_name.lower()]:
            return True
        title = "From %s %s" % (tweet.user.name,
                                relative_time(tweet.created_at))
        icon = get_user_icon(tweet.user)

    if tweet.from_type == "list":
        title += " on %s list" % tweet.from_arg
    elif tweet.from_type == "direct":
        title += " in direct message"
    elif tweet.from_type == "search":
        title += " in %s search" % tweet.from_arg

    # pylint: disable-msg=E1101
    note = pynotify.Notification(title,
                                 format_tweet(tweet.text, expand, mobile),
                                 icon)
    # pylint: enable-msg=E1101
    if not tweet.from_type == "direct":
        if "actions" in NOTIFY_SERVER_CAPS:
            note.add_action("default", " ", open_tweet(tweet, mobile))
            if tweet.from_type == "search" or not tweet.user.protected:
                note.add_action("mail-forward", "retweet",
                                lambda n, a: api.retweet(tweet.id))
            # In case this has been seen in another client
            if tweet.from_type == "search" or not tweet.favorited:
                note.add_action("bookmark", "Fave",
                                lambda n, a: api.create_favorite(tweet.id))
            if tweet.geo:
                note.add_action("find", "Geo", open_tweet(tweet, mobile,
                                                          map_provider))
            # Keep a reference for handling the action.
            NOTIFICATIONS[hash(note)] = note
            note.connect_object("closed", NOTIFICATIONS.pop, hash(note))
    note.set_timeout(timeout * 1000)
    note.set_category("im.received")
    # pylint: disable-msg=E1101
    # For lists: If we cared about these users they'd be followed, not listed
    # For searches: These are always low priority
    if tweet.from_type in ("list", "search"):
        note.set_urgency(pynotify.URGENCY_LOW)
    if api.me().screen_name.lower() in tweet.text.lower():
        note.set_urgency(pynotify.URGENCY_CRITICAL)
    if tweet.text.lower().startswith(("@%s" % api.me().screen_name.lower(),
                                      ".@%s" % api.me().screen_name.lower())):
        note.set_timeout(pynotify.EXPIRES_NEVER)
    if tweet.from_type == "direct":
        note.set_urgency(pynotify.URGENCY_CRITICAL)
        note.set_timeout(pynotify.EXPIRES_NEVER)
    # pylint: enable-msg=E1101
    if not note.show():
        # Fail hard at this point, recovery has little value.
        raise OSError("Notification failed to display!")
    if not tweet.from_type in ("direct", "search"):
        state.displayed[tweet.user.screen_name.lower()] = tweet.id
    if tweet.from_type == "user":
        state.displayed["self-status"] = tweet.id
    elif tweet.from_type == "direct":
        state.displayed["self-direct"] = tweet.id
    elif tweet.from_type == "list":
        state.displayed["list-%s" % tweet.from_arg] = tweet.id
    elif tweet.from_type == "search":
        state.displayed["search-%s" % tweet.from_arg] = tweet.id
    return True


def tooltip(icon, tweets):
    """Update statusicon tooltip

    :type icon: ``gtk.StatusIcon``
    :param icon: Status icon to update
    :type tweets: ``Tweets``
    :param tweets: Tweets pending display
    """

    n = len(tweets)

    icon.set_visible(n)
    icon.set_tooltip("%i tweets awaiting display" % n)
    return True


def get_token(auth, fetch, token_file):
    """Fetch a new OAuth token

    :type auth: ``OAuthHandler``
    :param auth: OAuth handler for bleeter
    :type fetch: ``bool``
    :param fetch: Fetch a new token, even if one exists
    :type token_file: ``str``
    :param token_file: Filename to store token data in
    """

    if os.path.exists(token_file) and not fetch:
        return json.load(open(token_file))

    try:
        open_browser(auth.get_authorization_url())
    except tweepy.TweepError:
        usage_note("Talking to twitter failed. "
                   "Is twitter or your network down?",
                   "Network error", fail)
        raise
    usage_note("Authentication request opened in default browser",
               level=success)
    time.sleep(3)

    dialog = gtk.Dialog("bleeter authorisation", None, 0,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

    hbox = gtk.HBox(False, 8)
    hbox.set_border_width(8)
    dialog.vbox.pack_start(hbox, False, False, 0)  # pylint: disable-msg=E1101

    icon = gtk.image_new_from_file(find_app_icon(uri=False))
    hbox.pack_start(icon, False, False, 0)

    table = gtk.Table(2, 1)
    table.set_row_spacings(4)
    table.set_col_spacings(4)
    hbox.pack_start(table, True, True, 0)

    label = gtk.Label("Twitter OAuth pin")
    table.attach(label, 0, 1, 0, 1)
    oauth_entry = gtk.Entry()
    table.attach(oauth_entry, 1, 2, 0, 1)
    label.set_mnemonic_widget(oauth_entry)

    dialog.show_all()
    response = dialog.run()
    verifier = oauth_entry.get_text().strip()
    dialog.destroy()

    if response == gtk.RESPONSE_OK:
        for i in range(3):  # pylint: disable-msg=W0612
            try:
                token = auth.get_access_token(verifier)
                break
            except tweepy.TweepError:
                pass
        else:
            usage_note("Fetching token failed")
            raise tweepy.TweepError("Fetching token failed")

    mkdir(os.path.dirname(token_file))
    json.dump([token.key, token.secret], open(token_file, "w"), indent=4)

    return token.key, token.secret


def main(argv):
    """Main handler

    :type argv: ``list``
    :param argv: Command line parameters
    :rtype: ``int``
    :return: Shell return value
    """

    # Must be ahead of setup, for non-X environments to run --help|--version
    config_file = "%s/bleeter/config.ini" % glib.get_user_config_dir()
    options = process_command_line(config_file)

    # pylint: disable-msg=E1101
    if not pynotify.init(argv[0]):
        print(fail("Unable to initialise pynotify!"))
        return errno.EIO
    NOTIFY_SERVER_CAPS.extend(pynotify.get_server_caps())
    # pylint: enable-msg=E1101

    try:
        create_lockfile()
    except IOError:
        return errno.EIO

    token_file = "%s/bleeter/oauth_token" % glib.get_user_data_dir()

    auth = tweepy.OAuthHandler(OAUTH_KEY, OAUTH_SECRET)
    try:
        token = get_token(auth, options.get_token, token_file)
    except tweepy.TweepError:
        return errno.EPERM
    if not token:
        return errno.EPERM

    if options.cache:
        cachedir = "%s/bleeter/http_cache" % glib.get_user_cache_dir()
        mkdir(cachedir)
        cache = tweepy.FileCache(cachedir)
    else:
        cache = None

    auth.set_access_token(*token)  # pylint: disable-msg=W0142
    api = tweepy.API(auth, cache=cache, secure=options.secure)

    if options.verbose or not options.tray:
        # Show a "hello" message, as it can take some time the first real
        # notification
        usage_note("Started", level=success)

    if not urlunshort and options.expand:
        usage_note("Link expansion support requires the urlunshort module")
        options.expand = False

    tweets = Tweets()

    loop = glib.MainLoop()
    if options.tray:
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
        usage_note("Talking to twitter failed. "
                   "Is twitter or your network down?",
                   "Network error", fail)
        return errno.EIO
    # Make calls to api.me() just return the response directly.
    api.me = lambda: me

    lists = []
    if options.lists:
        try:
            # Sort lists based on their name, they're returned sorted on ID
            lists = sorted(api.lists()[0], key=lambda l: l.name.lower())
        except IndexError:
            pass
    searches = []
    if options.searches:
        searches = sorted(api.saved_searches(), key=lambda s: s.name.lower())

    state = State(options.stealth, lists, searches)

    update(api, "user", tweets, state, options.count, options.ignore)

    glib.timeout_add_seconds(options.frequency, update, api, "user", tweets,
                             state, options.count, options.ignore)
    glib.timeout_add_seconds(options.frequency * 10, update, api, "direct",
                             tweets, state, options.count, options.ignore)
    if options.stealth:
        glib.timeout_add_seconds(options.frequency / len(options.stealth) * 10,
                                 update, api, "stealth", tweets, state,
                                 options.stealth_count, options.ignore)

    if lists:
        glib.timeout_add_seconds(options.frequency / len(lists) * 10,
                                 update, api, "list", tweets, state,
                                 options.list_count, options.ignore)

    if searches:
        glib.timeout_add_seconds(options.frequency / len(searches) * 10,
                                 update, api, "search", tweets, state,
                                 options.search_count, options.ignore)

    glib.timeout_add_seconds(options.timeout + 1, display, api, tweets, state,
                             options.timeout, options.expand, options.mobile,
                             options.map_provider)
    if options.tray:
        glib.timeout_add_seconds(options.timeout // 2, tooltip, icon, tweets)

    glib.timeout_add_seconds(options.frequency * 2, state.save_state)
    loop.run()

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[:]))
    except KeyboardInterrupt:
        pass
