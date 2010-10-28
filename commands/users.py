import re

'''Register functionality with the bot'''
def register(bot):
    commands = [cmd for cmd in globals() if 'cmd_' in cmd]
    for cmd in commands:
        bot.__dict__[cmd] = globals()[cmd]
     
'''Check when and where the user was last seen'''
def cmd_users_seen(self, command, user, room):
    rex = re.match("\Aseen ((?P<here>here) )?(?P<who>.*)", command, re.I)
    
    if rex is not None:
        here = rex.group("here")
        who = rex.group("who")
        
        sel = "select user, nick from nicks where nick like #%{0}%# and room = #{1}#".format(who, room.fbid)
        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is None:
            sel = "select user, nick from nicks where nick like #%{0}%#".format(who)
            self.doSQL(sel)
            row = self.sql.fetchone()
            if row is None:
                self.sendChat(room, "Sorry, I can't find anyone with a nickname like {0}.".format(who))
                return
        
        who_user = row[0]
        who_nick = row[1]
        
        print who_user, who_nick
        
        if here is not None:
            sel = "select r.name, n.lastseen, n.said from nicks n, rooms r where r.id = n.room and n.user = #{0}# and n.room = #{1}# order by lastseen desc limit 1".format(who_user, room.fbid)
        else:
            sel = "select r.name, n.lastseen, n.said from nicks n, rooms r where r.id = n.room and n.user = #{0}# order by lastseen desc limit 1".format(who_user)

        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is not None:
            self.sendChat(room, "I last saw {0} in {1} at {2} saying: {3}".format(who_nick, row[0], row[1], row[2]))
        else:
            self.sendChat(room, "I don't think {0} has said anything recently.".format(who_nick))
    else:
        self.sendChat(room, "Seen who to the what where when?")  
