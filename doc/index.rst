.. _bleeter-label:

|modref|
========

.. module:: bleeter
   :synopsis: Nasty little twitter viewer
.. moduleauthor:: James Rowe <jnrowe@gmail.com>

.. ifconfig:: release.endswith("-git")

   .. warning::
      This documentation was built from a Git tree, and may not correspond
      directly to *any* released version.  Check the release tarballs for
      documentation for a particular version of ``bleeter``.

.. warning::
   This project is dead and unsupported.  While it may work for you, you’re on
   your own if it doesn’t.

|modref| is a nasty little viewer for twitter_, currently very much in a *Works
For Me* state.  It isn't intended to be used by others, but perhaps others will
find it useful.

All it does is fetch your friends timeline and display notification popups for
new tweets.  If your system's notification daemon supports adding actions [#s1]_
to the popups then you'll be able to make a number of choices by clicking the
buttons on the popup.

It is written in Python_, and requires v3.5 or later.  |modref| is released
under the `GPL v3`_ license.

:Git repository:  https://github.com/JNRowe/bleeter/
:Issue tracker:  https://github.com/JNRowe/bleeter/issues/
:Contributors:  https://github.com/JNRowe/bleeter/contributors/

Contents
--------

.. toctree::
   :maxdepth: 1

   background
   install
   configuration
   usage
   bleeter manpage <bleeter.1>
   thaw
   release
   NEWS
   api/index
   faq

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. rubric:: Footnotes

.. [#s1] Most common notification daemons support actions, including
         xfce4-notifyd_ and Galago's notification-daemon_.

.. _Python: http://www.python.org
.. _GPL v3: http://www.gnu.org/licenses/
.. _xfce4-notifyd: http://spuriousinterrupt.org/projects/xfce4-notifyd
.. _notification-daemon: http://www.galago-project.org/
.. _twitter: https://twitter.com/
