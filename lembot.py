from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict
import os
import shutil


@module.commands('info')
def info(bot,trigger):
    """
    Prints information about commands.  Example: ".info eval" prints information about the "eval" command. 
    """
    cmds = ["eval", "let", "show", "show_all", "pin", "pins", "save_pins", "load_pins", "clear_pins", "info"]
    if trigger.group(2):
        c = trigger.group(2).lower().strip()
        if c in cmds:
            bot.reply(globals()[c].__doc__)
    else:
        bot.say("Commands: " + ", ".join(cmds))
        bot.say('Type ".info <command>" for more information about a specific command.')

        
@module.commands('show_all')
def show_all(bot, trigger):
    """
    Shows all definitions of a given function name. An asterisk denotes a pin.
    """
    if trigger.group(2):
        functionName = trigger.group(2).split()[0]
    else:
        bot.reply("Example: '.show_all x' prints all definitions of functions named 'x'")

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

            
@module.commands('show')
def show(bot, trigger):
    """ 
    Show the currently active definition of a function name.  This is the pinned definition if it exists.  Otherwise, it is the last-defined definition.
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
    Pins a name to a specified definition.  Example: suppose '.show_all x' outputs three definitions "0: x = -1", "1: x = 2", and "2: x = 5". Then ".pin x 0" will make all (non-shadowed) occurrences of "x" evaluate to -1.  
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
    Prints all of your currently active pins. Type ".info pin" for more information about pins.
    """
    with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        ans = "Pins: "
        for k in pinDict.keys():
            ans += "(" + k + " " + str(pinDict[k]) + ") "
        bot.reply(ans)

@module.commands('clear_pins')
def new_pins(bot, trigger):
    """
    Clears all pins after saving a backup.  Type ".info pin" for more information about pins.
    """
    save_pins(bot, trigger)
    os.remove('/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite')
    bot.reply('Workspace cleared.')
   

@module.commands('save_pins')
def save_pins(bot,trigger):
    """
    Saves your current pins.  Type ".info pin" for more information about pins.
    """
    dest = trigger.nick + "_" + str(int(1000*time.time()))
    shutil.copy("/home/haskell/lembrary/pins/" + trigger.nick + ".sqlite",
                "/home/haskell/lembrary/savedPins/" + dest + ".sqlite")
    bot.reply("Saved workspace: " + dest)
        
    
@module.commands('load_pins')
def load_pins(bot, trigger):
    """
    Load previously saved pins.  Type ".info pin" for more information about pins.
    """
    dest = trigger.group(2)
    shutil.copy("/home/haskell/lembrary/savedPins/" + dest + ".sqlite",
                "/home/haskell/lembrary/pins/" + trigger.nick + ".sqlite")
    bot.reply("Loaded workspace: " + dest)
            
        
    
@module.commands('eval')
def eval(bot, trigger):
    """
    Evaluate an expression in Haskell.  Can use previously ".let"-defined functions. Example: ".eval 2 + 3".
    """
    expr = trigger.group(2)                   
    imports = []
    
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        tokens = set(re.split('\W+', expr))
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

        
    cmd = 'runghc2'
            
    result = subprocess.run([cmd, '-ilembrary',  path], timeout=5, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans = '   '.join(lines)
    bot.reply(ans)
    

@module.commands('let')
def let(bot, trigger):
    """
    Define a function in Haskell notation. Example: ".let cat x y = x ++ y" concatenates strings.
    """
    expr = trigger.group(2)

    
    eqSign = expr.index('=')

    args = expr[:eqSign].split()

    if "System" in re.split('\W+', expr[:eqSign]):
        bot.reply("Illegal keyword: 'System'")
        return

    functionName = args[0]
    
    imports = []
    
    with SqliteDict(filename='/home/haskell/lembrary/fn_mod_dict.sqlite') as fmDict:
        tokens = set(re.split('\W+', expr[eqSign:]))
        for t in tokens:
            if t in fmDict and not t in args:
                with SqliteDict(filename='/home/haskell/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
                    if t in pinDict:
                        imports.append(fmDict[t][pinDict[t]])
                    else:
                        imports.append(fmDict[t][-1])

        if functionName in fmDict:
            moduleName = "Def_" + functionName + "_" +  str(len(fmDict[functionName])) 
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
    result = subprocess.run([cmd, '-rtsopts', '-i/home/haskell/lembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()

    ans = '   '.join(lines)
    bot.reply(ans)

    

    
                


    
    
