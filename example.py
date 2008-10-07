"""
Example on how to use the im library to write a bot program.
"""

from im import selector, irc
import sys

class BotState(object):
    """This will hold vital information suck as:
    nicknames and alternate nicknames,
    usernames and ircnames,
    and any state that plugins might be interested in.
    """

    def __init__(self, nicknames, username, ircname):
        """A list of nicknames to use, an irc username, and an ircname."""
        
        # Multiple nicknames, so if the server kicks us off
        # for busy nickname, we can use another.
        self._nicks = nicknames
        self._user = username
        self._ircname = ircname
        self.current_nick = 0
        self.messages = {} # For a handler we'll write.
        
    def nick(self):
        
        # Select the next nickname to use.
        nick = self._nicks[self.current_nick]
        self.current_nick = (self.current_nick + 1) % len(self._nicks)
        return nick

    def user(self):

        return self._user

    def ircname(self):

        return self._ircname

# The handler interface has two methods,
# interested and run
# For our purposes here, using those will duplicate
# more than it'll help, so we'll just use functions
# and instanciate a handler with them since we don't need inheritance.
    
class Handler(object):
    """Generic handler class."""
    
    def __init__(self, interested, run):
        """Takes two callables as arguments."""
        
        self.interested = interested
        self.run = run

def interested_rem(line, state):
    """Are we interested in saving a reminder?"""
    
    return line.command() in ('PRIVMSG', 'NOTICE') and line.message().startswith('!remind')

def remember(line, state, sockwriter):
    """Remember this message for someone (Or help them figure out how this works."""
    
    if len(line.message().split()) < 3:
        sockwriter.nreply('Usage: !remind <nick> <message>')
    else:
        nick = line.message().split()[1]
        message = ' '.join(line.message().split()[2:])
        state.messages[nick] = state.messages.get(nick, []) + [(line.nick(), message)]
        sockwriter.nreply('Will remind %s about %s.' % (nick, message))

# We now have a handler for saving reminders.
reminder = Handler(interested_rem, remember)

def interested_join(line, state):
    """Is someone asking us to join a channel?"""
    
    return line.command() in ('PRIVMSG', 'NOTICE') and line.message().startswith('!join')

def join(line, state, sockwriter):
    """Join the channel, or tell the someone how to use our command."""
    
    if len(line.message().split()) < 2:
        sockwriter.nreply('Usage: !join <channel> [<key>]')
    else:
        channel = line.message().split()[1]
        if len(line.message().split()) == 3:
            key = line.message().split()[2]
        else:
            key = ""
        sockwriter.join(channel, key)

# We now have a handler for joining channels.
joiner = Handler(interested_join, join)

def interested_tell(line, state):
    """Do we have any reminders for this person?"""
    
    return line.nick() in state.messages

def tell(line, state, sockwriter):
    """Give the reminders to the person."""
    
    nick = line.nick()
    messages = state.messages.pop(nick)
    for sender, message in messages:
        sockwriter.notice(nick, '%s told me to remind you about %s' % (sender, message))

# We now have a handler who will tell people about their reminders.
teller = Handler(interested_tell, tell)

def log(event):
    """ A pseudo-logger, this will instead print everything
    of interest to stdout (The controlling console)."""
    
    if not event:
        return
    # Most lines are unicode, and they are not printable before being encoded.
    if isinstance(event, unicode):
        event = event.encode('utf-8')
    # If it's not a string (Could be an exception)
    # turn it into a string.
    if not isinstance(event, basestring):
        event = str(event)
    print event
    
if __name__ == '__main__':
    
        port = 6667
        if len(sys.argv) < 2:
            print 'Usage: python example.py server1 <server2 ...>'
            sys.exit()
        hosts = sys.argv[1:] # For ever command line argument, we'll make an irc client.
        clients = [irc.IRCProtocol(host, port, log=log) for host in hosts] # All connect to 6667
        state = BotState(['IRCBot', 'Botolf'], 'Botolf', 'This is a bot') # They all use the same nick, user and ircname.
        for client in clients:
            client.set_state(state) # Tell the client about it's nick and things like that.
            client.set_handlers([reminder, joiner, teller]) # Add functionality to the client.
            client.register() # Run it.
        reactor = selector.Reactor(clients)
        reactor.loop() # Loop indefinitely.

