import re

'''Get the user's position in the leaderboard'''
def getPos(rows, nick):
    pos = 0
    lastcount = 0
    for row in rows:
        if row[1] != lastcount:
            pos += 1
        if nick == row[0]:
            return "{0} (#{1})".format(row[1], pos)
        lastcount = row[1]
    return "None"

'''Register functionality with the bot'''
def register(bot):
    commands = [cmd for cmd in globals() if 'cmd_' in cmd]
    for cmd in commands:
        bot.__dict__[cmd] = globals()[cmd]
     
'''Forget a bit of content'''
def cmd_common_forget(self, command, user, room):
    rex = re.match(r"(?P<un>un)?forget (?P<all>all )?(?P<what>(item)|(quote)|(fact(oid)?)|(that))s?( '?(?P<which>[^']+)'? (?P<snip>.+))?", command, re.I)
    if rex is not None:
        force = rex.group("all") != None
        what = rex.group("what")
        which = rex.group("which")
        snip = rex.group("snip")
        table = None
        
        if what == "that":
            if self.last_triggered is None:
                self.sendChat(room, "Nothing has been triggered recently. Why don't you fuckers say something more interesting.")
                return
                
            if rex.group("un") is not None:
                remove = "null"
                self.sendChat(room, "Ok, {0}, unforgetting fact #{1}.".format(user.nick.lower(), self.last_triggered))
            else:
                remove = "#" + user.nick.lower() + "#"
                self.sendChat(room, "Ok, {0}, forgetting fact #{1}.".format(user.nick.lower(), self.last_triggered))               
                
            rm = 'update factdata set removed={0} where id=#{1}#'.format(remove, self.last_triggered)                                    
            self.doSQL(rm)
                            
            
            return
        
        if rex.group("un") is None:
            remove = "null"
        else:
            remove = "not null"  
            
        if what == "quote":                
                
            sel = 'select quote from quotes where removed is {2} and nick=#{0}# and quote like #%{1}%#;'.format(which, snip, remove)
            
            if not self.doSQL(sel):
                return
            if self.sql.rowcount > 1 and not force:
                self.sendChat(room, "That returned more than one quote, {0}. Be more specific, or affect them all with '(un)forget all quote'".format(user.nick))
            elif self.sql.rowcount == 0:
                self.sendChat(room, "That didn't return any quotes, {0}.".format(user.nick))
            else:
                row = self.sql.fetchone()
                
                if remove == "null":
                    action = "removing"
                else:
                    action = "unforgetting"
                self.sendChat(room, "Ok, {0} is {3} {2}'s quote '{1}'".format(user.nick, row[0], which, action))
                
                if remove == "null":
                    remove = '#{0}#'.format(user.nick.lower())
                else:
                    remove = 'null'
                    
                rm = 'update quotes set removed={0} where nick=#{1}# and quote like #%{2}%#;'.format(remove, which, snip)
                self.doSQL(rm)
        elif what == "item":
            if snip is not None:
                which = which + " " + snip
            sel = 'select name from items where name=#{0}#'.format(which)
            self.doSQL(sel)
            row = self.sql.fetchone()
            
            if row is not None:
                if remove == "null":
                    action = "removing"
                else:
                    action = "unforgetting"
                self.sendChat(room, "Ok, {0} is {2} item '{1}'".format(user.nick, which, action))
                
                if remove == "null":
                    remove = '#{0}#'.format(user.nick.lower())
                else:
                    remove = 'null'
                    
                rm = "update items set removed={0}, backpack=0 where name=#{1}#".format(remove, which)
                self.doSQL(rm)
            else:
                self.sendChat(room, "That didn't return any items, {0}! Be exact!".format(user.nick))
            
        elif what == "fact" or what == "factoid":
            sel = 'select fact from factdata where removed is {2} and `trigger` like #%{0}%# and fact like #%{1}%#;'.format(which, snip, remove)
            
            if not self.doSQL(sel):
                return
            if self.sql.rowcount > 1 and not force:
                self.sendChat(room, "That returned more than one factoid, {0}. Be more specific, or affect them all with '(un)forget all fact'".format(user.nick))
            elif self.sql.rowcount == 0:
                self.sendChat(room, "That didn't return any facts, {0}.".format(user.nick))
            else:
                row = self.sql.fetchone()
                
                if remove == "null":
                    action = "removing"
                else:
                    action = "unforgetting"
                self.sendChat(room, "Ok, {0} is {3} response to factoid '{2}': '{1}'".format(user.nick, row[0], which, action))
                
                if remove == "null":
                    remove = '#{0}#'.format(user.nick.lower())
                else:
                    remove = 'null'
                    
                rm = 'update factdata set removed={0} where `trigger` like #%{1}%# and fact like #%{2}%#;'.format(remove, which, snip)
                self.doSQL(rm)
        
        return
        
    self.sendChat(room, "What do you want me to forget, {0}?".format(user.nick))                                                                  
    
'''Current user leaderboard'''    
def cmd_common_leaderboard(self, command, user, room):
    rex = re.match("leader(boards?)?( (?P<who>.*))?", command, re.I)
    
    if rex is not None:
        who = rex.group("who")
        if who is None:
            sel_quoted = "select nick, count(nick) from quotes where removed is null and nick != 'mr. fritters' group by nick order by count(nick) desc limit 1"
            sel_quotes = "select author, count(author) from quotes where removed is null and author != 'mr. fritters' group by author order by count(author) desc limit 1"
            sel_facts = "select d.author, count(d.author) from factdata d, facts f where d.author != 'mikey' and d.author != 'mr. fritters' and d.removed is null and d.`trigger` = f.target and f.locked > -1 and f.`trigger` = f.`target` group by author order by count(author) desc limit 1"
            sel_items = "select author, count(author) from items where author != 'mr. fritters' and author != 'mikey' group by author order by count(author) desc limit 1"
            
            self.doSQL(sel_quoted)
            quotedrow = self.sql.fetchone()
            self.doSQL(sel_quotes)
            quotesrow = self.sql.fetchone()
            self.doSQL(sel_facts)
            factsrow = self.sql.fetchone()
            self.doSQL(sel_items)
            itemsrow = self.sql.fetchone()  
            
            message = "Current leaderboard! Facts: {0} ({1}); Times Quoted: {2} ({3}); Quotes Remembered: {4} ({5}); Items Created: {6} ({7})"
            self.sendChat(room, message.format(factsrow[0], factsrow[1], quotedrow[0], quotedrow[1], quotesrow[0], quotesrow[1], itemsrow[0], itemsrow[1]))
        elif who == "plus":
            sel_quoted = "select nick, count(nick) from quotes where removed is null group by nick order by count(nick) desc limit 1"
            sel_quotes = "select author, count(author) from quotes where removed is null group by author order by count(author) desc limit 1"
            sel_facts = "select d.author, count(d.author) from factdata d, facts f where d.removed is null and d.`trigger` = f.target and f.locked > -1 and f.`trigger` = f.`target` group by author order by count(author) desc limit 1"
            sel_items = "select author, count(author) from items group by author order by count(author) desc limit 1"
            
            self.doSQL(sel_quoted)
            quotedrow = self.sql.fetchone()
            self.doSQL(sel_quotes)
            quotesrow = self.sql.fetchone()
            self.doSQL(sel_facts)
            factsrow = self.sql.fetchone()
            self.doSQL(sel_items)
            itemsrow = self.sql.fetchone()                
            
            
            message = "Current leaderboard plus Fritters! Facts: {0} ({1}); Times Quoted: {2} ({3}); Quotes Remembered: {4} ({5}); Items Created: {6} ({7})"
            self.sendChat(room, message.format(factsrow[0], factsrow[1], quotedrow[0], quotedrow[1], quotesrow[0], quotesrow[1], itemsrow[0], itemsrow[1]))
        else:
            sel_quoted = "select nick, count(nick) from quotes where removed is null and nick != 'mr. fritters' group by nick order by count(nick) desc"
            sel_quotes = "select author, count(author) from quotes where removed is null and author != 'mr. fritters' group by author order by count(author) desc"
            sel_facts = "select d.author, count(d.author) from factdata d, facts f where d.author != 'mikey' and d.author != 'mr. fritters' and d.removed is null and d.`trigger` = f.target and f.locked > -1 and f.`trigger` = f.`target` group by author order by count(author) desc"
            
            sel_items = "select author, count(author) from items where author != 'mr. fritters' and author != 'mikey' group by author order by count(author) desc"
            
            self.doSQL(sel_quoted)
            quoted_rows = self.sql.fetchall()
            self.doSQL(sel_quotes)
            quotes_rows = self.sql.fetchall()
            self.doSQL(sel_facts)
            fact_rows = self.sql.fetchall()  
            self.doSQL(sel_items)
            items_rows = self.sql.fetchall()                                 
                
            facts = getPos(fact_rows, who.lower())
            quoted = getPos(quoted_rows, who.lower())
            quotes = getPos(quotes_rows, who.lower())
            items = getPos(items_rows, who.lower())
            
            message = "Leaderboard stats for {0}: Facts Learned: {1}; Times Quoted: {2}; Quotes Remembered: {3}; Items Created: {4}"
            self.sendChat(room, message.format(who, facts, quoted, quotes, items))
            
    else:
        self.spoutFact(room, "varerror", user.nick)

'''Statistics about what the bot knows'''        
def cmd_common_stats(self, command, user, room):
    sel = "select count(1) from facts f where (select count(1) from factdata d where d.`trigger` = f.`trigger` and d.removed is null) > 0 and locked=0"
    self.doSQL(sel)
    facts = self.sql.fetchone()[0]
    
    sel = "select count(1) from factdata d, facts f where f.target = d.`trigger` and f.locked=0 and d.removed is null"
    self.doSQL(sel)
    factdata = self.sql.fetchone()[0]
    
    sel = "select count(1) from quotes where removed is null"
    self.doSQL(sel)
    quotes = self.sql.fetchone()[0]
    
    sel = "select distinct nick from quotes where removed is null"
    self.doSQL(sel)
    nicks = self.sql.rowcount
    
    sel = "select count(1) from items where removed is null"
    self.doSQL(sel)
    items = self.sql.fetchone()[0]
    
    message="I know {0} fact triggers, with a total of {1} factoids ({2:.2} factoids per trigger). I have remembered {3} quotes from {4} different people ({5:.2} quotes per person). I know of {6} different items.".format(facts, factdata, factdata/float(facts), quotes, nicks, quotes/float(nicks), items)
    self.sendChat(room, message)          
