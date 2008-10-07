"""
This package supplies tools for working with automated services
connected to a server. It was written with IRC in mind, so it's not
very generic, in that it pretty much assumes a single client connected
to a central server, and it's not easy for a client to add further connections
at runtime (But possible, though you might have to avoid selector.Reactor.loop.
"""

__all__ = [
    "irc",
    "selector",
    "connection",
    "irc2num"
    ]

