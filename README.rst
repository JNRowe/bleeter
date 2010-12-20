bleeter - Nasty little twitter client
=====================================

Introduction
------------

``bleeter`` is a nasty little client for twitter_, currently very much in
a *Works For Me* state.  It isn't intended to be used by others, but perhaps
others will find it useful.

All it does is fetch your friends timeline and display notification popups for
new tweets.  If your system's notification daemon supports adding actions [#]_
to the popups then you'll be able to make a number of choices by clicking the
buttons on the popup.

.. [#] Most common notification daemons support actions, including
       xfce4-notifyd_ and Galago's notification-daemon_.

Requirements
------------

``bleeter`` requires Python_ v2.6 or above. ``bleeter``'s mandatory dependencies
outside of the standard library are the configobj_, notify-python_, pygtk_ and
tweepy_ packages.

If you wish to use the URL expansion option for shortened links, you will need
urlunshort_.

If you would like coloured terminal output for debugging information, then you
will need termcolor_.

No significant effort has been put in to making ``bleeter`` work with Python 3,
as few of the dependencies are ported yet.

Configuration
-------------

The first time you run ``bleeter`` it will open an authentication link in your
default web browser and prompt you for the twitter provided PIN.  Should you
wish, or need to generate a new authentication token, you can use the
``--get-token`` option.

It is possible to include tweets from users you are not directly following by
adding them to the configuration file, which should be placed in
``${XDG_CONFIG_HOME:-~/.config}/bleeter/config.ini``.  Its format should be::

    stealth = NotThatInteresting,Boring

Where the ``stealth`` value should be a comma separated list of twitter
usernames or numeric identifiers.  This feature can be used to keep track of
users for a short time without having to follow and then unfollow, for example
when you're at a conference and want to follow the conference news items.

There is an ``ignore`` option that allows you to specify a list of keywords you
wish to use as ignore filters for tweets you receive.  Keywords can be normal
words, ``@user`` usernames, ``#tag`` hashtags or any other word type.  By
default, tweets containing ``#nowplaying`` are ignored.

If you notification daemon supports it you can click on the popup to open the
tweet in your browser of choice.  The browser is opened using ``xdg-open`` from
xdg-utils_.  It should use your default browser under KDE_ or gnome_, or
whatever you've configured in the ``BROWSER`` environment variable elsewhere.

Contributors
------------

I'd like to thank the following people who have contributed to ``bleeter``.

Bug reports
'''''''''''

* Leal Hétu
* Leon Bird
* Matt Leighy
* Rachel Holmes

Ideas
'''''

* Greg Lovell
* Paul Murray

If I've forgotten to include your name I wholeheartedly apologise.  Just drop me
an email_ and I'll update the list!

Hacking
-------

Patches are most welcome, but I'd appreciate it if you could follow the
guidelines below to make it easier to integrate your changes.  These are
guidelines however, and as such can be broken if the need arises or you just
want to convince me that your style is better.

  * `PEP 8`_, the style guide, should be followed where possible.
  * While support for Python versions prior to v2.6 may be added in the future
    if such a need were to arise, you are encouraged to use v2.6 features now.
  * All new classes, methods and functions should be accompanied by new
    ``doctest`` examples and reStructuredText_ formatted descriptions.
  * Tests *must not* span network boundaries, use of a mocking framework is
    acceptable.
  * ``doctest`` tests in modules are only for unit testing in general, and
    should not rely on any modules that aren't in Python's standard library.
  * Functional tests should be in the ``doc`` directory in reStructuredText_
    formatted files, with actual tests in ``doctest`` blocks.  Functional tests
    can depend on external modules, but those modules must be Open Source.

New examples for the ``doc`` directory are as appreciated as code changes.

Bugs
----

If you find any problems, bugs or just have a question about this package either
file an issue_ or drop me a mail_.

If you've found a problem please attempt to include a minimal testcase so I can
reproduce the problem, or even better a patch!

.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/bleeter/issues
.. _twitter: http://twitter.com/
.. _Python: http://www.python.org/
.. _tweepy: http://pypi.python.org/pypi/tweepy/
.. _notify-python: http://www.galago-project.org/
.. _configobj: http://www.voidspace.org.uk/python/configobj.html
.. _xdg-utils: http://portland.freedesktop.org/wiki
.. _KDE: http://www.kde.org/
.. _gnome: http://www.gnome.org/
.. _xfce4-notifyd: http://spuriousinterrupt.org/projects/xfce4-notifyd
.. _notification-daemon: http://www.galago-project.org/
.. _pygtk: http://www.pygtk.org/
.. _urlunshort: http://bitbucket.org/runeh/urlunshort
.. _termcolor: http://pypi.python.org/pypi/termcolor/
.. _email: jnrowe@gmail.com

..
    :vim: set ft=rst ts=4 sw=4 et:

