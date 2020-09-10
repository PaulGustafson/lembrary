from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict
import os
import shutil
import random


@module.commands('info')
def info(bot,trigger):
    """
    Prints information about commands.  Example: ".info eval" prints information about the "eval" command. 
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    cmds = ["eval", "let", "show", "show_all", "pin", "pins", "save_pins", "load_pins", "clear_pins", "info", "update"]
    if trigger.group(2):
        c = trigger.group(2).lower().strip()
        if c in cmds:
            bot.reply(globals()[c].__doc__)
    else:
        bot.say("Commands: " + ", ".join(cmds))
        bot.say('Type ".info <command>" for more information about a specific command.')

        
@module.commands('showall')
def showall(bot, trigger):
    """
    Shows all definitions of a given function name. An asterisk denotes a pin.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    if trigger.group(2):
        function = trigger.group(2).split()[0]
    else:
        bot.reply("Example: '.showall x' prints all definitions of functions named 'x'")

    pin = -1
    with SqliteDict(filename='/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        if function in pinDict:
            pin = pinDict[function]
            
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not function in fmDict or len(fmDict[function]) == 0:
            bot.reply(function + " not found.")
            return

        for (i, module) in enumerate(fmDict[function]):
            with open('/lembrary/' + module + '.hs', 'r') as f:
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
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    function = trigger.group(2).split()[0]
    
    pin = -1
    with SqliteDict(filename='/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        if function in pinDict:
            pin = pinDict[function]
            
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not function in fmDict or len(fmDict[function]) == 0:
            bot.reply(function + " not found.")
            return

        module = fmDict[function][pin]
        with open('/lembrary/' + module + '.hs', 'r') as f:
            lines = f.read().splitlines()
            
            bot.reply(lines[-1])

                        
                        
@module.commands('pin')
def pin(bot, trigger):
    """
    Pins a name to a specified definition.  Example: suppose '.showall x' outputs three definitions "0: x = -1", "1: x = 2", and "2: x = 5". Then ".pin x 0" will make all (non-shadowed) occurrences of "x" evaluate to -1.  
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    tokens = trigger.group(2).split()
    function = tokens[0]
    if len(tokens) > 1:
        index = int(tokens[1])
    else:
        bot.reply("Pin index required.")
        return


    if pinH(function, index, trigger.nick):
        bot.reply(function + " " + str(index) + " pinned.")
    else:
        bot.reply("Pin failed: " + function + " " + str(index))
        


def pinH(function, index, nick):
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + nick + '.sqlite') as pinDict:
            if not function in fmDict or len(fmDict[function]) <= index:
                return False
            
            while index < 0:
                index += len(fmDict[function])

            pinDict[function] = index
            pinDict.commit()
            return True
        
    return False
    


            
@module.commands('pins')
def pins(bot, trigger):
    """
    Prints all of your currently active pins. Type ".info pin" for more information about pins.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    with SqliteDict(filename='/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
        ans = "Pins: "
        for k in pinDict.keys():
            ans += "(" + k + " " + str(pinDict[k]) + ") "
        bot.reply(ans)

        
@module.commands('clearpins')
def clearpins(bot, trigger):
    """
    Clears all pins after saving a backup.  Type ".info pin" for more information about pins.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    savepins(bot, trigger)
    os.remove('/lembrary/pins/' + trigger.nick + '.sqlite')
    bot.reply('Workspace cleared.')
   

@module.commands('savepins')
def savepins(bot, trigger):
    """
    Saves your current pins.  Type ".info pin" for more information about pins.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    
    dest = trigger.nick + "_" + str(int(1000*time.time()))
    shutil.copy("/lembrary/pins/" + trigger.nick + ".sqlite",
                "/lembrary/savedPins/" + dest + ".sqlite")
    bot.reply("Saved workspace: " + dest)
        
    
@module.commands('loadpins')
def loadpins(bot, trigger):
    """
    Load previously saved pins.  Type ".info pin" for more information about pins.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    
    dest = trigger.group(2)
    shutil.copy("/lembrary/savedPins/" + dest + ".sqlite",
                "/lembrary/pins/" + trigger.nick + ".sqlite")
    bot.reply("Loaded workspace: " + dest)


def process(expr, nick):
    function, args, tokens = exprData(expr)
    imports = getImports(tokens, nick)
    ans, index = makeFile(function, expr, imports)
    return ans, function, index



# Update pins in a module
def processM(module, nick, depth=0, fmDict, pinDict):
    expr, imports = moduleData(module)
    function, args, tokens = exprData(expr)

    print("Processing imports...")
    for t in tokens:
        if t in fmDict:
            if t in pinDict:
                imports[t] = fmDict[pinDict[t]]
            elif t in imports and depth > 0:
                processM(imports[t], nick, depth - 1, fmDict, pinDict)

    print("Making file...")
    ans, index = makeFile(function, expr, imports.values())
    return ans, function, index

    
def makeFile(function, expr, imports):
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        if function in fmDict:
            index = len(fmDict[function])
        else:
            index = 0

    module = "Def_" + function + "_" +  str(index)
    contents = "module " + module + " where \n" 
    for i in imports:
        contents += "import " + i + "\n"

    contents += expr + "\n"
        
    path = '/lembrary/' + module + '.hs'    
    with open(path, "w+") as f:
        print("FILE CREATED: " + path)
        f.write(contents)

    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not function in fmDict:
            fmDict[function] = []
        modList = fmDict[function]
        modList.append(module)
        fmDict[function] = modList
        fmDict.commit()

    if function == "main":
        cmd = ['sandbox','runghc', '-i/lembrary',  path]
    else:
        cmd = ['ghc', '-i/lembrary',  path]
        
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans =  '   '.join(lines)

    return ans, index



@module.commands('eval')
def eval(bot, trigger):
    """
    Evaluate an expression in Haskell.  Can use previously ".let"-defined functions. Example: ".eval 2 + 3".
    """

    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    expr = trigger.group(2)                   
    ans, _, _ = process("main = print $ " + expr, trigger.nick)
    bot.reply(ans)


@module.commands('let')
def let(bot, trigger):
    """
    Define a function in Haskell notation. Example: ".let cat x y = x ++ y" concatenates strings.
    """

    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return
    
    expr = trigger.group(2)
    ans, function, index  = process(expr, trigger.nick)
    if pinH(function, index, trigger.nick):
        bot.reply(ans)
    else:
        bot.reply("Definition failed.")

@module.commands('update')
def update(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return
    
    args = trigger.group(2).split()
    function = args[0]
    module = getModule(function, trigger.nick)
    recursionDepth = 0
    if len(args) == 2:
        recursionDepth = args[1]

    print("Processing update...")
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + nick + '.sqlite') as pinDict:
            ans, function, index = processM(module, trigger.nick, recursionDepth, fmDict, pinDict)

    if pinH(function, index, trigger.nick):
        bot.reply(ans)
    else:
        bot.reply("Update failed.")



def moduleData(module):
    path = '/lembrary/' + module + '.hs'
    with open(path, "r") as f:
        contents = f.read()

        lines = contents.splitlines()
        i = 0
        imports = dict()
        while not '=' in lines[i]:
            if 'import' in lines[i]:
                module = lines[i].split(" ")[1]
                function = module.split("_")[1]
                imports[function] = module
                    
                i += 1
                if i >= len(lines):
                    return 
                    
        expr = "\n".join(lines[i:])

        return expr, imports



def exprData(expr):
    eqSign = expr.index('=')
    args = expr[:eqSign].split()
    function = args[0]
    if re.search(r'\W', function) != None:
        bot.reply(
            'Illegal function name: only alphanumerics and underscores allowed')
        return
    allTokens = set(re.split('\W+', expr[eqSign:]))
    tokens = allTokens.difference(set(args))
    
    return function, args, tokens

def getImports(tokens, nick):
     with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + nick + '.sqlite') as pinDict:
            imports = []
            for t in tokens:
                if t in fmDict:
                    if t in pinDict:
                        imports.append(fmDict[t][pinDict[t]])
                    else:
                        imports.append(fmDict[t][-1])
            return imports
    

def getModule(f, nick):
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + nick + '.sqlite') as pinDict:
            if f in fmDict:
                if f in pinDict:
                    module = fmDict[f][pinDict[f]]
                else:
                    # TODO: find a better way to pick defaults
                    module = fmDict[f][-1]
                return module
            
    raise Exception('Module not found for ' + f)
        




