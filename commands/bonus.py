import re, urllib, simplejson
from twisted.internet import reactor

'''Register functionality with the bot'''
def register(bot):
    commands = [cmd for cmd in globals() if 'cmd_' in cmd]
    for cmd in commands:
        bot.__dict__[cmd] = globals()[cmd]
     
'''Answer a question'''
#TODO: Better responses based on what type of question was asked (who, what, how, etc)
def cmd_bonus_answer(self, command, user, room):
    self.spoutFact(room, "varanswer", user.nick)   

'''Insult someone'''
#TODO: Change this to a factoid, because its stupid to have this hardcoded as a command.
def cmd_bonus_insult(self, command, user, room):
    if self.squelched(room):
        return
        
    rex = re.match(r'insult (.+)', command, re.I)
    if rex is None:
        self.sendChat(room, "Insult who, {0}?".format(user.nick))
    else:
        insultee = rex.group(1)
        if insultee == "me":
            insultee = user.nick
        elif insultee == "you" or insultee == "yourself":
            self.sendChat(room, "I'm not quite THAT stupid, {0}.".format(user.nick), True)
            return
             
        self.spoutFact(room, "varinsult", user.nick, insultee)   

'''Query google's json API'''
def cmd_bonus_google(self, command, user, room):
    rex = re.match("((google)|(search)) (?P<what>.*)", command, re.I)        

    if rex is not None:        
        query = urllib.urlencode({'q' : rex.group("what")})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' \
          % (query)
        search_results = urllib.urlopen(url)
        json = simplejson.loads(search_results.read())
        results = json['responseData']['results']
        title = results[0]['title']
        title = title.replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
        topresult = "{0}: {1}".format(title, results[0]['url'])
        topresult
        self.sendChat(room, topresult)
    else:
        self.sendChat(room, "Search for what exactly?")
        
'''Mad-lib mode'''
def cmd_bonus_madlib(self, command, user, room):
    sel = "select id, text from madlib where removed is null order by rand() limit 1"
    self.doSQL(sel)
    row = self.sql.fetchone()
    
    if row is None:
        self.sendChat(room, "Ok, some jerk forgot all the mad libs... *glares*")
        return
        
    self.sendChat(room, "Aww yeah! Mad lib mode: ACTIVATED! Prepare for some serious nonsense.")                    
    
        
    mid = row[0]
    text = row[1]
    
    #time to parse this shit       
    cursor = text.find("{")
    wordcount = 0
    wordslist = []
    while cursor > -1 and wordcount < 100:
        cend = text.find("}", cursor)
        
        word = text[cursor + 1:cend]
        
        #this IS how you do it in python, fuckers!
        try:
            int(word)
        except:               
            text = text[:cursor + 1] + str(wordcount) + text[cend:]
            wordslist.append(word)                              
            wordcount += 1
            
        cursor = text.find("{", cursor + 1)
        
    if len(wordslist) == 0:
        self.sendChat(room, "Hrm, looks like mad lib {0} is invalid. Go fix it and try again.".format(mid))
        return
        
    print wordslist
    print text                
    
    #handle responses
    def madlibSecondary(self, command, user, room):                         
        responses = room.data['madlib']['responses']
        wordslist = room.data['madlib']['list']
        responses.append(command)
        self.sendChat(room, "Ok, great! {0} gave me {1}. ({2}/{3})".format(user.nick, command, len(responses), len(wordslist)))
        
        if len(responses) == len(wordslist):
            text = room.data['madlib']['text']
            text = text.replace("{", "{0[").replace("}", "]}")
            print text, responses
            text = text.format(responses)
            reactor.callLater(2.0, self.sendChat, room, text)
        else:
            reactor.callLater(3.0, self.sendChat, room, "Please give me the following: {0}".format(wordslist[len(responses)]))
            reactor.callLater(3.0, self.awaitResponse, room, madlibSecondary)
        
    reactor.callLater(3.0, self.sendChat, room, "Please give me the following: {0}".format(wordslist[0]))
    reactor.callLater(3.0, self.awaitResponse, room, madlibSecondary)
    
    room.data['madlib'] = {'id': mid, 'text': text, 'list': wordslist, 'responses': []}
        

'''Select from a range of user-given options'''
def cmd_bonus_or(self, command, user, room):
    if self.squelched(room):
        return            
        
    if command[-1] == '?':
        command = command[0: len(command) - 1]
    choices = command.split(" or ")
    if random.random() > 0.2:
        choice = choices[random.randrange(len(choices))]
    else:
        if len(choices) == 2:
            choice = "Both!"
        else:
            choice = "All of the above!"
            
    message = "{0}: {1}".format(user.nick, choice.replace(r" \or ", " or "))
    self.sendChat(room, message, True)                
