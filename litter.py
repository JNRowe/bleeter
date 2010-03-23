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
import json
import os
import sys
import time

from xml.sax.saxutils import escape

import pynotify
import twitter

def update(api, seen):
    """Fetch updates and display notifications

    :type api: ``twitter.Api``
    :param api: Authenticated ``twitter.Api`` object
    :type seen: ``list``
    :param seen: Already seen tweets
    """

    for m in reversed(api.GetFriendsTimeline()):
        if m.id in seen:
            continue
        else:
            n = pynotify.Notification("From %s at %s " % (m.user.name, m.created_at),
                                      escape(m.text),
                                      "Twitter-48.png")
            if api._username in m.text:
                n.set_urgency(pynotify.URGENCY_CRITICAL)
            if m.text.startswith("@%s" % api._username):
                n.set_timeout(10)
            if not n.show():
                raise OSError("Notification failed to display!")
            seen.append(m.id)
            time.sleep(4)

def main(argv):
    """main handler

    :type argv: ``list``
    :param argv: Command line parameters
    """

    if not pynotify.init(argv[0]):
        print "Unable to initialise pynotify!"
        return 1

    api = twitter.Api(os.getenv("TWEETUSERNAME"), os.getenv("TWEETPASSWORD"))
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

    while True:
        update(api, seen)
        time.sleep(300)

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))

