.. _bleeter-label:

:mod:`bleeter`
==============

.. module:: bleeter
   :synopsis: Nasty little twitter viewer
.. moduleauthor:: James Rowe <jnrowe@gmail.com>

.. ifconfig:: release.endswith("-git")

   .. warning::
      This documentation was built from a Git tree, and may not correspond
      directly to *any* released version.  Check the release tarballs for
      documentation for a particular version of ``bleeter``.

:mod:`bleeter`  is a nasty little viewer for twitter_, currently very much in
a *Works For Me* state.  It isn't intended to be used by others, but perhaps
others will find it useful.

All it does is fetch your friends timeline and display notification popups for
new tweets.  If your system's notification daemon supports adding actions [#]_
to the popups then you'll be able to make a number of choices by clicking the
buttons on the popup.

.. [#] Most common notification daemons support actions, including
       xfce4-notifyd_ and Galago's notification-daemon_.

It is written in Python_, and requires v2.6 or later.  :mod:`bleeter` is
released under the `GPL v3`_

Contents:

.. toctree::
   :maxdepth: 1

   background
   install
   configuration
   usage
   bleeter manpage <bleeter.1>
   faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Python: http://www.python.org
.. _GPL v3: http://www.gnu.org/licenses/
.. _xfce4-notifyd: http://spuriousinterrupt.org/projects/xfce4-notifyd
.. _notification-daemon: http://www.galago-project.org/
.. _twitter: http://twitter.com/
