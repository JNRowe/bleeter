Configuration
=============

:program:`bleeter` stores its configuration in
``${XDG_CONFIG_HOME}/bleeter/config.ini`` [#s1]_.

The configuration file is a simple ``INI`` format file,   The file is processed
with the :pypi:`configobj` module, the documentation for which will describe
some of the advanced features available within the configuration file.

You can specify command line options in the configuration file as defaults, and
optionally override them from the command line.  To toggle disabled options from
the command line use their ``--no-`` prefixed versions.

An example configuration file is below:

.. code-block:: ini

    frequency = 600
    timeout = 10
    stealth = unfolloweduser,stalkeduser
    ignore = "#nowplaying"

``frequency`` option
--------------------

The :option:`frequency` option allows you to set the update frequency for
checking for new tweets.  Its value is specified in seconds, and *must* be
higher than 60.

``timeout`` option
------------------

The :option:`timeout` option allows you to specify the default notification
timeout, its value is specified in seconds.

.. note::

    Not all notification daemons support setting this value, and some daemons
    may simply ignore it.

.. _stealth-label:

``stealth`` option
------------------

The :option:`stealth` option allows you to specify a list of users you wish to
receive tweets from without following, its main purpose is to follow people for
limited periods of time without needing to go through the follow and unfollow
dance.

Consider the use case of attending a conference and wanting to follow your
fellow attendees without having to explicitly unfollow them once the conference
is over.

``ignore`` option
-----------------

The :option:`ignore` option allows you to specify a list of keywords you wish to
use as ignore filters for tweets you receive.  Keywords can be normal words,
``@user`` usernames, ``#tag`` hashtags or any other word type.

The default is ``#nowplaying`` to ignore all the audio player spam that some
people like to produce.

The entries should be comma separated, and must be quoted if they contain ``#``
to match hashtags.

Consider the use case of following a user who frequently interacts with one of
the copious poisonous people to be found on twitter, adding
a ``@secondary_user`` filter means you won’t see the interactions regardless of
how they’re referenced in a tweet.

``count`` options
------------------

The :option:`count` option allows you to specify the maximum number of new
statuses from your timeline to fetch when updating.  Only new tweets are
fetched, so specifying large values here only affects initial runs and users who
do not run :program:`bleeter` very often.

By default twitter_ returns 20 new statuses, and this is also the default
setting for :program:`bleeter`.  twitter_ sets a limit of 200 statuses, so
larger values are of no use.

The :option:`search_count` and :option:`list_count` options perform the same
task for search results and list timelines respectively.  The
:option:`stealth_count` option performs the same task for stealth follows, see
:ref:`stealth-label` for more information.

``lists`` option
----------------

The :option:`lists` option enables fetching of the user’s lists, in addition to
the standard behaviour of fetching the user’s timeline and mentions.

``searches`` option
-------------------

The :option:`searches` option enables fetching of the user’s saved searches, in
addition to the standard behaviour of fetching user’s timeline and
mentions.

.. rubric:: Footnotes

.. [#s1] The default value for :envvar:`${XDG_CONFIG_HOME}` is system dependent,
         but likely to be ``~/.config`` if you haven’t set it.  For more
         information see `XDG base directory specification`_.

.. _XDG base directory specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
.. _twitter: https://twitter.com/
