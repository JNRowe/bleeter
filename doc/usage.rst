Usage
-----

:program:`bleeter.py` will seek authorisation when initially run.  As twitter_
uses OAuth_ this process is a little more cumbersome than it should be.

* An authentication link will be opened in your default browser, allowing you to
  sign in to twitter_ and declare that you want :program:`bleeter` to have
  access to your account.
* A small dialog window will pop up where you can enter the PIN given to you by
  twitter_.

If you wish to create a new authentication token, or need to regenerate it, you
can be doing one of the following::

    $ bleeter.py --get-token
    $ rm ${XDG_DATA_HOME:-~/.local}/bleeter/oauth_token

Options
'''''''

.. program:: bleeter.py

.. cmdoption:: --version

   show program's version number and exit

.. cmdoption:: -h, --help

   show this help message and exit

.. cmdoption:: -t <n>, --timeout=<n>

   timeout for notification popups in seconds

.. cmdoption:: -f <n>, --frequency=<n>

   update frequency in in seconds

.. cmdoption:: -g, --get-token

   generate a new OAuth token for twitter

.. cmdoption:: --secure

   use SSL to connect to twitter

.. cmdoption:: --no-secure

   don't use SSL to connect to twitter

.. cmdoption:: -s ewornj, --stealth=ewornj

   users to watch without following(comma separated)

.. cmdoption:: --no-stealth

   don't check stealth users for updates

.. cmdoption:: -i "#nowplaying", --ignore "#nowplaying"

   keywords to ignore in tweets(comma separated)

.. cmdoption:: --no-ignore

   don't test for ignore keywords

.. cmdoption:: --no-tray

   disable the system tray icon

.. cmdoption:: -e, --expand

   expand links in tweets

.. cmdoption:: --no-expand

   don't expand links in tweets

.. cmdoption:: --count

   maximum number of tweets to fetch(max 200)

.. cmdoption:: --lists

   fetch user's lists

.. cmdoption:: --no-lists

   don't fetch user's lists

.. cmdoption:: --no-cache

   don't cache twitter communications

.. cmdoption:: -v, --verbose

   produce verbose output

.. cmdoption:: -q, --quiet

   output only results and errors

.. _oauth: http://oauth.net/
.. _twitter: http://twitter.com/
