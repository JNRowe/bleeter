bleeter.py
==========

A nasty little twitter viewer
"""""""""""""""""""""""""""""

:Author: James Rowe <jnrowe@gmail.com>
:Date: 2010-04-09
:Copyright: GPL v3
:Manual section: 1
:Manual group: Instant Messaging

SYNOPSIS
--------

    bleeter.py [option]...

DESCRIPTION
-----------

Fetches your twitter friends timeline and displays notification popups for new
tweets.  If your system's notification daemon supports adding actions to the
popups then you'll be able to make a number of choices by clicking the buttons
on the popup.

OPTIONS
-------

--version
    show program's version number and exit

-h, --help
    show this help message and exit

-t, --timeout **n**
    timeout for notification popups in seconds

-f, --frequency **n**
    update frequency in in seconds

-g, --get-token
    generate a new OAuth token for twitter

--secure
    use SSL to connect to twitter

--no-secure
    don't use SSL to connect to twitter

-s, --stealth **user**
    users to watch without following(comma separated)

--no-stealth
    don't check stealth users for updates

-i, --ignore **word**
    keywords to ignore in tweets(comma separated)

--no-ignore
    don't test for ignore keywords

--no-tray
    disable the system tray icon

-e, --expand
    expand links in tweets

--no-expand
    don't expand links in tweets

-m, --mobile
    open links in lighter mobile versions

--no-mobile
    don't open links in lighter mobile versions

--map-provider **site**
    open geo links using specified site

--count **n**
    maximum number of timeline tweets to fetch(max 200)

--stealth-count **n**

   maximum number of stealth tweets to fetch

--search-count **n**

   maximum number of tweets to fetch for searches

--list-count **n**

   maximum number of tweets to fetch for lists

--lists
    fetch user's lists

--no-lists
    don't fetch user's lists

--searches
    fetch user's saved searches

--no-searches
   don't fetch user's saved searches

--no-cache
    don't cache twitter communications

-v, --verbose
    produce verbose output

-q, --quiet
    output only results and errors

CONFIGURATION FILE
------------------

The configuration file, **${XDG_CONFIG_HOME:-~/.config}/bleeter/config.ini**, is
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

Home page: http://github.com/JNRowe/bleeter

COPYING
-------

Copyright © 2010-2011  James Rowe.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

..
    :vim: set ft=rst ts=4 sw=4 et:

