import re, random

'''Clean up a string to make it suitable for use in facts'''
def cleanup(string):
    return re.sub("[\\.,\\?!'\"-_=\\\\\\*]", '', string.lower()).strip()
    
'''Trigger facts when said in chat'''
def chatFactCheck(self, body, user, room):
    if self.squelched(room):
        return
    #pickup any factoids after "fritbot", otherwise treat it as a malformed command                        
    rex = self.static_rex['command'].search(body)
    
    if rex is None:
        rex = re.search(r'\A@?(%s)[,:]?\s(?P<command>.*)' % room.nick, body, re.I)
    
    #Check for invalid commands
    if rex is not None:
        command = rex.group("command")
        
        if not checkFactoids(self, command, user, room, True):            
            self.spoutFact(room, "varerror", user.nick)    
        
        return 
        
    #check for factoids                    
    if checkFactoids(self, body, user, room):   
        return
        
'''Check a line to see if any valid facts were triggered'''
def checkFactoids(self, body, user, room, force=False):
    #TODO: Move to commands.facts
    if len(body) < 2:
        return False                        
                        
    trigger = cleanup(body)
    
    sel = 'select target, id, count, triggered, locked from facts where `trigger` = #{0}#;'.format(trigger)                    
        
    if not self.doSQL(sel, False):
        return False
    
    row = self.sql.fetchone()
    
    if row is None:
        #second try!;
        sel = 'select target, id, count, triggered, locked from facts where #{0}# like concat(#%#, `trigger`, #%#) and length(`trigger`) > 3 and locked >= 0 order by length(`trigger`) desc, rand() limit 1;'.format(trigger)
        
        if not self.doSQL(sel, False):
            return False
    
        row = self.sql.fetchone()
        if row is None:
            return False
            
        target = row[0]
        triggered = row[3]
        if triggered is not None and force is False:            
            delta = datetime.datetime.today() - triggered
            if delta.days < 1:
                chance = (delta.seconds / 10000.) - 0.15
                print "Random chance of", target, ":", chance
                if random.random() > chance:
                    print target, "cancelled."
                    return False
    
    if row is not None:
        target = row[0]
        tid = row[1]
        count = row[2]            
        locked = row[4]
        
        if locked == -1:
            print target, "locked from triggering"
            return        
            
        
        upd = 'update facts set triggered=now(), count=count + 1 where id={0}'.format(tid)
        self.doSQL(upd, False)                
                
        return self.spoutFact(room, target, user.nick)
            
    return False

'''Alias one fact to another'''
def cmd_facts_alias(self, command, user, room):
    rex = re.match(r'(?P<orig>.*) alias (?P<new>.*)', command, re.I)
    
    if rex is not None:
        trigger = rex.group("orig")
        alias = rex.group("new")
        
        sel = 'select id from facts where `trigger`=#{0}#;'.format(trigger)
        if not self.doSQL(sel):
            return
        
        row = self.sql.fetchone()
        if row is not None:
            ins = 'update facts set updated=now(), target=#{0}# where `trigger`=#{1}#;'.format(alias, trigger)
            if not self.doSQL(ins):
                return
            self.sendChat(room, "Ok, {0}, {1} is now aliased to {2}. Any facts tied to {1} are now orphaned!".format(user.nick, trigger, alias))
        else:
            self.sendChat(room, "{1} has to exist first, {0}.".format(user.nick, alias))
        
    else:
        self.spoutFact(room, "varerror", user.nick)

'''Learn a fact from a given command'''
def cmd_facts_learn(self, command, user, room, silent=False):
    if silent and ('<' in command or '>' in command):
        return
        
    rex = re.match(r'(?P<trigger>.*?) (?P<verb>({0}|(<.*>))) (?P<fact>.*)'.format(self.verblist), command, re.I)
    
    if rex is not None:
        trigger = cleanup(rex.group("trigger"))
        verb = rex.group("verb").strip('<>')
        fact = rex.group("fact")      
        fact = fact.replace('\\', '')
        if len(trigger) < 2 or (silent and len(trigger) < 5):
            if not silent:
            	self.sendChat(room, "{0}, the trigger was too short. Specify a longer trigger.".format(user.nick))
            return
        
        if len(trigger) > 30:
            if not silent:
                self.sendChat(room, "{0}, no one is going to realistically trigger that. Keep triggers under 30 characters. KTHX".format(user.nick))
            return
            
        if verb == "alias" and not silent:
            sel = 'select target from facts where `trigger`=#{0}#;'.format(trigger)
            if not self.doSQL(sel):
                return
            
            row = self.sql.fetchone()
            if row:
                self.sendChat(room, "That trigger already exists, {0}. Use 'fritbot {1} alias {2}' to alter it.".format(user.nick, trigger, fact))
                return
                 
            sel = 'select target from facts where `trigger`=#{0}#;'.format(fact)
            if not self.doSQL(sel):
                return
            
            row = self.sql.fetchone()
            if row is not None:
                ins = 'insert into facts (`trigger`, target, created, updated) values (#{0}#, #{1}#, now(), now())'.format(trigger, row[0])
                if not self.doSQL(ins):
                    return
                self.sendChat(room, "Ok, {0}, {1} is now aliased to {2}.".format(user.nick, trigger, fact))
            else:
                self.sendChat(room, "{1} has to exist first, {0}.".format(user.nick, fact))
                    
        elif random.random() > 0.9 and (verb == "is" or verb == "has" or verb == "are") and not silent:    
            if verb == "has":
                self.sendChat(room, "Your MOM has {0}!".format(fact))
            else:
                self.sendChat(room, "Your MOM is {0}!".format(fact))                    
            return
        else:
            sel = 'select target, locked from facts where `trigger`=#{0}#;'.format(trigger)
            if not self.doSQL(sel):
                return
            
            row = self.sql.fetchone()
            if not row:
                ins = 'insert into facts (`trigger`, target, created, updated) values (#{0}#, #{0}#, now(), now());'.format(trigger)
                if not self.doSQL(ins):
                    return
            else:
                trigger = row[0]
                locked = row[1]
                if locked != 0:
                    if not silent:
                        self.sendChat(room, "'{0}' has been locked and won't accept new factoids, {1}.".format(trigger, user.nick))
                    return
            
            ins = 'insert into factdata (`trigger`, verb, fact, created, author) values (#{0}#, #{1}#, #{2}#, now(), #{3}#);'.format(trigger, verb, fact, user.nick.lower())
            if not self.doSQL(ins):
                return
                                
            
            if not silent:
                self.sendChat(room, "Ok, {0}.".format(user.nick))
        
    elif not silent:
        self.spoutFact(room, "varerror", user.nick)

'''Lock a fact'''  
def cmd_facts_lock(self, command, user, room):
    rex = re.match("\A(?P<un>un)?lock (?P<which>.*)", command, re.I)
    
    if rex is not None:
        un = rex.group("un") != None
        which = rex.group("which")
        
        sel = "select id from facts where `trigger`=#{0}#".format(which)
        self.doSQL(sel)
        row = self.sql.fetchone()
        if row is None:            
            if not un:
                ins = "insert into facts (`trigger`, target, created, updated, locked) values (#{0}#, #{0}#, now(), now(), -1)".format(which)
                if not self.doSQL(ins):
                    return
                self.sendChat(room, "The fact '{0}' has been created and marked as locked.".format(which))                                        
            else:
                self.sendChat(room, "The fact '{0}' doesn't exist yet, therefore cannot be unlocked.".format(which))
        else:
            fid = row[0]
            if un:
                act = 0
                verb = "Unlocked"
            else:
                act = -1
                verb = "Locked"
            upd = "update facts set locked={0} where id={1}".format(act, fid)
            if not self.doSQL(upd):
                return
            
            self.sendChat(room, "{0} fact '{1}'".format(verb, which))                                    
    else:
        self.sendChat(room, "What do you want to unlock?")
            
'''Spout a fact'''
def cmd_facts_whatwas(self, command, user, room):
    if self.last_triggered is None:
        self.sendChat(room, "Nothing has been triggered recently. Why don't you fuckers say something more interesting.")
    else:
        sel = "select `trigger`, verb, fact, created, author from factdata where id={0}".format(self.last_triggered)
        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is not None:
            trigger = row[0]
            verb = row[1]
            fact = row[2]
            created = row[3]
            author = row[4]
            self.sendChat(room, "That was fact #{5}: '{0} <{1}> {2}' created on {3} by {4}".format(trigger, verb, fact, created, author, self.last_triggered))
        else:
            self.sendChat(room, "Something unexpected happened and I can't retrieve that factoid. Maybe I should quit the boozing...")            
