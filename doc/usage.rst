Usage
=====

:program:`bleeter` will seek authorisation from twitter_ when initially run.  As
twitter_ uses OAuth_ this process is a little more cumbersome than it could
ideally be.

* An authentication link will be opened in your default browser, allowing you to
  sign in to twitter_ and declare that you want :program:`bleeter` to have
  access to your account.
* A small dialog window will pop up where you can enter the PIN given to you by
  twitter_.

If you wish to create a new authentication token, or need to regenerate it, you
can be doing one of the following:

.. code-block:: console

    $ bleeter --get-token
    $ rm ${XDG_DATA_HOME:-~/.local}/bleeter/oauth_token

Options
-------

.. program:: bleeter

.. option:: --version

   Show program’s version number and exit

.. option:: -h, --help

   Show this help message and exit

.. option:: -t <n>, --timeout=<n>

   Timeout for notification popups in seconds

.. option:: -f <n>, --frequency=<n>

   Update frequency in in seconds

.. option:: -g, --get-token

   Generate a new OAuth token for twitter

.. option:: --secure

   Use SSL to connect to twitter

.. option:: --no-secure

   Don’t use SSL to connect to twitter

.. option:: -s ewornj, --stealth=ewornj

   Users to watch without following(comma separated)

.. option:: --no-stealth

   Don’t check stealth users for updates

.. option:: -i "#nowplaying", --ignore "#nowplaying"

   Keywords to ignore in tweets(comma separated)

.. option:: --no-ignore

   Don’t test for ignore keywords

.. option:: --no-tray

   Disable the system tray icon

.. option:: -e, --expand

   Expand links in tweets

.. option:: --no-expand

   Don’t expand links in tweets

.. option:: -m, --mobile

   Open links in lighter mobile versions

.. option:: --no-mobile

   Don’t open links in lighter mobile versions

.. option:: --map-provider "google"

   Open geo links using specified site

.. option:: --count

   Maximum number of timeline tweets to fetch(max 200)

.. option:: --stealth-count

   Maximum number of stealth tweets to fetch

.. option:: --search-count

   Maximum number of tweets to fetch for searches

.. option:: --list-count

   Maximum number of tweets to fetch for lists

.. option:: --lists

   Fetch user’s lists

.. option:: --no-lists

   Don’t fetch user’s lists

.. option:: --searches

   Fetch user’s saved searches

.. option:: --no-searches

   Don’t fetch user’s saved searches

.. option:: --no-cache

   Don’t cache twitter communications

.. option:: -v, --verbose

   Produce verbose output

.. option:: -q, --quiet

   Output only results and errors

.. _oauth: http://oauth.net/
.. _twitter: https://twitter.com/
