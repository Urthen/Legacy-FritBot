import re

'''Register functionality with the bot'''
def register(bot):
    commands = [cmd for cmd in globals() if 'cmd_' in cmd]
    for cmd in commands:
        bot.__dict__[cmd] = globals()[cmd]
    
'''List contents of the backpack'''
def cmd_items_backpack(self, command, user, room):
    backpack = []
    
    sel = "select name from items where backpack = 1 and removed is null order by name"
    self.doSQL(sel)
    row = self.sql.fetchone()
    while row is not None:
        backpack.append(row[0])
        row = self.sql.fetchone()
        
    if len(backpack) == 0:
        out = "My backpack is empty!"
    elif len(backpack) == 1:            
        out = "I have " + backpack[0]
    else:
        backpack[-1] = "and " + backpack[-1]               
        out = "I've got: " + ", ".join(backpack)
    
    self.sendChat(room, out)       

'''Get a new item'''
def cmd_items_have(self, command, user, room):
        rex = re.match("((have)|(take)) (?P<what>.*)", command, re.I)
        
        if rex is not None:
            what = rex.group("what")
            if len(what) < 4:
                self.sendChat(room, "Thats too small, {0}. Give me something with more letters!".format(user.nick))
                return
            
            if what=="something":
                what = self.getSomething(True)
            else:
                sel = "select removed from items where name=#{0}#".format(what)
                self.doSQL(sel)
                row = self.sql.fetchone()                                
            
                if row is None:
                    ins = "insert into items (name, created, author, backpack) values (#{0}#, now(), #{1}#, 2)".format(what, user.nick.lower()) 
                    self.doSQL(ins)
                elif row[0] is not None:
                    self.sendChat(room, "That item seems to have been explicitly forgotten. Try unforgetting it instead.")
                    return                    

            count = "select count(1) from items where backpack=1"
            self.doSQL(count)
            counted = int(self.sql.fetchone()[0])
            
            if counted > item_max:
                self.spoutFact(room, "itemswap", user.nick, what)
            else:
                self.spoutFact(room, "itemtake", user.nick, what)
                            
            upd = "update items set backpack=1 where name=#{0}#".format(what)
            self.doSQL(upd)                                            
            
        else:
            self.sendChat(room, "What did you want to give me, {0}?".format(user.nick))                    
