from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict
import os
import shutil


@module.commands('print')
def printfun(bot, trigger):
    functionName = trigger.group(2).split()[0]

    pin = -1
    with SqliteDict(filename='lembrary/ws_' + trigger.nick + '.sqlite') as pinDict:
        if functionName in pinDict:
            pin = pinDict[functionName]
            
    with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) == 0:
            bot.reply(functionName + " not found.")
            return

        for (i, moduleName) in enumerate(fmDict[functionName]):
            with open('lembrary/' + moduleName + '.hs', 'r') as f:
                lines = f.read().splitlines()
                
                for l in lines[1:]:
                    if i == pin:
                        bot.reply(str(i) + "*: " + l)
                    else:
                        bot.reply(str(i) + " : " + l)

                        
@module.commands('pin')
def pin(bot, trigger):
    tokens = trigger.group(2).split()
    functionName = tokens[0]


    with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:

        with SqliteDict(filename='lembrary/ws_' + trigger.nick + '.sqlite') as pinDict:
            if not functionName in fmDict:
                bot.reply(trigger.group(2) + " not found.")
                return
                
            if len(tokens) > 1:
                index = int(tokens[1])
            else:
                index = len(fmDict[functionName]) - 1

            if len(fmDict[functionName]) <= index:
                bot.reply(trigger.group(2) + " not found.")
                return
            
            pinDict[functionName] = index
            pinDict.commit()
            bot.reply(functionName + " " + str(index) + " pinned.")


            
@module.commands('pins')
def pins(bot, trigger): 
    with SqliteDict(filename='lembrary/ws_' + trigger.nick + '.sqlite') as pinDict:
        ans = "Pins: "
        for k in pinDict.keys():
            ans += "(" + k + " " + str(pinDict[k]) + ") "
        bot.reply(ans)

@module.commands('new_workspace')
def newpins(bot, trigger):
    saveWorkspace(bot, trigger)
    os.remove('lembrary/ws_' + trigger.nick + '.sqlite')
    bot.reply('Workspace cleared.')
   

@module.commands('save_workspace')
def saveWorkspace(bot,trigger):
    dest = trigger.nick + "_" + str(int(1000*time.time())) 
    shutil.copy("lembrary/ws_" + trigger.nick + ".sqlite",
                "lembrary/savedWs_" + dest + + ".sqlite")
    bot.reply("Saved workspace: " + dest)
        
    
@module.commands('load_workspace')
def loadWorkspace(bot, trigger):
    dest = trigger.group(2)
    shutil.copy("lembrary/savedWs_" + dest + + ".sqlite",
                "lembrary/ws_" + trigger.nick + ".sqlite")
    bot.reply("Loaded workspace: " + dest)
            
        
        
# TODO: mutual recursion?    
@module.commands('eval', 'let')
def eval(bot, trigger):
    expr = trigger.group(2)        
    
    if trigger.group(1) == 'eval':
        tokens = re.split('\W+', expr)
    else:
        eqSign = expr.index('=')
        tokens = re.split('\W+', expr[eqSign:])
        
    imports = []
    
    with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:
        for t in tokens:
            if t in fmDict:
                with SqliteDict(filename='lembrary/ws_' + trigger.nick + '.sqlite') as pinDict:
                    if t in pinDict:
                        imports.append(fmDict[t][pinDict[t]])
                    else:
                        imports.append(fmDict[t][-1])


    if trigger.group(1) == 'eval':
        moduleName = "Eval_" + trigger.nick + "_" + str(int(1000*time.time()))
    else:
        moduleName = "Fun_" + trigger.nick + "_" +  str(int(1000*time.time()))

    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    contents = "module " + moduleName + " where \n" 
    for i in imports:
        contents += "import " + i + "\n"

    if trigger.group(1) == 'eval':
        contents += "main = print $ " + expr + "\n"
    else:
        contents += expr + "\n"
        
    path = 'lembrary/' + moduleName + '.hs'    
    with open(path, "w+") as f:
        print("FILE CREATED: " + path)
        f.write(contents)

    if trigger.group(1) == 'eval':
        cmd = 'runghc'
    else:
        cmd = 'ghc'
        
    result = subprocess.run([cmd, '-ilembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans = '   '.join(lines)
    bot.reply(ans)
    

    if trigger.group(1) == 'let':
        functionName = expr.split()[0]
        with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:
            if not functionName in fmDict:
                fmDict[functionName] = []
            modList = fmDict[functionName]
            modList.append(moduleName)
            fmDict[functionName] = modList
            fmDict.commit()


    
                


    
    
