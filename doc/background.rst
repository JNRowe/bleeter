Background
----------

I have had no real urge to use twitter_, and to this day I still don’t.
Unfortunately, I know a few people who use only twitter_ to push updates.
Originally, I had included the RSS feed of their timelines in my feed reader,
but I had been finding it to be a touch too annoying to process the entries that
way.  I decided to bite the bullet and use a twitter client, that way I could
also watch the build bots for a couple of projects I care about too.

And that is where the problems began.  It turns out there are no clients that
suit my needs.  All I want is something fast, light, usable on my mobile
devices, not too distracting and preferably not taking up an entire virtual
desktop for the latest “Just had a coffee” incantation.

The closest I came to finding a usable client was with gwibber_ or twirssi_,

gwibber_ didn’t quite work out because of a few show-stopper bugs when using it
on my desktop, and some layout issues on my mobile devices.  The package also
appears to be in a state of serious flux right now, and hacking it on it to fix
the bugs would be painful because of that.  Plus the size of the changes to make
it work correctly on my mobile devices would be immense, and that isn’t a fun
prospect given that it is hosted on launchpad.

twirssi_ was ruled out because it required a very complex setup to use from my
phone, with IRC proxies and an always on server connection to feed it.  It is
definitely a very cool project though, and I suspect it would quickly become my
client of choice if I started to “use” twitter_ a lot.

The obvious answer to all this was to just make a little script to do exactly
what I wanted... and |modref| was born.  It isn’t pretty, it isn’t clean, it
isn’t even that useful but it Works For Me™.

.. _twitter: httsp://twitter.com/
.. _gwibber: https://launchpad.net/gwibber/
.. _twirssi: http://www.twirssi.com/
