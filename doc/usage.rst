Usage
-----

:program:`bleeter.py` must initially be run from the command line to fetch the
user's authentication data::

    $ bleeter.py --get-token

Once you've set up the authentication following runs of :program:`bleeter.py`
can be run from either the command prompt or your session's startup files.

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

.. cmdoption:: -r <key>,<secret>, --token=<key>,<secret>

   OAuth token for twitter(mostly used for testing)

.. cmdoption:: -g, --get-token

   generate a new OAuth token for twitter

.. cmdoption:: -s ewornj, --stealth=ewornj

   users to watch without following(comma separated)

.. cmdoption:: -i "#nowplaying", --ignore "#nowplaying"

   keywords to ignore in tweets(comma separated)

.. cmdoption:: --no-tray

   disable the system tray icon

.. cmdoption:: -v, --verbose

   produce verbose output

.. cmdoption:: -q, --quiet

   output only results and errors

