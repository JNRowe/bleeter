``bleeter``
===========

Frequently Asked Questions
--------------------------

.. contents::

Why another twitter client?
---------------------------

Because other clients didn't do quite what I wanted, or work on the systems
I wanted to use them on.

The closest I came to finding a usable client for my needs was gwibber_.  It
doesn't work quite right on my mobile devices though and there are a few bugs
that need fixing before I could use it on my desktop, but unfortunately the
source is on launchpad.

So, in the end writing ``bleeter`` seemed like the obvious answer.  It didn't
take long, does exactly what I want and works where I want it to work.

.. _gwibber: https://launchpad.net/gwibber

I can't click on the tweets!
----------------------------

If you're using Ubuntu that is a design goal of their new notify-osd_ default
notification system.  Find another client, install another notification daemon
or just read the tweets and refer to twitter.com when you wish to interact.

The specific feature that is required is called ``actions``.  It is possible to
use ``notify-osd`` with actions by just ignoring the servers stated
capabilities, and then ``notify-osd`` opens a alert box for each message which
is even less useful than just being a passive reader.

Patches for integration with the Ubuntu notification and indicator system
probably won't be accepted unless other distributions decide to switch.

.. _capabilities testing:

You can check what features your notification daemon has by running the
following in a Python interpreter::

    >>> impory pynotify
    >>> pynotify.init("test")
    >>> pynotify.get_server_caps()
    ['actions', 'body', 'body-hyperlinks', 'body-markup', 'icon-static']

.. _notify-osd: https://launchpad.net/notify-osd

The icons are cut in half in tweets!
------------------------------------

.. figure:: http://jnrowe.github.com/images/e17-notify.png

   e17's notification module with cropped icon

If you're using e17_ with its `notification module`_ then there isn't a great
deal I can do about this, it is just a bug in that module.

If you're not using e17_ and see behaviour like this please `file a bug`_ or
send me a mail_!!

.. _e17: http://enlightenment.org/
.. _notification module: http://trac.enlightenment.org/e/browser/trunk/E-MODULES-EXTRA/notification/
.. _file a bug: http://github.com/JNRowe/bleeter/issues
.. _mail: jnrowe@gmail.com

There are no buttons on the tweets!
-----------------------------------

If you're using Ubuntu or e17_ this is expected behaviour.  Neither the Ubuntu
or e17_ notification systems support the ``actions`` capability that is required
for adding buttons to notifications,

The only ways around this are to find another client, install another
notification daemon or just read the tweets and refer to twitter.com when you
wish to interact.

See `capabilities testing`_ for a method to check your notification systems
support.


..
    :vim: set ft=rst ts=4 sw=4 et:

