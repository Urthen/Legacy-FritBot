#!/usr/bin/python

from twisted.internet import defer, reactor
from twisted.words.protocols.jabber import jid
from wokkel import muc
import re, random, sys, datetime, time
import commands.core, commands.common, commands.users, commands.facts, commands.items, commands.quotes, commands.bonus

#TODO: Migrate this to a common module
def cleanup(string):
    return re.sub("[\\.,\\?!'\"-_=\\\\\\*]", '', string.lower()).strip()
    
#TODO: Figure out if I actually need this function...    
def timeparse(s):
    return datetime.datetime(int(s[0:4]),int(s[5:7]),int(s[8:10]),int(s[11:13]), int(s[14:16]), int(s[17:19]))
    
#Setup some global variables
#TODO: Make these externally configurable    
rawverblist = ["is", "isn\'?t", "has", "are", "hates", "loves", "likes", "aren\'?t", "said", "says"]
accepted_name_list = ["fritbot", "fribot", "flirtbot", "fritbut", "fritbutt", "bucket", "fuckbucket", "firbot", "fb"]
special_facts = ["itemtake", "itemswap", "varerror", "varinsult", "varfunny", "varawkward", "varinsult"]
item_max = 12

class FritBot(muc.MUCClient):   
    
    '''Initialize the bot: Only called on first bot start up.'''
    def __init__(self, server, roomlist, nick, rulerlist, connection):
        muc.MUCClient.__init__(self)        
        
        #Register chat triggers
        self.chat_triggers = [
            commands.facts.chatFactCheck,
            commands.bonus.chatReplacements,
        ]
        
        #Set up initial data
        self.server = server
        self.roomlist = roomlist
        self.roomdata = {}
        self.nickname = nick
        self.rulerlist = rulerlist
        self.last_triggered = None
        self.when_triggered = datetime.datetime.today()
        self.verblist = "(" + ')|('.join(rawverblist) + ")"
                
        if self.nickname.lower() not in accepted_name_list:
            accepted_name_list.append(self.nickname.lower())
        accepted_names = '|'.join('({0})'.format(x) for x in accepted_name_list)
        
        #Compile some regexes
        #TODO: Remove these, do something better
        self.static_rex = {
            'ex': re.compile(r"\bex", re.I),
            'anex': re.compile(r"\ban ex", re.I),
            'command': re.compile(r'\A@?(%s)[,:]?\s(?P<command>.*)' % accepted_names, re.I),
            'awkward': re.compile(r'\A\.\.+\s*\Z', re.I),
            'funny': re.compile(r'\A(((ha)|(he)|(lo)){2,}|(lo+l))', re.I),
            'learn': re.compile(' ({0}|(<.*>)) '.format(self.verblist), re.I),
            'question': re.compile(r'\? *\Z'),
            }    
        
        #Set command order
        self.commands = [        
            (re.compile(r'\Ashut ?down', re.I), commands.core.cmd_core_shutdown, 0),
            (re.compile('\Ainsult', re.I), commands.bonus.cmd_bonus_insult, 2),
            (re.compile('\A(((go)|(jump)) ((to)|(in))|(join))', re.I), commands.core.cmd_core_jump, 1),
            (re.compile('\A(leave)', re.I),  commands.core.cmd_core_leave, 0),
            (re.compile('\A([^\.\?]*) ((or)|(vs)) ([^\.\?]+)[\?\.]?', re.I), commands.bonus.cmd_bonus_or, 2),
            (re.compile('((shut( the fuck)? ?up)|(quiet)|(go away))', re.I), commands.core.cmd_core_quiet, 0),
            (re.compile('((come back)|(wake up)|(\Atalk))', re.I), commands.core.cmd_core_wakeup, 1),
            (re.compile('\Aremember', re.I), commands.quotes.cmd_quotes_remember, 1),
            (re.compile('\Aquote ', re.I), commands.quotes.cmd_quotes_quote, 2),
            (re.compile('\A(un)?forget', re.I), commands.common.cmd_common_forget, 2),
            (re.compile(' alias ', re.I), commands.facts.cmd_facts_alias, 2),
            (re.compile('\Aquotestats', re.I), commands.quotes.cmd_quotes_quotestats, 2),
            (re.compile('\Awhat( the fuck)? was that', re.I), commands.facts.cmd_facts_whatwas, 2),
            (re.compile('\Astats', re.I), commands.common.cmd_common_stats, 2),
            (re.compile('\A(un)?lock', re.I), commands.facts.cmd_facts_lock, 2),
            (re.compile('leader', re.I), commands.common.cmd_common_leaderboard, 2),
            (re.compile('(become)|(ghost)', re.I), commands.core.cmd_core_ghost, 2),
            (re.compile('(backpack)|(inventory)', re.I), commands.items.cmd_items_backpack, 2),
            (re.compile('\A((google)|(search)) ', re.I), commands.bonus.cmd_bonus_google, 1),
            (re.compile('\Aauth ', re.I), commands.core.cmd_core_auth, 0),
            (re.compile('\Aseen ', re.I), commands.users.cmd_users_seen, 1),
            (re.compile('mad ?lib', re.I), commands.bonus.cmd_bonus_madlib, 2),            
            (self.static_rex['question'], commands.bonus.cmd_bonus_answer, 2),            
            (re.compile('(have)|(take)', re.I), commands.items.cmd_items_have, 2),            
            (self.static_rex['learn'], commands.facts.cmd_facts_learn, 1),
        ]              
        
        #Setup SQL
        #TODO: Don't use a persistent connection, use new connection each use.
        self.sqlconnection = connection
        self.sql = self.sqlconnection.cursor()        
       
    '''Join rooms on connect/reconnect.'''
    def initialized(self):
        for room, nick in self.roomlist.items():
            self.joinRoom(room, nick)
        
    '''Perform post-join configuration.
    Configure rooms that need to be before others can join.'''
    @defer.inlineCallbacks
    def initRoom(self, room):
        if int(room.status) == muc.STATUS_CODE_CREATED:
            userhost = self.rjid(room).userhost()
            config_form = yield self.getConfigureForm(userhost)
            
            # set config default
            config_result = yield self.configure(userhost)  
            
        reactor.callFromThread(self.fbInitRoom, room)
        
    '''Joined a room, get the configuration or create default configuration'''
    def fbInitRoom(self, room):   
        sel = "select id, auth from rooms where name=#{0}#".format(room.name)
        self.doSQL(sel)
        row = self.sql.fetchone()   
        if row is not None:
            print "Getting settings for", room.name
            room.fbid = row[0]
            room.auth = row[1]
        else:
            print "Creating new room in DB:", room.name
            ins = "insert into rooms (name) values (#{0}#)".format(room.name)
            self.doSQL(ins)           

            
            sel = "select id from rooms where name=#{0}#".format(room.name)
            self.doSQL(sel)
            row = self.sql.fetchone()   
            room.fbid = row[0]
            room.auth = 0
        
        if room.name not in self.roomdata:
            self.roomdata[room.name] = {}
            room.data = self.roomdata[room.name]
            room.data['history'] = []
            room.data['responses'] = {}
            room.data['squelched'] = 0
        else:
            room.data = self.roomdata[room.name]                        
            
        self.roomlist[room.name] = room.nick 
        
    '''Update user nicknames, if appropriate'''
    def doNickUpdate(self, user, room):    
        
        sel = "select id from nicks where nick=#{0}# and user=#{1}# and room=#{2}#".format(user.nick, user.fb_user_id, room.fbid)
        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is not None:
            user.fb_nick_id = row[0]
        else:
            #TODO: Do this correctly (Don't select the ID immediately after inserting! Theres a better way, but I'm too lazy to fix it right now
            ins = "insert into nicks (user, nick, room) values (#{0}#, #{1}#, #{2}#)".format(user.fb_user_id, user.nick, room.fbid)
            self.doSQL(ins)
            sel = "select id from nicks where nick=#{0}# and user=#{1}# and room=#{2}#".format(user.nick, user.fb_user_id, room.fbid)
            self.doSQL(sel)
            row = self.sql.fetchone()
            user.fb_nick_id = row[0]       
        
    '''Called when a user joins a room'''
    def userJoinedRoom(self, room, user):
        sel = "select id from users where resource=#{0}#".format(user.resource)
        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is not None:
            user.fb_user_id = row[0]            
            
        else:
            #TODO: Do this correctly (Don't select the ID immediately after inserting! Theres a better way, but I'm too lazy to fix it right now
            ins = "insert into users (resource) values (#{0}#)".format(user.resource)
            self.doSQL(ins)
            sel = "select id from users where resource=#{0}#".format(user.resource)
            self.doSQL(sel)
            row = self.sql.fetchone()
            user.fb_user_id = row[0]
            
        #Call a moment later to eliminate a race condition    
        reactor.callLater(0.5, self.doNickUpdate, user, room)
            
    '''Called when a user changes their nickname'''
    def userUpdatedStatus(self, room, user, show, status):
        self.doNickUpdate(user, room)
        
    '''Return the JID of the given room'''
    def rjid(self, room):
        return jid.internJID(room.name + '@conference.bazaarvoice.com/' + room.nick)
        
    '''Perform an SQL command.'''    
    def doSQL(self, cmd, reprimand = True):
        #TODO: Don't use persistent connections
        cmd = cmd.replace('"', "'").replace(';','').replace('#','"')
        self.sql.execute(cmd)
        return True
        
    '''Join a room'''
    def joinRoom(self, room, nick):
        self.join("conference.bazaarvoice.com", room, nick).addCallback(self.initRoom)                           
        
    '''Leave a room'''
    def leaveRoom(self, chan):
        cid = jid.internJID(chan + '@conference.bazaarvoice.com/' + self.roomlist[chan])
        self.leave(cid)
        del self.roomlist[chan]
        
    '''Return squelched status of given room'''
    def squelched(self, room):                        
        if (time.time() > room.data['squelched'] and room.data['squelched'] > -1) and room.auth == 2:        
            return False                           
        return True        
        
    '''Returns a random person in a room'''
    def getSomeone(self, room):
        k = []       
        for key in room.roster.keys():
            if key.lower() != room.nick.lower():
                k.append(key)
                
        who = k[random.randrange(0, len(k))]
            
        return who
    
    '''Returns a random item.'''
    def getSomething(self, restrict=False, owned=False):
        #TODO: Decouple this and migrate to commands.items
        if restrict:            
            if owned:
                sel = "select name from items where backpack = 1 and removed is null order by rand() limit 1"
            else:
                sel = "select name from items where backpack = 0 and removed is null order by rand() limit 1"
        else:
            sel = "select name from items where backpack != 2 and removed is null order by rand() limit 1"    
        self.doSQL(sel)
        row = self.sql.fetchone()
        
        if row is None: #backup in case the original call doesn't return anything
            if restrict or owned:
                item = self.getSomething()
            else:
                return "something completely different" #complete failback to prevent infinite loops in case someone managed to zero out the entire inventory
        else:
            item = row[0]
            
        return item
            
    '''Adds a given item'''
    def getItem(what):
        #TODO: Decouple this and migrate to commands.items
        upd = "update items set backpack=1 where name=#{0}#".format(what)
        self.doSQL(upd)
            
    '''Send a message to a room'''
    def sendChat(self, room, message, slow = False):
        #TODO: Message modes (uppercase, l337, etc...)
        if slow:
            delay = random.random() * 3. + 1.5
            print "{0} ({1:.1}s delay): {2}".format(room.name, delay, message)
            reactor.callLater(delay, self.groupChat, self.rjid(room), message)
        else:            
            print "{0}: {1}".format(room.name, message)            
            reactor.callLater(0.2, self.groupChat, self.rjid(room), message)    
            
    '''Set up response callbacks'''
    def awaitResponse(self, room, function, user = None):
        #user None means allow from any user. any other value indicates that response is only allowed from that user.
        if user is not None:
            print "Registered callback response for room {0}, user {1}".format(room.name, user.nick)
            room.data['responses'][user.fb_user_id] = function
        else:
            print "Registered callback response for room {0}, any user".format(room.name)
            room.data['responses'][0] = function
            
    '''Triggered when a group chat is recieved in a room the bot is in'''        
    def receivedGroupChat(self, room, user, body):
        if user is None or user.nick.lower() == room.nick.lower():
            return     
            
        body = body.encode('utf-8')                      
            
        #TODO: Check if this user is completely ignored.
        
        print "Processing body:", room.name, user.nick, user.fb_user_id, user.fb_nick_id, body            
                
        upd = "update nicks set lastseen=now(), activity=activity + 1, said=#{1}# where id = #{0}#".format(user.fb_nick_id, body)
        self.doSQL(upd)          
        
        #commands come first and shouldn't be recorded in history
        rex = self.static_rex['command'].search(body)
        if rex is None:
            rex = re.search(r'\A@?(%s)[,:]?\s(?P<command>.*)' % room.nick, body, re.I)
        if rex is not None:
            command = rex.group("command")
            if self.doCommand(command, user, room):
                return
                
        #record all other history
        history = (user, body)   
        if len(room.data['history']) > 40:
            room.data['history'] = room.data['history'][1:]
        room.data['history'].append(history)
                
        for trigger in self.chat_triggers:
            if trigger(self, body, user, room):
               break 
                                                                                                                                               
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
        
    '''Perform token replacements'''
    def iterFact(self, room, fact):
        #TODO: Make this function not quite so stupid
        if "$something" in fact:
            fact = re.sub(r'\$something', self.getSomething(), fact, 1)
            return fact, True, None
        if "$inventory" in fact:
            fact = re.sub(r'\$inventory', self.getSomething(True, True), fact, 1)
            return fact, True, None
        if "$giveitem" in fact:
            item = self.getSomething(True, True)
            fact = re.sub(r'\$giveitem', item, fact, 1)
            upd = "update items set backpack=2 where name=#{0}#".format(item)
            self.doSQL(upd)
            upd = "update items set backpack=0 where name=#{0}#".format(item)
            return fact, True, upd
        if "$takeitem" in fact:
            item = self.getSomething(True)
            fact = re.sub(r'\$takeitem', item, fact, 1)
            upd = "update items set backpack=2 where name=#{0}#".format(item)
            self.doSQL(upd)
            upd = "update items set backpack=1 where name=#{0}#".format(item)
            return fact, True, upd
        if "$someone" in fact:
            fact = re.sub(r'\$someone', self.getSomeone(room), fact, 1)
            return fact, True, None
        
        
        return fact, False, None
        
    '''Send a response to a given fact'''
    def spoutFact(self, room, target, who, what=""):
        #TODO: Decouple and migrate to commands.facts
        
        if self.squelched(room):
            return False
            
        sel = 'select verb, fact, id from factdata where removed is null and `trigger` = #{0}# order by rand() limit 1;'.format(target)
          
        if not self.doSQL(sel, False):
            return
        row = self.sql.fetchone()
        if row is not None:
            verb = row[0]
            fact = row[1]
            self.last_triggered = row[2]
            fact = re.sub(r'\$who', who, fact)
            
            if what == "":
                what = self.getSomething()
            fact = re.sub(r'\$(what)', what, fact)                        
            
            i = 0
            cont = True
            upds = []
            while cont and i < 10:
                fact, cont, upd = self.iterFact(room, fact)
                if upd is not None:
                    upds.append(upd)
            for upd in upds:
                self.doSQL(upd)
                
            if verb == "reply" or target in special_facts:
                self.sendChat(room, fact, True)
            else:
                self.sendChat(room, "{0} {1} {2}".format(target, verb, fact), True)                         
                                
            return True
        
        return False
            
    '''User has addressed the bot, attempt to perform a command.'''
    def doCommand(self, command, user, room):                    
        for compair in self.commands:
            if compair[0].search(command) is not None and compair[2] <= room.auth:
                compair[1](self, command, user, room)
                return True
                        
        if 0 in room.data['responses'] and room.data['responses'][0] is not None:
                print "Global response callback triggered in {0} by {1}.".format(room.name, user.nick)
                room.data['responses'][0](self, command, user, room)
                room.data['responses'][0] = None
                return True        
        elif user.fb_user_id in room.data['responses'] and room.data['responses'][user.fb_user_id] is not None:
                print "Specific response callback triggered in {0} by {1}.".format(room.name, user.nick)
                room.data['responses'][user.fb_user_id](self, command, user, room)
                room.data['responses'][user.fb_user_id] = None
                return True            
        
        return False        
