.. module:: bleeter
   :synopsis: Nasty little twitter client

Main functionality
==================

Constants
---------

.. autodata:: OAUTH_KEY
.. autodata:: OAUTH_SECRET
.. autodata:: USER_AGENT

Classes
-------

.. autoclass:: State
.. autoclass:: Tweets

Functions
---------

Command line functionality
''''''''''''''''''''''''''

.. autofunction:: process_command_line
.. autofunction:: main

Twitter support
'''''''''''''''

.. autofunction:: format_tweet
.. autofunction:: get_user_icon
.. autofunction:: open_tweet
.. autofunction:: skip_check

Interaction
'''''''''''

.. autofunction:: update
.. autofunction:: display
.. autofunction:: tooltip
.. autofunction:: get_token

.. _bleeter-examples:

Examples
--------

.. testsetup::

    from bleeter import format_tweet

.. doctest::

    >>> format_tweet('Populate #sup contacts from #abook')
    'Populate <i>#sup</i> contacts from <i>#abook</i>'
