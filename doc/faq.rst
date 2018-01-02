Frequently Asked Questions
--------------------------

Why another twitter client?
'''''''''''''''''''''''''''

Because other clients didn’t do quite what I wanted, or work on the systems
I wanted to use them on.

So, in the end writing ``bleeter`` seemed like the obvious answer.  It didn’t
take long, does exactly what I want and works where I want it to work.

Why is the logo so crap?
''''''''''''''''''''''''

.. image:: .static/bleeter.png

Because *I* made it with my complete lack of design skills, if you can do better
please do so.  Send me a mail_ if you come up with something better.

.. _mail: jnrowe@gmail.com

I can’t click on the tweets!
''''''''''''''''''''''''''''

If you’re using Ubuntu that is a design goal of their new notify-osd_ default
notification system.  Find another client, install another notification daemon
or just read the tweets and refer to twitter_ when you wish to interact.

The specific feature that is required is called ``actions``.  It is possible to
use actions with ``notify-osd`` by just ignoring the servers stated
capabilities, but then ``notify-osd`` will open an alert box for each message
which is even less useful than just being a passive reader.

Patches for integration with the Ubuntu notification and indicator system
probably won’t be accepted unless other distributions decide to switch.  Such
changes are currently too invasive for their value.

.. _capabilities testing:

You can check what features your notification daemon has by running the
following in a Python interpreter::

    >>> impory pynotify
    >>> pynotify.init("test")
    >>> pynotify.get_server_caps()
    ['actions', 'body', 'body-hyperlinks', 'body-markup', 'icon-static']

.. _notify-osd: https://launchpad.net/notify-osd
.. _twitter: https://twitter.com

The icons are cut in half in tweets!
''''''''''''''''''''''''''''''''''''

.. figure:: .static/e17-notify.png

   e17’s notification module with cropped icon

If you’re using e17_ with its `notification module`_ then there isn’t a great
deal I can do about this, it is just a bug in that module.

If you’re not using e17_ and see behaviour like this please `file an issue`_ or
send me a mail_!!

.. _e17: http://enlightenment.org/
.. _notification module: http://trac.enlightenment.org/e/browser/trunk/E-MODULES-EXTRA/notification/
.. _file an issue: https://github.com/JNRowe/bleeter/issues/

There are no buttons on the tweets!
'''''''''''''''''''''''''''''''''''

If you’re using Ubuntu or e17_ this is expected behaviour.  Neither the Ubuntu
or e17_ notification systems support the ``actions`` capability that is required
for adding buttons to notifications.

The only workarounds for this are to find another client, install another
notification daemon or just read the tweets and refer to twitter_ when you wish
to interact.

See `capabilities testing`_ for a method to check your notification systems
support for ``actions``.  If you’re not seeing buttons and your notification
daemon supports ``actions`` please `file an issue`_ or send me a mail_!!

The tweets don’t have the same formatting as the screenshots!
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

If you’re using Ubuntu, Xfce_ or e17_ this is expected behaviour.

.. figure:: .static/ubuntu-notify3.png

    Example tweet being displayed with Ubuntu’s notification system

It is likely the feature you’re missing is either ``body-markup`` or
``body-hyperlinks``, see `capabilities testing`_ for a method you can use to
check your notification systems supported capabilities.

The Xfce_ notification system, xfce4-notifyd_, supports ``actions`` and
``body-markup`` which means it is still quite usable with ``bleeter``.  The only
functionality you’ll be missing is the direct opening of links within tweet
text.

If you’re not using either Ubuntu, Xfce_ or e17_ but you’re having display
problems then you may have found a bug.  You’re encouraged to post a screenshot
online and either link to it when you `file an issue`_ or send me a mail_ with a
link to the image and an explanation of the problem.

.. _Xfce: http://www.xfce.org/
.. _xfce4-notifyd: http://spuriousinterrupt.org/projects/xfce4-notifyd

.. _pypi listing:

Why isn’t this listed on PyPI?
''''''''''''''''''''''''''''''

For the Python projects I’ve posted on PyPI_, or contributed to significantly,
I’d say at least 90% of the bug reports have been from ``easy_install`` users
with problems caused by ``easy_install``.  Frankly dealing with those has sucked
the life out of my hobby projects for far too long already.

Handling such bug reports killed public releases of upoints_, and the plone_
users finally killed public releases of pyisbn_.  Having given this some
considerable thought I decided that my hobby projects shouldn’t be exposed to
that, so that they can remain fun.  I apologise if this causes you
inconvenience.

Why can’t I ``easy_install`` this?
''''''''''''''''''''''''''''''''''

See `PyPI listing`_.

.. _PyPI: https://pypi.python.org/pypi
.. _upoints: https://github.com/JNRowe/upoints/
.. _plone: http://plone.org/
.. _pyisbn: https://github.com/JNRowe/pyisbn/
