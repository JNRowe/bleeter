``bleeter``
===========

User-visible changes
--------------------

.. contents::

0.4.0 - 2010-04-21
------------------

    * Systray icon is now optional
    * Tweets with geotags have a button to open the location in `Google Maps`_
    * Added support for ignoring tweets containing certain words, by default
      the ``#nowplaying`` hashtag

.. _Google maps: http://maps.google.com/

0.3.0 - 2010-04-07
------------------

    * Switched to OAuth_
    * User images are now resized to a reasonable size
    * Added a button to retweet from within the notifications
    * Added status icon showing number of pending tweets

.. _oauth: http://oauth.net/

0.2.0 - 2010-02-28
------------------

    * Switched to the tweepy_ twitter_ library
    * Support for notifications daemons that don't support markup in messages
    * Open displayed tweet in a browser by clicking the notification
    * Support for overriding options from the command line
    * Displays user "mentions"
    * A button to mark tweets as favourites from within the notification

.. _tweepy: http://pypi.python.org/pypi/tweepy/
.. _twitter: http://twitter.com/

0.1.0 - 2010-02-10
------------------

    * Initial release

..
    :vim: set ft=rst ts=4 sw=4 et:

