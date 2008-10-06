"""
This module provides a reactor that will allow
an application to read from several files
simultaneously, without using threads.

For a more complete reactor, take a look at
twistedmatrix.com. The idea behind this design
has been 'stolen' from there.
"""

import socket
import select

class Reactor(object):
    """This class runs a select-loop to check if
    file descriptors have input, and if they do,
    it notifies the client the fd belongs to."""
    
    def __init__(self, clients=None, logger=None):
        """Instanciate a Reactor with a list of clients,
        and a logger, both of which may be None.

        A client supports three methods:
        client.id() - should return a valid file descriptor.
                      in Python most file-like objects can give
                      you their fd by calling object.fileno().
        client.do_io() - client should deal with it's io,
                         by reading it and stowing it away in a
                         buffer, or reacting to it in some way.
        client.retry() - The client had a socket.error or IOError,
                         and should try to fix it's problem.
                         If this returns a false value, it is removed
                         from the list of clients.
        A logger is simply a callable of one argument, and it's
        obviously meant to log that argument (Which may be a string,
        or an exception).
        """
        if clients is None:
            self.clients = []
        else:
            self.clients = clients
        self.logger = logger

    def addclient(self, client):
        """Add a client to this reactor."""
        
        self.clients.append(client)
        
    def log(self, event):
        """Log event."""
        if self.logger:
            self.logger(event)
            
    def tick(self):
        """Perform one tick of the select loop."""
        
        assert self.clients
        filenos = [client.id() for client in self.clients]
        inputs = select.select(filenos, [], [])[0]
        for input in inputs:
            client = filter(lambda client: client.id() == input, self.clients)[0]
            try:
                client.do_io()
            except (IOError, socket.error), err:
                self.log(err)
                if not client.retry():
                    self.clients.remove(client)

    def loop(self):
        """Loop indefinitely, calling self.tick."""
        
        while True:
            self.tick()
            
                
