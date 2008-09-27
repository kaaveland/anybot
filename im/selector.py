import socket
import select

class Reactor(object):

    def __init__(self, clients=None, logger=None):

        if clients is None:
            self.clients = []
        else:
            self.clients = clients
        self.logger = logger

    def addclient(self, client):

        self.clients.append(client)
        
    def log(self, event):

        if self.logger:
            self.logger(event)
            
    def tick(self):

        assert self.clients
        filenos = [client.id() for client in self.clients]
        inputs = select.select(filenos, [], [])
        for input in inputs:
            client = filter(lambda client: client.id() == input, self.clients)[0]
            try:
                client.do_io()
            except socket.error, err:
                self.log(err)
                if not client.retry():
                    self.clients.remove(client)

    def loop(self):

        while True:
            self.tick()
            
                
