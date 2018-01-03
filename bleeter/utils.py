#
"""utils - Utilities for bleeter."""
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

import atexit
import datetime
import errno
import os
import sys
import webbrowser

from contextlib import contextmanager
from functools import wraps

try:
    from sh import xdg_open
except ImportError:
    xdg_open = None

import blessings
import pynotify

from gi.repository import GLib

try:
    import setproctitle  # pylint: disable-msg=F0401
except ImportError:  # pragma: no cover
    setproctitle = None  # pylint: disable-msg=C0103

try:
    import urlunshort  # pylint: disable-msg=F0401
except ImportError:  # pragma: no cover
    urlunshort = None  # pylint: disable-msg=C0103

from . import _version


T = blessings.Terminal()


# Set up informational message functions
def _colourise(text, colour):
    """Colour text, if possible.

    Args:
        text (str): Text to colourise
        colour (str): Colour to display text in

    Returns:
        str: Colourised text, if possible
    """
    return getattr(T, colour.replace(' ', '_'))(text)


def success(text):
    return _colourise(text, 'bright green')


def fail(text):
    return _colourise(text, 'bright red')


def warn(text):
    return _colourise(text, 'bright yellow')


def mkdir(directory):
    """Create directory, including parents.

    Args:
        directory (str): Directory to create

    Raises:
        OSError: Unable to create directory
    """

    try:
        os.makedirs(os.path.expanduser(directory))
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def create_lockfile():
    """Create lockfile handler.

    # Test mocks
    >>> from mock import Mock
    >>> atexit.register = Mock()
    >>> GLib.get_user_data_dir = Mock(return_value="test/xdg_data_home")

    # Make sure there isn’t a stale lock from a previous run
    >>> if os.path.exists("%s/bleeter/lock" % GLib.get_user_data_dir()):
    ...     os.unlink("%s/bleeter/lock" % GLib.get_user_data_dir())

    >>> create_lockfile()
    >>> os.path.exists("%s/bleeter/lock" % GLib.get_user_data_dir())
    True
    >>> try:
    ...     create_lockfile()
    ... except IOError:
    ...     pass
    Another instance is running or `test/xdg_data_home/bleeter/lock' is stale
    >>> os.unlink("%s/bleeter/lock" % GLib.get_user_data_dir())
    """
    lock_file = "%s/bleeter/lock" % GLib.get_user_data_dir()

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
    """Display a usage notification.

    Args:
        message (str): Message to display
        title (str): Title for notification popup
        level (func): Function to display text message with
        icon (str): Icon to use for notification popup
    """

    message = message.replace("%prog", sys.argv[0])
    if not title:
        title = "%%prog %s" % _version.dotted
    title = title.replace("%prog", os.path.basename(sys.argv[0]))
    print(level(message))
    if "icon-static" in pynotify.get_server_caps():
        if not icon:
            if level == success:
                icon = find_app_icon()
            elif level == warn:
                icon = "stock_dialog-warning"
            elif level == fail:
                icon = "error"
    else:
        icon = None
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
    """Open URL in user’s browser.

    Args:
        uri (str): URL to open
    """

    if xdg_open:
        xdg_open(url)
    else:
        try:
            webbrowser.open(url, new=2)
        except webbrowser.Error:
            usage_note("Failed to open link", level=fail)


def find_app_icon(uri=True):
    """Find suitable bleeter application icon.

    # Test mocks
    >>> from mock import Mock
    >>> GLib.get_user_cache_dir = Mock(return_value="test/xdg_cache_home")

    >>> sys.prefix = ""
    >>> sys.path.insert(0, "non-existent-path")

    >>> find_app_icon()
    'file://test/xdg_cache_home/bleeter/bleeter.png'
    >>> find_app_icon(False)
    'test/xdg_cache_home/bleeter/bleeter.png'

    # Test with no personal icon
    >>> GLib.get_user_cache_dir = Mock(return_value="None")
    >>> find_app_icon()
    Traceback (most recent call last):
        ...
    EnvironmentError: Can’t find application icon!

    # Test with local icon
    >>> sys.path.insert(0, "")
    >>> find_app_icon()  #doctest: +ELLIPSIS
    'file://.../bleeter/bleeter.png'

    Args:
        uri (bool): Return a URI for the path

    Returns:
        str: Path to the application icon
    """
    icon_locations = [
        "%s/bleeter.png" % os.path.abspath(sys.path[0]),
        "%s/bleeter/bleeter.png" % GLib.get_user_cache_dir(),
        "%s/share/pixmaps/bleeter.png" % sys.prefix,
    ]
    for icon in icon_locations:
        if os.path.exists(icon):
            return "%s%s" % ("file://" if uri else "", icon)
    raise EnvironmentError("Can’t find application icon!")


def relative_time(timestamp):
    """Format a relative time.

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

    Args:
        timestamp (datetime.datetime): Event to generate relative timestamp
            against

    Returns:
        str: Human readable date and time offset
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


def url_expand(match):
    """Generate links with expanded URLs.

    # Test mocks
    >>> URLS["http://bit.ly/dunMgV"] = "terminal.png"
    >>> from mock import Mock
    >>> match = Mock()
    >>> match.group = Mock(return_value=URLS.keys()[0])

    >>> url_expand(match)
    '<a href="terminal.png">terminal.png</a>'

    Args:
        match (SRE_Match): Regular expression match object

    Returns:
        str: HTML formatted link for URL
    """
    url = match.group()
    if url not in URLS:
        if urlunshort.is_shortened(url):
            URLS[url] = GLib.markup_escape_text(urlunshort.resolve(url))
        else:
            URLS[url] = GLib.markup_escape_text(url)
    return '<a href="%s">%s</a>' % (URLS[url], URLS[url])


@contextmanager
def wrap_proctitle(string):
    """Set process title for a given context.

    Args:
        string (str): Context to display in process title
    """
    if setproctitle:
        oldtitle = setproctitle.getproctitle()
        setproctitle.setproctitle("%s [%s]" % (sys.argv[0], string))
    yield
    if setproctitle:
        setproctitle.setproctitle(oldtitle)


def proctitle_decorator(f):
    """Decorator to apply ``wrap_proctitle``.

    Args:
        f (func): Function to wrap

    Returns:
        func: Function wrapped in ``wrap_proctitle`` context manager
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        with wrap_proctitle(f.__name__):
            retval = f(*args, **kwargs)
        return retval
    return wrapper
