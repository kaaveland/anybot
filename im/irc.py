"""
This module provides a reasonably
complete IRC client for use with selector.Reactor.
"""

from connection import BufferedSockWriter
import socket
import irc2num

class ParseError(Exception):
    """Represents an IRC parse error."""
    
    pass

    
class ParsedLine(object):
    """Instanciate this with an ircline to be able to query it
    for generic information."""
    
    def __init__(self, ircline):
        """Provide a unicode or str object to parse."""
        
        self.ircline = ircline.strip()

    def hostmask(self):
        """The hostmask of the sender (Potentially a server)."""
        
        return self.ircline.split()[0][1:]

    def nick(self):
        """Nick of the sender."""
        
        return self.hostmask().split('!')[0].replace('~', '')

    def command(self):
        """Which command was used?"""

        com = self.ircline.split()[1]
        return irc2num.num2rpl.get(com, com)

    def __str__(self):
        """Printable string of line."""

        return self.ircline.encode('utf-8')
        
    def params(self):
        """Get the params part of the line."""

        return ' '.join(self.ircline.split(' ')[2:])

    def message(self):
        """Get the message part of a privmsg or notice or equivalent line."""

        return self.params().split()[1:]

    def target(self):
        """Get the target of a command."""

        if self.command() in ('PRIVMSG', 'NOTICE', 'TOPIC',
                              'JOIN', 'PART', 'KICK'):
            return self.params().split()[0]
        else:
            raise ParseError('Getting target of command %s not yet supported.' % self.command())

        
    
class IRCProtocol(BufferedSockWriter):
    """Extend BufferedSockWriter to give a logging, buffered client
    supporting a decent subset of the irc protocol.

    It expects you to call set_state and set_handlers
    on it as well.

    A state supports the following methods:
    nick() - return the nick to be used for this connection.
    user() - return the user to be used for this connection.
    ircname() - return the ircname to be used for this connection.
    And anything handlers might want to use (As they have access to it).
    Good place to put SQL connection objects, configuration data
    and things like that.

    A handler supports:
    interested(ParsedLine, state) - return a true value if the handler
                                    wants to run on this line.
    run(ParsedLine, state, IRCProtocol) - Let handler perform IO with
                                          IRCProtocol instance.
    This is the plugin system of this class.
    """
    
    def privmsg(self, target, message):
        """Send message to target. Message is either a list
        of unicode/str instances, or a unicode/str instance."""
        
        if isinstance(message, list):
            for line in message:
                self.privmsg(target, line)
        elif isinstance(message, unicode):
            message = message.encode('utf-8')
        while message:
            line, message = message[:400], message[400:]
            self.wline('PRIVMSG %s :%s' % (target, line))

    def notice(self, target, message):
        """Send a notice. See privmsg for description of params."""
        
        if isinstance(message, list):
            for line in message:
                self.notice(target, message)
        elif isinstance(message, unicode):
            message = message.encode('utf-8')
        while message:
            line, message = message[:400], message[400:]

    def set_handlers(self, handlers):
        """Set the line handlers on self to the list
        handlers."""
        
        self.handlers = handlers

    def set_state(self, state):
        """Set the state of self."""
        
        self.state = state

    def add_handler(self):
        """Add a handler to self."""
        
        self.handlers.append(handler)
        
    def register(self):
        """Register this irc client.

        Sends nick, user and ircname."""
        
        BufferedSockWriter.register(self)
        nick, user = self.state.nick(), self.state.user()
        ircname = self.state.ircname()
        self.wline('NICK %s' % nick)
        self.wline('USER %s 0 * : %s' % (user, ircname))
        
    def handle_line(self, line):
        """Handle a line. Pings are automatically handled
        here. Run interested handlers on line."""
        
        self.log(line)
        if 'PING' in line.upper():
            line = line.split()
            if len(line) == 3:
                self.wline('PONG %s' % line[2])
            else:
                self.wline('PONG %s' % line[1])
            return
        self.line = ParsedLine(line)
        for handler in self.handlers:
            try:
                if handler.interested(self.line, self.state):
                    handler.run(self.line, self.state, self)
            except ParseError, err:
                self.reply("Failed to parse this line correctly."
                           " Maybe you haven't set your modes right?")
                self.log(err)

    def topic(self, channel, new=None):
        """Run the IRC topic command."""
        
        if new is not None:
            self.wline('TOPIC %s :%s' % (channel, topic))
        else:
            self.wline('TOPIC %s' % channel)
            
    def reply(self, message):
        """Send message to whoever asked something of this bot the
        last time."""
        
        assert self.line
        target = self.line.target()
        if target == self.state.nick():
            self.privmsg(self.line.nick(),
                         message)
        else:
            self.privmsg(target, message)

    def nreply(self, message):
        """Send message to whoever asked something of this client the last time,
        using notice."""

        assert self.line
        target = self.line.target()
        if target == self.state.nick():
            self.notice(self.line.nick(), message)
        else:
            self.notice(target, message)
            
    def nick(self, new):
        """The IRC nick command."""
        
        self.wline('NICK %s' % new)

    def whois(self, target):
        """The IRC whois command."""
        
        self.wline('WHOIS %s' % target)

    def whowas(self, target):
        """The irc whowas command."""
        
        self.wline('WHOWAS %s' % target)

    def retry(self, tries=3):
        """Try to reconnect and reregister again."""
        
        if tries > 0:
            try:
                self.sock = self.sockmaker()
                self.buf = ""
                self.register()
                return True
            except socket.error, err:
                self.log('Failed to reconnect with %s' % err)
                self.retry(tries - 1)

    def usermode(self, user, mode):
        """Set modes on user."""
        
        self.wline('MODE %s %s' % (user, mode))

    def channel_mode(self, channel, mode):
        """Set modes on channel."""
        
        self.wline('MODE %s %s' % (channel, mode))

    def channel_mode_user(self, channel, mode, user):
        """Set a mode on user on channel."""
        
        self.wline('MODE %s %s %s' % (channel, mode, user))

    def op(self, user, channel):
        """Give user operator status on channel."""
        
        self.channel_mode_user(channel, '+o', user)

    def deop(self, user, channel):
        """Take away operator status from user on channel."""
        
        self.channel_mode_user(channel, '-o', user)

    def join(self, channel, key=None):
        """Join channel. If password protected, provide key."""
        
        if key:
            self.wline('JOIN %s %s' %(channel, key))
        else:
            self.wline('JOIN %s' % channel)

    def part(self, channel):
        """Part channel."""
        
        self.wline('PART %s' % channel)

    def kick(self, channel, nick, comment=None):
        """Kick nick from channel, optionally providing a comment."""
        
        if comment:
            self.wline('KICK %s %s %s' % (channel, nick, comment))
        else:
            self.wline('KICK %s %s' % (channel, nick))

    def invite(self, nick, channel):
        """Invite nick to channel (Requires operator mode)."""
        
        self.wline('INVITE %s %s' % (nick, channel))

    def names(self, channels):
        """Run the IRC names command."""
        
        if isinstance(channels, list):
            self.wline('LIST %s' % ','.join(channels))
        else:
            self.wline('LIST %s' % channels)

    def who(self, mask, operator=False):
        """Run the irc who command."""
        
        if operator:
            self.wline('WHO %s o' % mask)
        else:
            self.wline('WHO %s' % mask)

    def away(self, message=None):
        """When message is provided, set away status
        and use message, otherwise toggle away status."""
        
        if message:
            self.wline('AWAY %s' % message)
        else:
            self.wline('AWAY')

    def ping(self, target=None):
        """Send a ping to target."""
        
        if server is None:
            self.wline('PING :%s' % self.dst)
        else:
            self.wline('PING :%s' % server)
