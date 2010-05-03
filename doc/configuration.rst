Configuration
-------------

:program:`bleeter` stores its configuration in
:file:`${XDG_CONFIG_HOME}/bleeter/config.ini` [#]_.

The configuration file is a simple ``INI`` format file,   The file is processed
with the configobj_ module, the documentation for which will describe some of
the advanced features available within the configuration file.

An example configuration file is below:

.. code-block:: ini

    frequency = 600
    timeout = 10
    stealth = unfolloweduser,stalkeduser
    ignore = "#nowplaying"

``frequency`` option
''''''''''''''''''''

The ``frequency`` option allows you to set the update frequency for checking for
new tweets.  Its value is specified in seconds, and *must* be higher than 60.

``timeout`` option
''''''''''''''''''

The ``timeout`` option allows you to specify the default notification timeout,
Its value is specified in seconds.  Not all notification daemons support setting
this value, and some daemons may simply ignore it.

``stealth`` option
''''''''''''''''''

The ``stealth`` option allows you to specify a list of users you wish to receive
tweets from without following, its main purpose is to follow people for limited
periods of time without needing to follow and unfollow them.

Consider the use case of attending a conference and wanting to follow your
fellow attendees without having to explicitly unfollow them once the conference
is over.

``ignore`` option
'''''''''''''''''

The ``ignore`` option allows you to specify a list of keywords you wish to
use as ignore filters for tweets you receive.  Keywords can be normal words,
``@user`` usernames, ``#tag`` hashtags or any other word type.

The default is "#nowplaying" to ignore all the audio player spam that some
people like to produce.

The entries should be comma separated, and must be quoted if they contain '#'
to match hashtags.

.. [#] The default value for ``${XDG_CONFIG_HOME}`` is system dependent, but
       likely to be ``~/.config`` if you haven't set it.  For more information
       see `XDG base directory specification`_.

.. _configobj: http://www.voidspace.org.uk/python/configobj.html
.. _XDG base directory specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
