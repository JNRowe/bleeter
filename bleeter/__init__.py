#
"""bleeter - Nasty little twitter client.

A simple little twitter client that display notifications for new tweets and
nothing more.
"""
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

from . import _version

__version__ = _version.dotted
__date__ = _version.date
__author__ = 'James Rowe <jnrowe@gmail.com>'
__copyright__ = 'Copyright (C) 2010-2012  James Rowe <jnrowe@gmail.com>'

import atexit
import copy
import collections
import errno
import hashlib
import optparse
import os
import re
import shutil
import sys
import time
import urllib

from contextlib import suppress
from xml.sax import saxutils

import json

import configobj
import gi
import tweepy
import validate

gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import GdkPixbuf, GLib, Gtk, Notify

from . import utils


# OAuth design FTL!
OAUTH_KEY = 'WJ3RGn3aMN98b41b3pJQ'
OAUTH_SECRET = 'PU0b7yrBOcdpbSrD1pcQq1kfA9ZVmPQoD0fqtg1bQBQ'
USER_AGENT = 'bleeter/{} (https://github.com/JNRowe/bleeter/)'.format(__version__)

# Pull the first paragraph from the docstring
USAGE = __doc__[:__doc__.find('\n\n', 100)].splitlines()[2:]
# Replace script name with optparse's substitution var, and rebuild string
USAGE = '\n'.join(USAGE).replace('bleeter', '%prog')


class State(object):
    """Bleeter state handling."""

    _version = 1

    def __init__(self, users=None, lists=None, searches=None):
        """Initialise a new ``State`` object.

        # Test mocks
        >>> from mock import Mock
        >>> atexit.register = Mock()
        >>> GLib.get_user_data_dir = Mock(return_value='test/xdg_data_home')

        >>> state = State()
        >>> state.fetched['self-status']
        16460438496

        # Test no config
        >>> GLib.get_user_data_dir = Mock(return_value='None')
        >>> state = State()
        >>> state.fetched['self-status']
        1

        Args:
            users (list): Stealth users to watch
            lists (list): Authenticated user’s lists
            searches (list): Authenticated user’s saved searches
        """
        self.state_file = '{}/bleeter/state.db'.format(GLib.get_user_data_dir())

        self.users = users if users else []
        self.lists = lists if lists else []
        self.searches = searches if searches else []

        # Hold previous state, for save handling
        self._data = {'fetched': {}}

        self.displayed = collections.defaultdict(lambda: 1)
        self.fetched = collections.defaultdict(lambda: 1)
        if os.path.exists(self.state_file):
            data = json.load(open(self.state_file))
            # Keep loaded data, this keeps state data we’re not using on this
            # run
            self._data = data
            if data.get('version', 1) == 1:
                self.fetched.update(data['fetched'])
                self.displayed.update(data['fetched'])
                if 'user' in data and data['user'] in self.users:
                    for i in range(self.users.index(data['user'])):
                        self.get_user()
                if 'list' in data and data['list'] in self.lists:
                    for i in range(self.lists.index(data['list'])):
                        self.get_list()
                if 'search' in data and data['search'] in self.searches:
                    for i in range(self.searches.index(data['search'])):
                        self.get_search()
            else:
                raise NotImplementedError('Unsupported state file format')

        atexit.register(self.save_state, force=True)
        # Shutdown can take a long time, especially with lots of lists or
        # stealth follows.
        atexit.register(sys.stderr.write, utils.warn('Shutting down\n'))

    def get_user(self):
        """Return next stealth user to update.

        Returns:
            str: Next stealth user to update

        Raises:
            IndexError: When user list is empty
        """
        user = self.users[0]
        # Rotate users list
        self.users.append(self.users.pop(0))
        return user

    def get_list(self):
        """Return next list to update.

        Returns:
            tweepy.models.List: Next list to update

        Raises:
            IndexError: When user lists are empty
        """
        list_ = self.lists[0]
        # Rotate user’s lists
        self.lists.append(self.lists.pop(0))
        return list_

    def get_search(self):
        """Return next saved search to update.

        Returns:
            tweepy.models.SavedSearch: Next saved search to update

        Raises:
            IndexError: When user’s saved searches are empty
        """
        search = self.searches[0]
        # Rotate user’s lists
        self.searches.append(self.searches.pop(0))
        return search

    def save_state(self, force=False):
        """Seen tweets state saver.

        We store displayed, not fetched, info so we don’t miss pending tweets
        from a previous run

        Args:
            force (bool): Force update, even if data hasn’t changed for mtime
                promotion
        """
        data = copy.deepcopy(self._data)
        data['fetched'].update(self.displayed)
        if self.users:
            data['user'] = self.get_user()
        if self.lists:
            data['list'] = self.get_list().name
        if self.searches:
            data['search'] = self.get_search().name

        # Store state version
        data['version'] = self._version
        if force or not data == self._data:
            state_dump = json.dumps(data, indent=4)
            open(self.state_file, 'w').write(state_dump)

        self._data = data

        # Must return True, so we can use this method in a timer
        return True


class Tweets(dict):
    """Object for holding tweets pending display.

    Using a dictionary subclass affords us a free ID-based duplicate filter
    """
    def popitem(self):
        """Pop tweet with oldest ID.

        Returns:
            tweepy.models.Status: Oldest tweet

        Raises:
            KeyError: Tweets is empty
        """
        if not self:
            raise KeyError('popitem(): object is empty')
        return self.pop(min(self.keys()))

    def add(self, tweets):
        """Add new tweets to the store.

        Args:
            tweets (list): Tweets to add store
        """
        for tweet in tweets:
            self[tweet.id] = tweet


def process_command_line(config_file):
    """Main command line interface.

    Args:
        config_file (str): Location of the configuration file

    Returns:
        (optparse, list): Parsed options and arguments
    """

    def check_value(option, opt_str, value, parser):
        """Check frequency value is within bounds."""

        # pylint: disable-msg=W0613

        if option.dest == 'frequency':
            if value < 60:
                raise optparse.OptionValueError(
                    '{} must be at least 60'.format(opt_str))
        elif option.dest in 'timeout':
            if value < 1:
                raise optparse.OptionValueError(
                    '{} must be at least 1'.format(opt_str))
        elif option.dest == 'count':
            if value < 1:
                raise optparse.OptionValueError(
                    '{} must be at least 1'.format(opt_str))
            if value > 200:
                raise optparse.OptionValueError(
                    '{} must be less than 200'.format(opt_str))
        else:
            raise optparse.BadOptionError(
                '{} unknown option to check'.format(opt_str))

    config_spec = [
        'timeout = integer(min=1, default=10)',
        'frequency = integer(min=60, default=300)',
        'secure = boolean(default=False)',
        "stealth = list(default=list('ewornj'))",
        "ignore = list(default=list('#nowplaying'))",
        'tray = boolean(default=True)',
        'expand = boolean(default=False)',
        'mobile = boolean(default=False)',
        "map_provider = string(default='google')",
        'count = integer(min=1, max=200, default=20)',
        'stealth_count = integer(min=1, max=200, default=20)',
        'search_count = integer(min=1, max=200, default=20)',
        'list_count = integer(min=1, max=200, default=20)',
        'lists = boolean(default=False)',
        'searches = boolean(default=False)',
        'cache = boolean(default=True)',
    ]
    config = configobj.ConfigObj(config_file, configspec=config_spec)
    results = config.validate(validate.Validator())
    if results is not True:
        for key in filter(lambda k: not results[k], results):
            print(utils.fail("Config value for `{}' is invalid".format(key)))
        raise SyntaxError('Invalid configuration file')

    parser = optparse.OptionParser(usage='%prog [options...]',
                                   version='%prog v' + __version__,
                                   description=USAGE)

    parser.set_defaults(timeout=config['timeout'],
                        frequency=config['frequency'],
                        secure=config.get('secure'),
                        stealth=config.get('stealth'),
                        ignore=config.get('ignore'),
                        tray=config.get('tray'),
                        expand=config.get('expand'),
                        mobile=config.get('mobile'),
                        map_provider=config.get('map_provider'),
                        count=config.get('count'),
                        stealth_count=config.get('stealth_count'),
                        search_count=config.get('search_count'),
                        list_count=config.get('list_count'),
                        lists=config.get('lists'),
                        searches=config.get('searches'),
                        cache=config.get('cache'))

    parser.add_option('-t', '--timeout', action='callback', type='int',
                      metavar=config['timeout'], callback=check_value,
                      help='Timeout for notification popups in seconds')
    parser.add_option('-f', '--frequency', action='callback', type='int',
                      metavar=config['frequency'], callback=check_value,
                      help='Update frequency in in seconds')

    auth_opts = optparse.OptionGroup(parser, 'Authentication options')
    parser.add_option_group(auth_opts)
    auth_opts.add_option('-g', '--get-token', action='store_true',
                         help='Generate a new OAuth token for twitter')
    auth_opts.add_option('--secure', action='store_true',
                         help='Use SSL to connect to twitter')
    auth_opts.add_option('--no-secure', action='store_false',
                         dest='secure',
                         help='Don’t use SSL to connect to twitter')

    user_opts = optparse.OptionGroup(parser, 'User options')
    parser.add_option_group(user_opts)
    user_opts.add_option('-s', '--stealth', action='store',
                         metavar=','.join(config.get('stealth')),
                         help='Users to watch without '
                              'following(comma separated)')
    user_opts.add_option('--no-stealth', action='store_false',
                         dest='stealth',
                         help='Don’t check stealth users for updates')

    tweet_opts = optparse.OptionGroup(parser, 'Tweet options')
    parser.add_option_group(tweet_opts)
    tweet_opts.add_option('-i', '--ignore', action='store',
                          metavar=','.join(config.get('ignore')),
                          help='Keywords to ignore in tweets(comma separated)')
    tweet_opts.add_option('--no-ignore', action='store_false',
                          dest='ignore', help='Don’t test for ignore keywords')
    tweet_opts.add_option('-e', '--expand', action='store_true',
                          help='Expand links in tweets')
    tweet_opts.add_option('--no-expand', action='store_false',
                          dest='expand', help='Don’t expand links in tweets')
    tweet_opts.add_option('-m', '--mobile', action='store_true',
                          help='Open links in lighter mobile versions')
    tweet_opts.add_option('--no-mobile', action='store_false', dest='mobile',
                          help='Don’t open links in lighter mobile versions')
    tweet_opts.add_option('--map-provider', action='store',
                          choices=('bing', 'google', 'google-nojs'),
                          metavar=config.get('map_provider'),
                          help='Open geo links using specified site')
    tweet_opts.add_option('--count', action='callback', type='int',
                          metavar=config['count'], callback=check_value,
                          help='Maximum number of timeline tweets to fetch')
    tweet_opts.add_option('--stealth-count', action='callback', type='int',
                          metavar=config['stealth_count'],
                          callback=check_value,
                          help='Maximum number of stealth tweets to fetch')
    tweet_opts.add_option('--search-count', action='callback', type='int',
                          metavar=config['search_count'], callback=check_value,
                          help='Maximum number of tweets to fetch for '
                               'searches')
    tweet_opts.add_option('--list-count', action='callback', type='int',
                          metavar=config['list_count'], callback=check_value,
                          help='Maximum number of tweets to fetch for lists')
    tweet_opts.add_option('--lists', action='store_true',
                          help='Fetch user’s lists')
    tweet_opts.add_option('--no-lists', action='store_false',
                          dest='lists', help='Don’t fetch user’s lists')
    tweet_opts.add_option('--searches', action='store_true',
                          help='Fetch user’s saved searches')
    tweet_opts.add_option('--no-searches', action='store_false',
                          dest='searches',
                          help='Don’t fetch user’s saved searches')

    parser.add_option('--no-cache', action='store_false',
                      dest='cache',
                      help='Don’t cache twitter communications')
    parser.add_option('--no-tray', action='store_false',
                      dest='tray', help='Disable systray icon')
    parser.add_option('-v', '--verbose', action='store_true',
                      dest='verbose', help='Produce verbose output')
    parser.add_option('-q', '--quiet', action='store_false',
                      dest='verbose',
                      help='Output only matches and errors')

    options = parser.parse_args()[0]
    if isinstance(options.stealth, str):
        options.stealth = options.stealth.split(',')
    elif options.stealth is False:
        options.stealth = []
    options.stealth = sorted(map(str.lower, options.stealth))
    if isinstance(options.ignore, str):
        options.ignore = options.ignore.split(',')
    if options.ignore is False:
        options.ignore = []

    return options


def format_tweet(text, expand=False, mobile=False):
    """Format tweet for display.

    >>> from mock import Mock
    >>> Notify.get_server_caps = Mock(return_value=[])
    >>> format_tweet('Populate #sup contacts from #abook')
    'Populate #sup contacts from #abook'
    >>> Notify.get_server_caps = Mock(return_value=['body-markup', ])
    >>> format_tweet('Populate #sup contacts from #abook')
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet('RT @ewornj Populate #sup contacts from #abook')
    '<b>RT</b> @<u>ewornj</u> Populate <i>#sup</i> contacts from <i>#abook</i>'
    >>> format_tweet('@rachcholmes London marathon signup closed yet? ;)')
    '@<u>rachcholmes</u> London marathon signup closed yet? ;)'
    >>> format_tweet('Updated my vim colour scheme see http://bit.ly/dunMgV')
    'Updated my vim colour scheme see <u>http://bit.ly/dunMgV</u>'
    >>> Notify.get_server_caps = Mock(return_value=['body-markup',
    ...                                             'body-hyperlinks'])
    >>> format_tweet('See http://bit.ly/dunMgV')
    'See <a href="http://bit.ly/dunMgV">http://bit.ly/dunMgV</a>'
    >>> format_tweet('b123 https://example.com/dunMgV')
    'b123 <a href="https://example.com/dunMgV">https://example.com/dunMgV</a>'
    >>> format_tweet('A list @someone/list')
    'A list @<a href="http://twitter.com/someone/list">someone/list</a>'
    >>> format_tweet('See http://url-hyphen/?and=parm')
    'See <a href="http://url-hyphen/?and=parm">http://url-hyphen/?and=parm</a>'
    >>> format_tweet('Handle ampersands & win')
    'Handle ampersands &amp; win'
    >>> format_tweet("entity test, & \\" ' < >")
    'entity test, &amp; &quot; &apos; &lt; &gt;'
    >>> Notify.get_server_caps = Mock(return_value=[])

    Args:
        api (str): Tweet content
        expand (bool): Expand links in tweet text
        mobile (bool): Open links in twitter’s mobile site

    Returns:
        str: Tweet content with pretty formatting
    """
    # Sanitize entity escaping for input
    text = GLib.markup_escape_text(saxutils.unescape(text))

    # re is smart enough to use pre-cached versions
    url_match = re.compile(r'(https?://[\w\.?=\+/_-]+)')
    user_match = re.compile(r'@(\w+(/\w+)?)')
    hashtag_match = re.compile(r'(#\w+)')

    if mobile:
        base = 'https://mobile.twitter.com'
    else:
        base = 'https://twitter.com'

    if 'body-markup' in Notify.get_server_caps():
        if 'body-hyperlinks' in Notify.get_server_caps():
            if expand:
                text = url_match.sub(utils.url_expand, text)
            else:
                text = url_match.sub(r'<a href="\1">\1</a>', text)
            text = user_match.sub(r'@<a href="{}/\1">\1</a>'.format(base),
                                  text)
            text = hashtag_match.sub(
                r'<a href="{}/search?q=\1">\1</a>'.format(base),
                text)
        else:
            text = url_match.sub(r'<u>\1</u>', text)
            text = user_match.sub(r'@<u>\1</u>', text)
            text = hashtag_match.sub(r'<i>\1</i>', text)

        if text.startswith('RT '):
            text = '<b>RT</b> ' + text[3:]
    return text


def get_user_icon(user):
    """Get icon location for user.

    Args:
        user (tweepy.models.User): Tweet user reference

    Returns:
        str: Location of the icon file
    """
    if 'icon-static' not in Notify.get_server_caps():
        return None

    cache_dir = '{}/bleeter'.format(GLib.get_user_cache_dir())
    utils.mkdir(cache_dir)
    md5 = hashlib.md5(user.profile_image_url)  # pylint: disable-msg=E1101
    filename = '{}/{}'.format(cache_dir, md5.hexdigest())
    if not os.path.exists(filename):
        try:
            # twitter results can be Unicode strings, urlretrieve won’t work
            # with them.
            urllib.urlretrieve(user.profile_image_url.encode('utf-8'),
                               filename)
        except IOError:
            # Fallback to application icon
            if not os.path.exists('{}/bleeter.png'.format(cache_dir)):
                shutil.copy(utils.find_app_icon(uri=False), cache_dir)
            filename = '{}/bleeter.png'.format(cache_dir)
        icon = GdkPixbuf.Pixbuf.new_from_file(filename)
        if not (icon.get_width(), icon.get_height()) == (48, 48):
            icon = icon.scale_simple(48, 48, GdkPixbuf.InterpType.BILINEAR)
            icon.save(filename, 'png')

    return 'file://{}'.format(filename)


def open_tweet(tweet, mobile=False, map_provider='google'):
    """Create tweet opening function.

    Args:
        tweet (tweepy.models.Status): Twitter status message to open
        mobile (bool): Open links in lighter mobile versions
        map_provider (str): Map provider to open geo links in, if ``mobile``
            is ``False``

    Returns:
        func: Wrapper to open tweet in browser
    """
    if mobile:
        twitter_base = 'https://mobile.twitter.com'
        map_url = 'http://maps.google.com/maps/api/staticmap?zoom=14' \
            '&markers={0[latlon]}&size=500x300&sensor=false'
    else:
        twitter_base = 'https://twitter.com'
        if map_provider == 'bing':
            map_url = 'http://bing.com/maps/default.aspx?where1={0[latlon]}'
        elif map_provider == 'google':
            map_url = 'http://maps.google.com/maps?q={0[name]}@{0[latlon]}' \
                '&sll={0[latlon]}&z=16'
        elif map_provider == 'google-nojs':
            map_url = 'http://maps.google.com/m?q={0[latlon]}s&oi=nojs'

    def show(notification, action):  # pylint: disable-msg=W0613
        """Open tweet in browser.

        Args:
            notification (Notify.Notification): Calling notification instance
            action (str): Calling action name
        """
        if action == 'find':
            latlon = ','.join(map(str, tweet.geo['coordinates']))

            url = map_url.format({'name': tweet.user.screen_name,
                                  'latlon': latlon})
        else:
            if tweet.from_type == 'search':
                name = tweet.from_user
            else:
                name = tweet.user.screen_name
            url = '{}/{}/status/{}'.format(twitter_base, name, tweet.id)
        utils.open_browser(url)
    return show


def skip_check(ignore):
    """Create tweet skip testing wrapper function.

    >>> filt = skip_check(['#nowplaying', '@boring'])
    >>> tweet = tweepy.models.Status()
    >>> tweet.text = 'This is a test'
    >>> filt(tweet)
    True
    >>> tweet.text = 'This is a test #nowplaying'
    >>> filt(tweet)
    False
    >>> tweet.text = 'Reply to @boring'
    >>> filt(tweet)
    False
    >>> filt = skip_check([])
    >>> tweet.text = 'This is a test #nowplaying'
    >>> filt(tweet)
    True

    Args:
        ignore (List[str]): List of words to trigger tweet skipping

    Returns:
        func: Wrapper to scan tweets
    """

    def wrapper(tweet):
        """Filter tweets containing user selected words.

        Args:
            tweet (tweepy.models.Status): Twitter status message to scan for
                selected words

        Returns:
            bool: True if tweet is clean
        """
        # Not just \W, because of the special case of # and @ in tweets
        word_match = re.compile('[^a-zA-Z0-9_#@]')

        return not any(map(ignore.__contains__, re.split(word_match,
                                                         tweet.text)))
    return wrapper


@utils.proctitle_decorator
def update(api, ftype, tweets, state, count, ignore):
    """Fetch new tweets and queue them for display.

    For stealth, list and search fetches we only fetch a single user, list or
    search on each run, fetching the full timeline for each element on each run
    is a waste of resources

    Args:
        api (tweepy.api.API): Authenticated ``tweepy.api.API`` object
        ftype (str): Type of update to perform
        tweets (Tweets): Tweets awaiting display
        state (state): Application state
        count (int): Number of new tweets to fetch
        ignore (List[str]): List of words to trigger tweet skipping

    Returns:
        True: Timers must return a ``True`` value for timer to continue
    """
    kwargs = {'count': count}

    if ftype == 'user':
        fetch_ref = 'self-status'
        methods = [('home_timeline', []), ('mentions', [])]
    elif ftype == 'direct':
        fetch_ref = 'self-direct'
        methods = [('direct_messages', [])]
    elif ftype == 'stealth':
        user = state.get_user()
        fetch_ref = user
        methods = [('user_timeline', [user, ])]
    elif ftype == 'list':
        list_ = state.get_list()
        fetch_ref = 'list-{}'.format(list_.name)
        methods = [('list_timeline', [api.me().screen_name, list_.slug])]
    elif ftype == 'search':
        search = state.get_search()
        fetch_ref = 'search-{}'.format(search.name)
        # API is stupidly incompatible for searches
        kwargs['rpp'] = count
        methods = [('search', [search.query, ])]
    else:
        raise ValueError("Unknown fetch type `{}'".format(ftype))
    kwargs['since_id'] = state.fetched[fetch_ref]

    try:
        new_tweets = []
        for method, args in methods:
            new_tweets.extend(getattr(api, method)(*args, **kwargs))
    except tweepy.TweepError:
        if ftype == 'user':
            msg = 'Fetching user data failed'
            title = None
        elif ftype == 'direct':
            msg = 'Fetching direct messages failed'
            title = None
        elif ftype == 'stealth':
            msg = "Data for `{}' not available".format(user)
            title = 'Fetching user data failed'
        elif ftype == 'list':
            msg = "Data for `{}' list not available".format(list_.name)
            title = 'Fetching list data failed'
        elif ftype == 'search':
            msg = "Data for `{}' search not available".format(search.name)
            title = 'Fetching search data failed'
        utils.usage_note(msg, title, utils.fail)
        # Still return True, so we re-enter the loop
        return True

    if new_tweets:
        state.fetched[fetch_ref] = new_tweets[0].id

        # Add identifier for display() use, and state storage.
        for tweet in new_tweets:
            tweet.from_type = ftype
            if ftype == 'list':
                tweet.from_arg = list_.name
            elif ftype == 'search':
                tweet.from_arg = search.name

        tweets.add(filter(skip_check(ignore), new_tweets))

    return True


NOTIFICATIONS = {}


@utils.proctitle_decorator
def display(api, tweets, state, timeout, expand, mobile, map_provider):
    """Display notifications for new tweets.

    Args:
        api (tweepy.api.API): Authenticated ``tweepy.api.API`` object
        tweets (Tweets): Tweets awaiting display
        seen (State): Application state
        timeout (int): Timeout for notifications in seconds
        expand (bool): Whether to expand links in tweet text
        mobile (bool): Links open in lighter mobile versions
        map_provider (str): Map provider to open geo links in, if ``mobile``
            is ``False`

    Returns:
        True: Timers must return a ``True`` value for timer to continue
    """
    try:
        tweet = tweets.popitem()
    except KeyError:
        # No tweets awaiting display
        return True

    if tweet.from_type == 'direct':
        title = 'From {} {}'.format(tweet.sender.name,
                                    utils.relative_time(tweet.created_at))
        icon = get_user_icon(tweet.sender)
    elif tweet.from_type == 'search':
        title = 'From {} {}'.format(tweet.from_user,
                                    utils.relative_time(tweet.created_at))
        icon = get_user_icon(tweet)
    else:
        # Don’t re-display already seen tweets
        if tweet.id <= state.displayed[tweet.user.screen_name.lower()]:
            return True
        title = 'From {} {}'.format(tweet.user.name,
                                    utils.relative_time(tweet.created_at))
        icon = get_user_icon(tweet.user)

    if tweet.from_type == 'list':
        title += ' on {} list'.format(tweet.from_arg)
    elif tweet.from_type == 'direct':
        title += ' in direct message'
    elif tweet.from_type == 'search':
        title += ' in {} search'.format(tweet.from_arg)

    # pylint: disable-msg=E1101
    note = Notify.Notification.new(title,
                                   format_tweet(tweet.text, expand, mobile),
                                   icon)
    # pylint: enable-msg=E1101
    if not tweet.from_type == 'direct':
        if 'actions' in Notify.get_server_caps():
            note.add_action('default', ' ', open_tweet(tweet, mobile))
            if tweet.from_type == 'search' or not tweet.user.protected:
                note.add_action('mail-forward', 'retweet',
                                lambda n, a: api.retweet(tweet.id))
            # In case this has been seen in another client
            if tweet.from_type == 'search' or not tweet.favorited:
                note.add_action('bookmark', 'Fave',
                                lambda n, a: api.create_favorite(tweet.id))
            if tweet.geo:
                note.add_action('find', 'Geo', open_tweet(tweet, mobile,
                                                          map_provider))
            # Keep a reference for handling the action.
            NOTIFICATIONS[hash(note)] = note
            note.connect_object('closed', NOTIFICATIONS.pop, hash(note))
    note.set_timeout(timeout * 1000)
    note.set_category('im.received')
    # pylint: disable-msg=E1101
    # For lists: If we cared about these users they’d be followed, not listed
    # For searches: These are always low priority
    if tweet.from_type in ('list', 'search'):
        note.set_urgency(Notify.Urgency.LOW)
    if api.me().screen_name.lower() in tweet.text.lower():
        note.set_urgency(Notify.Urgency.CRITICAL)
    if tweet.text.lower().startswith(('@{}'.format(api.me().screen_name.lower()),
                                      '.@{}'.format(api.me().screen_name.lower()))):
        note.set_timeout(Notify.EXPIRES_NEVER)
    if tweet.from_type == 'direct':
        note.set_urgency(Notify.Urgency.CRITICAL)
        note.set_timeout(Notify.EXPIRES_NEVER)
    # pylint: enable-msg=E1101
    if not note.show():
        # Fail hard at this point, recovery has little value.
        raise OSError('Notification failed to display!')
    if tweet.from_type not in ('direct', 'search'):
        state.displayed[tweet.user.screen_name.lower()] = tweet.id
    if tweet.from_type == 'user':
        state.displayed['self-status'] = tweet.id
    elif tweet.from_type == 'direct':
        state.displayed['self-direct'] = tweet.id
    elif tweet.from_type == 'list':
        state.displayed['list-{}'.format(tweet.from_arg)] = tweet.id
    elif tweet.from_type == 'search':
        state.displayed['search-{}'.format(tweet.from_arg)] = tweet.id
    return True


def tooltip(icon, tweets):
    """Update statusicon tooltip.

    Args:
        icon (Gtk.StatusIcon): Status icon to update
        tweets (Tweets): Tweets pending display
    """
    count = len(tweets)

    icon.set_visible(count)
    icon.set_tooltip('{} tweets awaiting display'.format(count))
    return True


@utils.proctitle_decorator
def get_token(auth, fetch, token_file):
    """Fetch a new OAuth token.

    Args:
        auth (OAuthHandler): OAuth handler for bleeter
        fetch (bool): Fetch a new token, even if one exists
        token_file (str): Filename to store token data in
    """
    if os.path.exists(token_file) and not fetch:
        return json.load(open(token_file))

    try:
        utils.open_browser(auth.get_authorization_url())
    except tweepy.TweepError:
        utils.usage_note('Talking to twitter failed. '
                         'Is twitter or your network down?',
                         'Network error', utils.fail)
        raise
    utils.usage_note('Authentication request opened in default browser',
                     level=utils.success)
    time.sleep(3)

    dialog = Gtk.Dialog('bleeter authorisation', None, 0,
                        (Gtk.STOCK_OK, Gtk.ResponseType.OK,
                         Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

    hbox = Gtk.HBox(False, 8)
    hbox.set_border_width(8)
    dialog.vbox.pack_start(hbox, False, False, 0)  # pylint: disable-msg=E1101

    icon = Gtk.Image.new_from_file(utils.find_app_icon(uri=False))
    hbox.pack_start(icon, False, False, 0)

    table = Gtk.Table(2, 1)
    table.set_row_spacings(4)
    table.set_col_spacings(4)
    hbox.pack_start(table, True, True, 0)

    label = Gtk.Label('Twitter OAuth pin')
    table.attach(label, 0, 1, 0, 1)
    oauth_entry = Gtk.Entry()
    table.attach(oauth_entry, 1, 2, 0, 1)
    label.set_mnemonic_widget(oauth_entry)

    dialog.show_all()
    response = dialog.run()
    verifier = oauth_entry.get_text().strip()
    dialog.destroy()

    if response == Gtk.ResponseType.OK:
        for _ in range(3):
            with suppress(tweepy.TweepError):
                token = auth.get_access_token(verifier)
                break
        else:
            utils.usage_note('Fetching token failed')
            raise tweepy.TweepError('Fetching token failed')

    utils.mkdir(os.path.dirname(token_file))
    json.dump([token.key, token.secret], open(token_file, 'w'), indent=4)

    return token.key, token.secret


def main(argv=sys.argv[:]):
    """Main handler.

    Args:
        argv (List[str]): Command line parameters

    Returns:
        int: Shell return value
    """
    if utils.setproctitle:
        utils.setproctitle.setproctitle(sys.argv[0])

    # Must be ahead of setup, for non-X environments to run --help|--version
    config_file = '{}/bleeter/config.ini'.format(GLib.get_user_config_dir())
    options = process_command_line(config_file)

    # pylint: disable-msg=E1101
    if not Notify.init(argv[0]):
        print(utils.fail('Unable to initialise Notify.'))
        return errno.EIO
    # pylint: enable-msg=E1101

    try:
        utils.create_lockfile()
    except IOError:
        return errno.EIO

    with utils.wrap_proctitle('authenticating'):
        token_file = '{}/bleeter/oauth_token'.format(GLib.get_user_data_dir())

        auth = tweepy.OAuthHandler(OAUTH_KEY, OAUTH_SECRET)
        try:
            token = get_token(auth, options.get_token, token_file)
        except tweepy.TweepError:
            return errno.EPERM
        if not token:
            return errno.EPERM

    if options.cache:
        cachedir = '{}/bleeter/http_cache'.format(GLib.get_user_cache_dir())
        utils.mkdir(cachedir)
        cache = tweepy.FileCache(cachedir)
    else:
        cache = None

    auth.set_access_token(*token)  # pylint: disable-msg=W0142
    api = tweepy.API(auth, cache=cache, secure=options.secure)

    if options.verbose or not options.tray:
        # Show a "hello" message, as it can take some time the first real
        # notification
        utils.usage_note('Started', level=utils.success)

    if not utils.urlunshort and options.expand:
        utils.usage_note('Link expansion support requires the urlunshort '
                         'module')
        options.expand = False

    tweets = Tweets()

    loop = GLib.MainLoop()
    if options.tray:
        icon = Gtk.StatusIcon.new_from_file(utils.find_app_icon(uri=False))
        icon.set_tooltip('Initial update in progress')
        icon.connect('activate',
                     lambda x: utils.open_browser('https://twitter.com/'))

        # Make sure icon is set up, before entering update()
        ctx = loop.get_context()
        while ctx.pending():
            ctx.iteration()

    try:
        me = api.me()
    except tweepy.TweepError:
        utils.usage_note('Talking to twitter failed. '
                         'Is twitter or your network down?',
                         'Network error', utils.fail)
        return errno.EIO
    # Make calls to api.me() just return the response directly.
    api.me = lambda: me

    lists = []
    if options.lists:
        with suppress(IndexError):
            # Sort lists based on their name, they’re returned sorted on ID
            lists = sorted(api.lists(), key=lambda l: l.name.lower())
    searches = []
    if options.searches:
        searches = sorted(api.saved_searches(), key=lambda s: s.name.lower())

    state = State(options.stealth, lists, searches)

    with utils.wrap_proctitle('Initial update'):
        update(api, 'user', tweets, state, options.count, options.ignore)

    GLib.timeout_add_seconds(options.frequency, update, api, 'user', tweets,
                             state, options.count, options.ignore)
    GLib.timeout_add_seconds(options.frequency * 10, update, api, 'direct',
                             tweets, state, options.count, options.ignore)
    if options.stealth:
        GLib.timeout_add_seconds(options.frequency / len(options.stealth) * 10,
                                 update, api, 'stealth', tweets, state,
                                 options.stealth_count, options.ignore)

    if lists:
        GLib.timeout_add_seconds(options.frequency / len(lists) * 10,
                                 update, api, 'list', tweets, state,
                                 options.list_count, options.ignore)

    if searches:
        GLib.timeout_add_seconds(options.frequency / len(searches) * 10,
                                 update, api, 'search', tweets, state,
                                 options.search_count, options.ignore)

    GLib.timeout_add_seconds(options.timeout + 1, display, api, tweets, state,
                             options.timeout, options.expand, options.mobile,
                             options.map_provider)
    if options.tray:
        GLib.timeout_add_seconds(options.timeout // 2, tooltip, icon, tweets)

    GLib.timeout_add_seconds(options.frequency * 2, state.save_state)
    loop.run()


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        sys.exit(main())
