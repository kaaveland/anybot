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

class Handler(object):

    def __init__(self, interested, run):

        self.interested = interested
        self.run = run

def interested_rem(line, state):

    return line.command() in ('PRIVMSG', 'NOTICE') and line.message().startswith('!remind')

def remember(line, state, sockwriter):

    if len(line.message().split()) < 3:
        sockwriter.nreply('Usage: !remind <nick> <message>')
    else:
        nick = line.message().split()[1]
        message = ' '.join(line.message().split()[2:])
        state.messages[nick] = state.messages.get(nick, []) + [(line.nick(), message)]
        sockwriter.nreply('Will remind %s about %s.' % (nick, message))

reminder = Handler(interested_rem, remember)

def interested_join(line, state):

    return line.command() in ('PRIVMSG', 'NOTICE') and line.message().startswith('!join')

def join(line, state, sockwriter):

    if len(line.message().split()) < 2:
        sockwriter.nreply('Usage: !join <channel> [<key>]')
    else:
        channel = line.message().split()[1]
        if len(line.message().split()) == 3:
            key = line.message().split()[2]
        else:
            key = ""
        sockwriter.join(channel, key)
        
joiner = Handler(interested_join, join)

def interested_tell(line, state):

    return line.nick() in state.messages

def tell(line, state, sockwriter):

    nick = line.nick()
    messages = state.messages.pop(nick)
    for sender, message in messages:
        sockwriter.notice(nick, '%s told me to remind you about %s' % (sender, message))

teller = Handler(interested_tell, tell)

def log(event):
    if not event:
        return
    if isinstance(event, unicode):
        event = event.encode('utf-8')
    if not isinstance(event, basestring):
        event = str(event)
    print event
    
if __name__ == '__main__':
    
        port = 6667
        if len(sys.argv) < 2:
            print 'Usage: python example.py server1 <server2 ...>'
            sys.exit()
        hosts = sys.argv[1:]
        clients = [irc.IRCProtocol(host, port, log=log) for host in hosts]
        state = BotState(['IRCBot', 'Botolf'], 'Botolf', 'This is a bot')        
        for client in clients:
            client.set_state(state)
            client.set_handlers([reminder, joiner, teller])
            client.register()
        reactor = selector.Reactor(clients)
        reactor.loop()
