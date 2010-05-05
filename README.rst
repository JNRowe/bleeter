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

``bleeter``'s mandatory dependencies outside of the Python_ standard library are
the configobj_, notify-python_, pygobject_ and tweepy_ packages.  If you're
still using Python 2.5 you'll also need the simplejson_ library.

If you wish to use the systray_ icon you'll also need pygtk_, if you do not wish
to use the systray_ icon you'll need PIL_ for processing the user icons.

``bleeter`` should run with Python 2.5 or any newer release from the 2.x branch.
No effort has been put in to making it work with Python 3, as a few of the
dependencies aren't ported yet.

Configuration
-------------

The first time you run ``bleeter`` you should use the ``--get-token`` option to
setup OAuth_ access.

It is possible to include tweets from users you are not directly following by
adding them to the configuration file, which should be placed in
``${XDG_CONFIG_HOME}/bleeter/config.ini``.  Its format should be::

    stealth = NotThatInteresting,Boring

Where the ``stealth`` value should be a comma separated list of twitter
usernames or numeric identifiers.

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

* Leon Bird
* Matt Leighy
* Rachel Holmes

Ideas
'''''

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
  * While support for Python versions prior to v2.5 may be added in the future
    if such a need were to arise, you are encouraged to use v2.5 features now.
  * All new classes and methods should be accompanied by new ``doctest``
    examples and reStructuredText_ formatted descriptions.
  * Tests *must not* span network boundaries, see ``test.mock`` for workarounds.
  * ``doctest`` tests in modules are only for unit testing in general, and
    should not rely on any modules that aren't in Python's standard library.
  * Functional tests should be in the ``doc`` directory in reStructuredText_
    formatted files, with actual tests in ``doctest`` blocks.  Functional tests
    can depend on external modules, but they must be Open Source.

New examples for the ``doc`` directory are as appreciated as code changes.

Bugs
----

If you find any problems, bugs or just have a question about this package either
drop me a mail_ or file an issue_.  Locally bugs are managed with ditz_, so if
you're working with a clone of the repository you can report, list and fix bugs
using ``ditz``.

If you've found please attempt to include a minimal testcase so I can reproduce
the problem, or even better a patch!

.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/bleeter/issues
.. _ditz: http://ditz.rubyforge.org/
.. _twitter: http://twitter.com/
.. _Python: http://www.python.org/
.. _tweepy: http://pypi.python.org/pypi/tweepy/
.. _notify-python: http://www.galago-project.org/
.. _pygobject: http://www.pygtk.org/
.. _configobj: http://www.voidspace.org.uk/python/configobj.html
.. _xdg-utils: http://portland.freedesktop.org/wiki
.. _KDE: http://www.kde.org/
.. _gnome: http://www.gnome.org/
.. _xfce4-notifyd: http://spuriousinterrupt.org/projects/xfce4-notifyd
.. _notification-daemon: http://www.galago-project.org/
.. _simplejson: http://undefined.org/python/#simplejson
.. _systray: http://standards.freedesktop.org/systemtray-spec/systemtray-spec-latest.html
.. _pygtk: http://www.pygtk.org/
.. _PIL: http://www.pythonware.com/products/pil/index.htm
.. _email: jnrowe@gmail.com
.. _OAuth: http://oauth.net/

..
    :vim: set ft=rst ts=4 sw=4 et:

