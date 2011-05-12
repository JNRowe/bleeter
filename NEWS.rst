``bleeter``
===========

User-visible changes
--------------------

.. contents::

0.8.0 - 2011-05-12
------------------

    * Main script is now installed as ``bleeter`` without the ``.py`` extension
    * Desktop entry for easier systray management in modern desktops
    * zsh_ completion script in ``extra``
    * Display status in process title, if setproctitle_ is available

.. _zsh: http://www.zsh.org/
.. _setproctitle: http://code.google.com/p/py-setproctitle/

0.7.0 - 2010-12-20
------------------

    * New ``--mobile`` option for low-bandwidth links
    * Optional SSL twitter communication
    * Support for multiple map providers
    * Optional support for twitter_'s saved searches and lists
    * Coloured terminal output with termcolor_

.. _termcolor: http://pypi.python.org/pypi/termcolor/


0.6.0 - 2010-07-12
------------------

    * OAuth_ authentication is now handled inline
    * pygtk_ is now required
    * Python_ v2.6, or later release from the v2 branch, is required
    * URL matching has been improved
    * Stealth user tweet fetching has been improved, meaning less hits to twitter_

.. _pygtk: http://www.pygtk.org/
.. _python: http://www.python.org/

0.5.0 - 2010-05-16
------------------

    * Optional URL expansion with urlunshort_
    * Links are now opened using ``xdg-open`` from xdg-utils_ if it is
      available, which should handle default browsers better
    * User names and hashtags are now linked in notifications if your daemon
      supports links
    * The status icon is only shown when there are tweets pending displayed

.. _urlunshort: http://bitbucket.org/runeh/urlunshort
.. _xdg-utils: http://portland.freedesktop.org/wiki

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
