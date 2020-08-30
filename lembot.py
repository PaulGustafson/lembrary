from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict
import os
import shutil


@module.commands('printall')
def printall(bot, trigger):
    """
    Prints all definitions of a given function name. An
    asterisk denotes a pin.

    """
    functionName = trigger.group(2).split()[0]

    pin = -1
    with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        if functionName in pinDict:
            pin = pinDict[functionName]
            
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) == 0:
            bot.reply(functionName + " not found.")
            return

        for (i, moduleName) in enumerate(fmDict[functionName]):
            with open('/home/haskell/lembrary/' + moduleName + '.hs', 'r') as f:
                lines = f.read().splitlines()

                if i == pin:
                    bot.reply("(" + str(i) + ")*   " + lines[-1])
                else:
                    bot.reply("(" + str(i) + ")    " + lines[-1])

            
@module.commands('print')
def printFun(bot, trigger):
    """ 
    Prints the currently active definition of a function name.  This is
    the pinned definition if it exists.  Otherwise, it is the last-defined
    definition.
    """
    functionName = trigger.group(2).split()[0]
    
    pin = -1
    with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        if functionName in pinDict:
            pin = pinDict[functionName]
            
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) == 0:
            bot.reply(functionName + " not found.")
            return

        moduleName = fmDict[functionName][pin]
        with open('/home/haskell/lembrary/' + moduleName + '.hs', 'r') as f:
            lines = f.read().splitlines()
            
            bot.reply(lines[-1])

                        
                        
@module.commands('pin')
def pin(bot, trigger):
    """
    Pins a name to a specified definition.  
    """
    tokens = trigger.group(2).split()
    functionName = tokens[0]


    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:

        with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
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
    """
    Prints all of your currently active pins.
    """
    with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        ans = "Pins: "
        for k in pinDict.keys():
            ans += "(" + k + " " + str(pinDict[k]) + ") "
        bot.reply(ans)

@module.commands('clear_pins')
def new_pins(bot, trigger):
    """
    Clears all pins after saving a backup.
    """
    save_pins(bot, trigger)
    os.remove('/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite')
    bot.reply('Workspace cleared.')
   

@module.commands('save_pins')
def save_pins(bot,trigger):
    """
    Saves your current pins.
    """
    dest = trigger.nick + "_" + str(int(1000*time.time()))
    shutil.copy("/home/haskell/lembrary/pins/" + trigger.nick + ".sqlite",
                "/home/haskell/lembrary/savedPins/" + dest + ".sqlite")
    bot.reply("Saved workspace: " + dest)
        
    
@module.commands('load_pins')
def loadWorkspace(bot, trigger):
    """
    Load previously saved pins.
    """
    dest = trigger.group(2)
    shutil.copy("/home/haskell/lembrary/savedPins/" + dest + ".sqlite",
                "/home/haskell/lembrary/pins/" + trigger.nick + ".sqlite")
    bot.reply("Loaded workspace: " + dest)
            
        
    
@module.commands('eval')
def eval(bot, trigger):
    """
    Evaluate an expression.
    """
    expr = trigger.group(2)        
    

    tokens = re.split('\W+', expr)
            
    imports = []
    
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        for t in tokens:
            if t in fmDict:
                with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
                    if t in pinDict:
                        imports.append(fmDict[t][pinDict[t]])
                    else:
                        imports.append(fmDict[t][-1])


    moduleName = "Eval_" + trigger.nick + "_" + str(int(1000*time.time()))
    
    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    contents = "module " + moduleName + " where \n" 
    for i in imports:
        contents += "import " + i + "\n"

    contents += "main = print $ " + expr + "\n"
    
        
    path = '/home/haskell/lembrary/' + moduleName + '.hs'    
    with open(path, "w+") as f:
        print("FILE CREATED: " + path)
        f.write(contents)

        
    cmd = 'runghc'
            
    result = subprocess.run([cmd, '-ilembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans = '   '.join(lines)
    bot.reply(ans)
    

@module.commands('let')
def let(bot, trigger):
    """
    Define a function.
    """
    expr = trigger.group(2)        
    
    eqSign = expr.index('=')
    tokens = re.split('\W+', expr[eqSign:])
    functionName = expr[:eqSign].split()[0]
    
    imports = []
    
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        for t in tokens:
            if t in fmDict:
                with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
                    if t in pinDict:
                        imports.append(fmDict[t][pinDict[t]])
                    else:
                        imports.append(fmDict[t][-1])

        if functionName in fmDict:
            moduleName = "Def_" + functionName + "_" +  str(len(fmDict[functionName]))  #FIXME: not incrementing
        else:
            moduleName = "Def_" + functionName + "_0" 

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
        
    path = '/home/haskell/lembrary/' + moduleName + '.hs'    
    with open(path, "w+") as f:
        print("FILE CREATED: " + path)
        f.write(contents)

    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict:
            fmDict[functionName] = []
        modList = fmDict[functionName]
        modList.append(moduleName)
        fmDict[functionName] = modList
        fmDict.commit()

    cmd = 'ghc'    
    result = subprocess.run([cmd, '-i/home/haskell/lembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()

    ans = '   '.join(lines)
    bot.reply(ans)

    

    
                


    
    
