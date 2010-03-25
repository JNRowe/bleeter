bleeter - Nasty little twitter client
=====================================

Introduction
------------

``bleeter`` is a nasty little client for twitter_, currently very much in a *Works
For Me* state.  It isn't intended to be used by others, but perhaps others will
find it useful.

All it currently does is fetch your friends timeline and display notification
popups for new tweets.  Nothing more and nothing less.

Requirements
------------

``bleeter``'s only mandatory dependencies outside of the Python_ standard library
are the configobj_, notify-python_, pygobject_ and tweepy_ packages.

It should run with Python 2.5 or newer.

Configuration
-------------

It is also possible to include tweets from users you are not directly following
by adding them to the configuration file, which should be placed in
``${XDG_CONFIG_HOME}/bleeter/config.ini``.  Its format should be::

    stealth = NotThatInteresting,Boring

Where the ``stealth`` value should be a comma separated list of twitter
usernames or numeric identifiers.

``bleeter`` reads the ``TWEETUSERNAME`` and ``TWEETPASSWORD`` environment
variables to store authentication data.  It is also possible to store the
username and password in the configuration file using the following format::

    user = username
    password = unguessable


Hacking
-------

Patches are most welcome, but I'd appreciate it if you could follow the
guidelines below to make it easier to integrate your changes.  These are
guidelines however, and as such can be broken if the need arises or you
just want to convince me that your style is better.

  * `PEP 8`_, the style guide, should be followed where possible.
  * While support for Python versions prior to v2.5 may be added in the
    future if such a need were to arise, you are encouraged to use v2.5
    features now.
  * All new classes and methods should be accompanied by new
    ``doctest`` examples and reStructuredText_ formatted descriptions.
  * Tests *must not* span network boundaries, see ``test.mock`` for
    workarounds.
  * ``doctest`` tests in modules are only for unit testing in general,
    and should not rely on any modules that aren't in Python's standard
    library.
  * Functional tests should be in the ``doc`` directory in
    reStructuredText_ formatted files, with actual tests in ``doctest``
    blocks.  Functional tests can depend on external modules, but they
    must be Open Source.

New examples for the ``doc`` directory are as appreciated as code
changes.

Bugs
----

If you find any problems, bugs or just have a question about this package either
drop me a mail_ or file an issue_.  Locally bugs are managed with ditz_, so if
you're working with a clone of the repository you can report, list and fix bugs
using ``ditz``.

If you've found please attempt to include a minimal testcase so I can
reproduce the problem, or even better a patch!

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

..
    :vim: set ft=rst ts=4 sw=4 et:

