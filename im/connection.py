import socket
import datetime
import time

CRLF = '\r\n'
LF = '\n'

class LineReciever(object):

    def __init__(self, destination, port, sockmaker=socket.socket):

        self.sock = sockmaker()
        self.dst, self.port = destination, port
        self.buf = ""
        self.sock.connect((self.dst, self.port))
        self.term = CRLF
        
    def id(self):

        return self.sock.fileno()

    def do_io(self):

        self.buf += self.sock.recv()
        if CRLF in self.buf:
            for line in self.buf.split(CRLF):
                self.handle_line(line)
        elif LF in self.buf:
            for line in self.buf.split(LF):
                self.handle_line(line)
        if CRLF in self.buf or LF in self.buf:
            self.buf = ""

    def handle_line(self, line):

        return NotImplemented

    def retry(self):

        return NotImplemented

    def set_term(self, new):

        self.term = new
        
def makelogger(name, format='%Y %m %d %H:%M'):

    logfile = open(name, 'a')
    def log(event):
        now = datetime.datetime.now().strftime(format)
        for line in event.split('\n'):
            logfile.write("%s | %s\n" % (now, event))
            
class LoggingReciever(LineReciever):

    def __init__(self, destination, port, sockmaker=socket.socket, log=None):

        if log is not None:
            self.log = log
        else:
            self.log = makelogger(self.dst)
        try:
            LineReciever.__init__(self, destination, port, sockmaker)
        except socket.error, err:
            self.log(err)
            raise
        
    def do_io(self):

        try:
            LineReciever.do_io(self)
        except Exception, error:
            self.log(error)
            raise

class BufferedSockWriter(LoggingReciever):

    def __init__(self, destination, port, sockmaker=socket.socket, log=None):

        LoggingReciever.__init__(self, destination, port, sockmaker, log)
        self.last = 0
        self.interval = 1

    def set_interval(self, new):

        self.interval = new
        
    def wline(self, line):

        if time.time() < self.last + self.interval:
            time.sleep(self.last + self.interval - time.time())
        self.sock.sendall(line.rstrip() + self.term)

    
