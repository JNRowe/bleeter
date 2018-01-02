:Author: James Rowe <jnrowe@gmail.com>
:Date: 2010-04-09
:Copyright: GPL v3
:Manual section: 1
:Manual group: Instant Messaging

bleeter
=======

A nasty little twitter viewer
-----------------------------

SYNOPSIS
--------

    bleeter [option]...

DESCRIPTION
-----------

Fetches your twitter friends timeline and displays notification popups for new
tweets.  If your system’s notification daemon supports adding actions to the
popups then you’ll be able to make a number of choices by clicking the buttons
on the popup.

OPTIONS
-------

.. program:: bleeter

.. option:: --version

    Show program’s version number and exit

.. option:: -h, --help

    Show this help message and exit

.. option:: -t, --timeout <n>

    Timeout for notification popups in seconds

.. option:: -f, --frequency <n>
    Update frequency in in seconds

.. option:: -g, --get-token

    Generate a new OAuth token for twitter

.. option:: --secure

    Use SSL to connect to twitter

.. option:: --no-secure

    Don’t use SSL to connect to twitter

.. option:: -s, --stealth <user>

    Users to watch without following(comma separated)

.. option:: --no-stealth

    Don’t check stealth users for updates

.. option:: -i, --ignore <word>

    Keywords to ignore in tweets(comma separated)

.. option:: --no-ignore

    Don’t test for ignore keywords

.. option:: --no-tray

    Disable the system tray icon

.. option:: -e, --expand

    Expand links in tweets

.. option:: --no-expand

    Don’t expand links in tweets

.. option:: -m, --mobile

    Open links in lighter mobile versions

.. option:: --no-mobile

    Don’t open links in lighter mobile versions

.. option:: --map-provider <site>

    Open geo links using specified site

.. option:: --count <n>

    Maximum number of timeline tweets to fetch(max 200)

.. option:: --stealth-count <n>

    Maximum number of stealth tweets to fetch

.. option:: --search-count <n>

    Maximum number of tweets to fetch for searches

.. option:: --list-count <n>

    Maximum number of tweets to fetch for lists

.. option:: --lists

    Fetch user’s lists

.. option:: --no-lists

    Don’t fetch user’s lists

.. option:: --searches / --no-searches

    Fetch user’s saved searches

.. option:: --cache / --no-cache

    Don’t cache twitter communications

.. option:: -v, --verbose

    Produce verbose output

.. option:: -q, --quiet

    Output only results and errors

CONFIGURATION FILE
------------------

The configuration file, ``${XDG_CONFIG_HOME:-~/.config}/bleeter/config.ini``, is
a simple **INI** format file for storing the command line options.  For
example::

    frequency = 600
    timeout = 10
    stealth = unfolloweduser

With the above configuration file twitter will be checked every ten minutes for
updates, new tweets will be shown for 10 seconds and **unfolloweduser** will be
watched for updates.

BUGS
----

None known.

AUTHOR
------

Written by `James Rowe <mailto:jnrowe@gmail.com>`__

RESOURCES
---------

Home page: https://github.com/JNRowe/bleeter/
Full documentation: http://bleeter.readthedocs.io/
Issue tracker: https://github.com/JNRowe/rdial/issues/

COPYING
-------

Copyright © 2010-2012  James Rowe.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.
