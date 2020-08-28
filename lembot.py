from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict


@module.commands('print')
def printfun(bot, trigger):
    functionName = trigger.group(2).split()[0]
    with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) == 0:
            bot.reply(functionName + " not found.")
            return

        for (i, moduleName) in enumerate(fmDict[functionName]):
            with open('lembrary/' + moduleName + '.hs', 'r') as f:
                lines = f.read().splitlines()

                for l in lines[1:]:
                    bot.reply(str(i) + ": " + l)

@module.commands('pin')
def pin(bot, trigger):
    tokens = trigger.group(2).split()
    functionName = tokens[0]


    with SqliteDict(filename='lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) <= index:
            bot.reply(functionName + " " + index + " not found.")
            return

        with SqliteDict(filename='lembrary/pins.sqlite') as pinDict:
            if not trigger.nick in pinDict:
                pinDict[trigger.nick] = [dict()]

            if len(tokens) > 1:
                index = int(tokens[1])
            else:
                index = len(fmDict[functionName]) - 1
    
            pinDict[trigger.nick][-1][functionName] = index

@module.commands('pins')
def pins(bot, trigger): 
    with SqliteDict(filename='lembrary/pins.sqlite') as pinDict:
        if not trigger.nick in pinDict:
            pinDict[trigger.nick] = [dict()]
                
        bot.reply("Pins " + str(len(pinDict[trigger.nick]) - 1) + " = " + str(pinDict[trigger.nick][-1]))

@module.commands('newpins')
def newpins(bot, trigger): 
    with SqliteDict(filename='lembrary/pins.sqlite') as pinDict:
        if not trigger.nick in pinDict:
            pinDict[trigger.nick] = [dict()]
        else:
            pinDict[trigger.nick].append(dict())
            
    pins(bot, trigger)

@module.commands('loadpins')
def loadpins(bot, trigger):
    tokens = trigger.group(2).split()
    pinIndex = int(tokens[0])
    if len(tokens > 1):
        nick = tokens[1]
    else:
        nick = trigger.nick
    
    with SqliteDict(filename='lembrary/pins.sqlite') as pinDict:
        if nick in pinDict and len(pinDict[nick]) > pinSetIndex:
            pins = pinDict[nick][pinSetIndex].copy()
            if not trigger.nick in pinDict:
                pinDict[trigger.nick] = [pins]
            else:
                pinDict[trigger.nick].append(pins)

    pins(bot, trigger)
            
        
        
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
                with SqliteDict(filename='lembrary/pins.sqlite') as pinDict:
                    if trigger.nick in pinDict and t in pinDict[trigger.nick]:
                        imports.append(fmDict[t][pinDict[trigger.nick]])
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


    
                


    
    
