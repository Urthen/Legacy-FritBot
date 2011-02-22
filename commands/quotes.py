import re, random
     
'''Quote a given user and quote'''
def cmd_quotes_quote(self, command, user, room):       
    if self.squelched(room):
        return
    rex = re.match("quote (?P<user>[^']+) ?(['\"](?P<what>.+)['\"])?", command, re.I)
    
    if rex is not None:
        user = rex.group("user").strip()
        what = rex.group("what")
        print what, command
        
        if what is None:
            whats = ""
        else:
            whats = "and quote like #%{0}%#".format(what)
            
        sel = "select quote from quotes where nick = #{0}# {1}and removed is null order by rand() limit 1".format(user, whats)
        if not self.doSQL(sel):
            return
        
        row = self.sql.fetchone()
        
        if row is None:
            sel = "select quote from quotes where nick like #%{0}%# {1}and removed is null order by rand() limit 1".format(user, whats)
            
            if not self.doSQL(sel):
                return
                
            row = self.sql.fetchone()
            if row is None:
                if what == "":
                    self.sendChat(room, "Sorry, I can't find any quotes for anyone matching {0}.".format(user))
                else:
                    self.sendChat(room, "Sorry, I can't find any quotes for anyone matching {0} with the phrase {1}.".format(user, what))
                return
               
        self.sendChat(room, row[0])
    else:
        self.sendChat(room, "Quote who, {0}?".format(user.nick))   
   
'''Remember a quote'''     
def cmd_quotes_remember(self, command, user, room):
    rex = re.match(r'remember (?P<user>\S+) (?P<quote>.+)', command, re.I)
    
    if rex is not None:
        target = rex.group("user")
        quote = rex.group("quote")
        
        for history in room.data['history'][::-1]:          
            if target.lower() in history[0].nick.lower():
                if quote.lower() in history[1].lower():
                
                    if history[0].fb_user_id == user.fb_user_id:
                        self.sendChat(room, "You can't quote yourself, {0}. Say something funnier and maybe someone else will remember you.".format(user.nick))
                        return
                        
                    message = "<{0}>: {1}".format(history[0].nick.lower(), history[1])
                    
                    qget = 'select * from quotes where quote=#{0}#;'.format(message)
                    if not self.doSQL(qget):
                        return
                    row = self.sql.fetchone()
                    if row is None:                                                
                        self.sendChat(room, "Ok, {0}, remembering {1}".format(user.nick, message))
                        qins = 'insert into quotes (nick, quote, created, author) values (#{0}#, #{1}#, now(), #{2}#);'.format(history[0].nick.lower(), message, user.nick.lower())
                        self.doSQL(qins)
                        return   
                    else:
                        self.sendChat(room, "{0}, I already know that about {1}.".format(user.nick, message))
                        return
                    
        self.sendChat(room, "I can't seem to recall '{0}' said by anyone named {1}".format(quote, target))
                    
    else:
        self.sendChat(room, "Remember what exactly, {0}?".format(user.nick))
        
'''Quote-specific statistics'''
def cmd_quotes_quotestats(self, command, user, room):
    rex = re.match(r'quotestats( (?P<who>.*))?', command, re.I)
    
    if rex is not None:
        who = rex.group('who')
        
        if who is None or who == "me":
            who = user.nick.lower()
                    
        sela = "select count(1) from quotes where nick=#{0}# and removed is null".format(who)
        selb = "select count(1) from quotes where author=#{0}# and removed is null".format(who)
        selc = "select count(1) from quotes where removed is null"
        self.doSQL(sela)
        row = self.sql.fetchone()
        quoted = int(row[0])
        self.doSQL(selb)
        row = self.sql.fetchone()
        author = int(row[0])
        self.doSQL(selc)
        row = self.sql.fetchone()
        total = float(row[0])
        
        message = "{0} has been quoted {1} times ({2:.1%} of total) and has quoted {3} others ({4:.1%})".format(who, quoted, quoted / total, author, author / total)
        self.sendChat(room, message)
        return        
        
    self.sendChat(room, "Show quote stats for who?")
    
'''Quotemashing: Generate a random conversation based on remembered quotes'''
def cmd_quotes_mash(self, command, user, room):
    limit = random.randrange(2, 6)
    sel = "select quote from quotes where removed is null order by rand() limit {0}".format(limit)
    self.doSQL(sel)
    row = self.sql.fetchone()
    
    while row is not None:
        self.sendChat(room, row[0])
        row = self.sql.fetchone()
