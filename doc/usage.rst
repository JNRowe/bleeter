Usage
-----

:program:`bleeter` will seek authorisation when initially run.  As twitter_
uses OAuth_ this process is a little more cumbersome than it should be.

* An authentication link will be opened in your default browser, allowing you to
  sign in to twitter_ and declare that you want :program:`bleeter` to have
  access to your account.
* A small dialog window will pop up where you can enter the PIN given to you by
  twitter_.

If you wish to create a new authentication token, or need to regenerate it, you
can be doing one of the following:

.. code-block:: sh

    $ bleeter --get-token
    $ rm ${XDG_DATA_HOME:-~/.local}/bleeter/oauth_token

Options
'''''''

.. program:: bleeter

.. option:: --version

   show program's version number and exit

.. option:: -h, --help

   show this help message and exit

.. option:: -t <n>, --timeout=<n>

   timeout for notification popups in seconds

.. option:: -f <n>, --frequency=<n>

   update frequency in in seconds

.. option:: -g, --get-token

   generate a new OAuth token for twitter

.. option:: --secure

   use SSL to connect to twitter

.. option:: --no-secure

   don't use SSL to connect to twitter

.. option:: -s ewornj, --stealth=ewornj

   users to watch without following(comma separated)

.. option:: --no-stealth

   don't check stealth users for updates

.. option:: -i "#nowplaying", --ignore "#nowplaying"

   keywords to ignore in tweets(comma separated)

.. option:: --no-ignore

   don't test for ignore keywords

.. option:: --no-tray

   disable the system tray icon

.. option:: -e, --expand

   expand links in tweets

.. option:: --no-expand

   don't expand links in tweets

.. option:: -m, --mobile

   open links in lighter mobile versions

.. option:: --no-mobile

   don't open links in lighter mobile versions

.. option:: --map-provider "google"

   open geo links using specified site

.. option:: --count

   maximum number of timeline tweets to fetch(max 200)

.. option:: --stealth-count

   maximum number of stealth tweets to fetch

.. option:: --search-count

   maximum number of tweets to fetch for searches

.. option:: --list-count

   maximum number of tweets to fetch for lists

.. option:: --lists

   fetch user's lists

.. option:: --no-lists

   don't fetch user's lists

.. option:: --searches

   fetch user's saved searches

.. option:: --no-searches

   don't fetch user's saved searches

.. option:: --no-cache

   don't cache twitter communications

.. option:: -v, --verbose

   produce verbose output

.. option:: -q, --quiet

   output only results and errors

.. _oauth: http://oauth.net/
.. _twitter: http://twitter.com/
