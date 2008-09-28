from connection import BufferedSockWriter
import socket

class ParseError(Exception):

    pass

class ParsedLine(object):

    def __init__(self, ircline):

        self.ircline = ircline.strip()

    def hostmask(self):

        return self.ircline.split()[0][1:]

    def nick(self):

        return self.hostmask().split('!')[0].replace('~', '')

    def command(self):

        return self.ircline.split()[1]

    
class IRCProtocol(BufferedSockWriter):

    def privmsg(self, target, message):

        if isinstance(message, list):
            for line in message:
                self.privmsg(target, line)
        while message:
            line, message = message[:400], message[400:]
            self.wline('PRIVMSG %s :%s' % (target, line))

    def notice(self, target, message):

        if isinstance(message, list):
            for line in message:
                self.notice(target, message)
        while message:
            line, message = message[:400], message[400:]

    def set_handlers(self, handlers):

        self.handlers = handlers

    def set_state(self, state):

        self.state = state

    def register(self):

        nick, user = self.state.nick(), self.state.user()
        ircname = self.state.ircname()
        self.wline('NICK %s' % nick)
        self.wline('USER %s 0 * : %s' % (user, ircname))
        
    def handle_line(self, line):

        self.line = ParsedLine(line)
        self.log(str(self.line))
        for handler in self.handler:
            try:
                if handler.interested(self.line, self.state):
                    handler.run(self.line, self.state, self)
            except ParseError, err:
                self.reply("Failed to parse this line correctly."
                           " Maybe you haven't set your modes right?")
                self.log(err)

    def topic(self, channel, new=None):

        if new is not None:
            self.wline('TOPIC %s :%s' % (channel, topic))
        else:
            self.wline('TOPIC %s' % channel)
            
    def reply(self, message):

        assert self.line
        target = self.line.reply_target()
        self.privmsg(target, message)
        
    def nick(self, new):

        self.wline('NICK %s' % new)

    def whois(self, target):

        self.wline('WHOIS %s' % target)

    def whowas(self, target):

        self.wline('WHOWAS %s' % target)

    def retry(self, tries=3):

        if self.tries > 0:
            try:
                self.sock = self.sockmaker()
                self.buf = ""
                self.sock.connect((self.dst, self.port))
                self.register()
            except socket.error, err:
                self.log('Failed to reconnect with %s' % err)
                self.retry(tries - 1)

    def usermode(self, user, mode):

        self.wline('MODE %s %s' % (user, mode))

    def channel_mode(self, channel, mode):

        self.wline('MODE %s %s' % (channel, mode))

    def channel_mode_user(self, channel, mode, user):

        self.wline('MODE %s %s %s' % (channel, mode, user))

    def op(self, user, channel):

        self.channel_mode_user(channel, '+o', user)

    def deop(self, user, channel):

        self.channel_mode_user(channel, '-o', user)

    
