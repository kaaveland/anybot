"""
This module provides a few baseclasses for basic
line-terminated protocols, for use with selector.Reactor.
"""

import socket
import datetime
import time

CRLF = '\r\n'
LF = '\n'

class LineReciever(object):
    """Baseclass for a client which can connect to a server, and deals
    with buffering of lines when there's input on its socket."""
    
    def __init__(self, destination, port, sockmaker=socket.socket):
        """Initiate with:
        destination - ip or address,
        port - TCP port number,
        sockmaker - a factory for sockets. Useful for testing,
                    by writing a mocksocket object. Needs
                    support for fileno, and recv.
        Methods that should be overriden:
        handle_line
        register (Needs to connect the socket)
        retry.
        """
        
        self.sock = sockmaker()
        self.sockmaker = sockmaker
        self.dst, self.port = destination, port
        self.buf = ""
        self.term = CRLF
        
    def id(self):
        """Return fd of socket."""
        
        return self.sock.fileno()

    def do_io(self):
        """Deal with input on socket."""
        
        self.buf += self.sock.recv(2048)
        if CRLF in self.buf:
            for line in self.buf.split(CRLF):
                self.handle_line(line.decode('utf-8'))
        elif LF in self.buf:
            for line in self.buf.split(LF):
                self.handle_line(line.decode('utf-8'))
        if CRLF in self.buf or LF in self.buf:
            self.buf = ""

    def register(self):
        """Register this client."""
        
        self.sock.connect((self.dst, self.port))
    
    def handle_line(self, line):
        """Override."""
        
        return NotImplemented

    def retry(self):
        """Override."""
        
        return NotImplemented

    def set_term(self, new):
        """Set the protocol terminator."""
        
        self.term = new
        
def makelogger(name, format='%Y %m %d %H:%M'):
    """Make a logger, logging to name (filepath),
    using format for timestamps.

    For more information on format, see man strptime and
    man strftime."""
    
    logfile = open(name, 'a')

    def log(event):
        """Log this event."""
        
        now = datetime.datetime.now().strftime(format)
        if isinstance(event, unicode):
            event = event.encode('utf-8')
        for line in str(event).split('\n'):
            logfile.write("%s | %s\n" % (now, line))
    return log

def nonlogger(name):
    """Fake a logger."""
    def log(event):
        pass
    return log

class LoggingReciever(LineReciever):
    """This behaves like a LineReciever, but
    logs exceptions."""
    
    def __init__(self, destination, port, sockmaker=socket.socket, log=None):
        """Log is a callable of one argument."""
        
        if log is not None:
            self.log = log
        else:
            self.log = makelogger(destination)
        LineReciever.__init__(self, destination, port, sockmaker)
        
    def do_io(self):
        """Perform io operations, and log any errors."""
        
        try:
            LineReciever.do_io(self)
        except Exception, error:
            self.log(error)
            raise

class BufferedSockWriter(LoggingReciever):
    """This behaves like LoggingReciever aside from
    using adding a wline method for writing to
    its socket (with sendall), and using buffering to
    stay nice to the server it is connected to.

    You can use set_interval to set a new interval between
    writes. Should be a relatively small number."""
    
    def __init__(self, destination, port, sockmaker=socket.socket, log=None):
        """See LoggingReciever.__init__."""
        
        LoggingReciever.__init__(self, destination, port, sockmaker, log)
        self.last = 0
        self.interval = 1

    def set_interval(self, new):
        """Set a new interval for buffered output."""
        
        self.interval = new
        
    def wline(self, line):
        """Write a line to socket."""
        
        self.log('>>> %s' % line)
        if time.time() < self.last + self.interval:
            time.sleep(self.interval)
        self.sock.sendall(line.rstrip() + self.term)
        
