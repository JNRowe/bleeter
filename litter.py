#! /usr/bin/python -tt

import atexit
import json
import os
import sys
import time

from xml.sax.saxutils import escape

import pynotify
import twitter

def update(api, seen):
    for m in reversed(api.GetFriendsTimeline()):
        if m.id in seen:
            continue
        else:
            seen.append(m.id)
            n = pynotify.Notification("From %s at %s " % (m.user.name, m.created_at),
                                      escape(m.text),
                                      "Twitter-48.png")
            if api._username in m.text:
                n.set_urgency(pynotify.URGENCY_CRITICAL)
            if m.text.startswith("@%s" % api._username):
                n.set_timeout(10)
            n.show()
            time.sleep(4)

def main(argv):
    pynotify.init(argv[0])
    api = twitter.Api(os.getenv("TWEETUSERNAME"), os.getenv("TWEETPASSWORD"))
    if os.path.exists("%s.dat" % argv[0]):
        seen = json.load(open("%s.dat" % argv[0]))
    else:
        seen = []

    def save_state(seen):
        json.dump(seen, open("%s.dat" % argv[0], "w"), indent=4)
    atexit.register(save_state, seen)

    while True:
        update(api, seen)
        time.sleep(300)

if __name__ == '__main__':
    main(sys.argv[:])
