import re, time


'''Change authorization level of a room'''
def cmd_core_auth(self, command, user, room):
    rex = re.match(r'\Aauth (?P<auth>[012])', command, re.I)
    
    if rex is not None and user.nick.lower() in self.rulerlist:     
        auth = int(rex.group("auth"))                        
        
        upd = "update rooms set auth=#{0}# where id=#{1}#".format(auth, room.fbid)
        self.doSQL(upd)
        room.auth = auth
        
        self.sendChat(room, "Ok, set auth level for this room to {0}".format(auth))
                    
    else:
        self.spoutFact(room, "varerror", user.nick)       
        
'''Change nickname'''
def cmd_core_ghost(self, command, user, room):
    rex = re.match("((become)|(ghost)) (?P<who>.*)", command, re.I)
    
    if rex is not None:
        nickname = rex.group("who")
        self.nick(room.entity_id, nickname)
        self.sendChat(room, "Behold! By the power of {0}, I am now {1}!".format(user.nick, nickname))
    else:
        self.sendChat("Become who, {0}?".format(user.nick))                 
    
'''Jump into another room'''
def cmd_core_jump(self, command, user, room):
    rex = re.match(r'(((go)|(jump)) ((to)|(in))|(join)) (?P<chan>[\S]+)( as)?( (?P<as>.*))?', command, re.I)
    if rex is None:
        self.sendChat(room, "Go where, {0}?".format(user.nick))
        return
        
    server = rex.group("chan")
    print server
        
    if server is None:
        self.sendChat(room, "Go where, {0}?".format(user.nick))
        return
        
    if server in self.roomlist:
        self.sendChat(room, "I'm already in {0}!".format(server))
        return
        
    nick = rex.group("as")
    if nick is None:
        nick = self.nickname
    self.joinRoom(server, nick) 
    self.sendChat(room, "Ok, I've jumped into {0}!".format(server))         
    return
        
'''Leave a room'''    
def cmd_core_leave(self, command, user, room):
    rex = re.match(r'(leave)( (?P<chan>[\S]+))?', command, re.I)
    if user.nick.lower() in self.rulerlist:
        chan = rex.group("chan")
        
        if chan is None:
            chan = room.name
            
        if chan not in self.roomlist:     
            self.sendChat(room, "I'm not in {0}.".format(chan))
            return
        
        self.leaveRoom(chan)
        
        if chan != room.name:
            self.sendChat(room, "Ok, I've left {0}.".format(chan))
        
    else:
        self.spoutFact(room, "varerror", user.nick)                   
        
'''Shutdown the bot'''        
def cmd_core_shutdown(self, command, user, room):
    if user.nick.lower() in self.rulerlist:
        self.sendChat(room, "Bye bye!")
        reactor.callLater(1, parent.stopService)
        reactor.callLater(2, reactor.stop)
    else:
        self.spoutFact(room, "varerror", user.nick)    

'''Squelch the bot'''            
def cmd_core_quiet(self, command, user, room):    
    rex = re.match(r'((shut up)|((be )?quiet( down)?)|(go away))( (for )?(?P<time>.*))?', command, re.I)
    
    if rex is not None:
        if room.auth < 2:
            self.sendChat(room, "I've been forced not to talk in this room. Shutting me up does nothing more.")    
            return
            
        t = rex.group("time")            
        seconds = 240
        if t is not None:
            if t == "a sec" or t == "a second":
                seconds = 30
            elif t == "a bit":
                seconds = 300
            elif t == "a while":
                seconds = 600
            else:
                rex2 = re.match(r'([0-9]+)([smh])', t)
                if rex2:
                    seconds = int(rex2.group(1))
                    if rex2.group(2) == "m":
                        seconds *= 60
                    if rex2.group(2) == "h":
                        seconds *= 60 * 60
        message = "Ok, {0}, shutting up for {1}".format(user.nick, time.strftime('%H:%M:%S', time.gmtime(seconds)))
        self.sendChat(room, message)
        room.data['squelched'] = time.time() + seconds        

'''Unsquelch the bot'''
def cmd_core_wakeup(self, command, user, room):
    if self.squelched(room):
        if room.auth < 2:
            self.sendChat(room, "Sorry, I can't talk in this room.")
        else:
            self.sendChat(room, "Ok, {0}, I'm back.".format(user.nick))
            room.data['squelched'] = 0
    else:
        self.sendChat(room, "I was already back, but thanks for the invitation.")

