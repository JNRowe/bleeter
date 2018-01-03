.. module:: bleeter.utils
   :synopsis: Utilities for bleeter

Utilities
=========

Functions
---------

Stylised text
'''''''''''''

.. autofunction:: success
.. autofunction:: fail
.. autofunction:: warn

File utilities
''''''''''''''

.. autofunction:: mkdir
.. autofunction:: create_lockfile
.. autofunction:: find_app_icon

Interaction support
'''''''''''''''''''

.. autofunction:: usage_note
.. autofunction:: open_browser

Time support
''''''''''''

.. autofunction:: relative_time

URL support
'''''''''''

.. autodata:: URLS
.. autofunction:: url_expand

Process support
'''''''''''''''

.. autofunction:: wrap_proctitle
.. autofunction:: proctitle_decorator

.. _utils-examples:

Examples
--------

.. testsetup::

    from datetime import datetime
    from bleeter.utils import file, find_app_icon, relative_time

    now = datetime.utcnow()

.. doctest::
   :options: +SKIP

    >>> create_lockfile()

.. doctest::

    >>> find_app_icon()
    '/usr/share/pixmaps/bleeter.png'
    >>> relative_time(now - datetime.timedelta(days=365))
    'last year'
