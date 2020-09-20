from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict
import os
import shutil
import random
import os.path

@module.commands('import')
def importC(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return


    with open("/lembrary/imports/" + trigger.nick  + ".txt", "a+") as f:
        f.write("import " + trigger.group(2) + "\n")
        bot.reply("Imported.")

@module.commands('imports')
def imports(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    with open("/lembrary/imports/" + trigger.nick  + ".txt", "a+"):
        pass

    bot.reply("Imports: ")
    
    with open("/lembrary/imports/" + trigger.nick  + ".txt", "r") as f:
        lines = f.read().splitlines()
        for l in lines:
            bot.reply(l)

            
@module.commands('unimport')
def unimport(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    term = trigger.group(2).strip()

    contents = ""

    with open("/lembrary/imports/" + trigger.nick  + ".txt", "a+"):
        pass
    
    with open("/lembrary/imports/" + trigger.nick  + ".txt", "r") as f:
        lines = f.read().splitlines()

        for l in lines():
            if not term in l:
                contents += l + "\n"
            
    with open("/lembrary/imports/" + trigger.nick  + ".txt", "w+") as f:
        f.write(contents)            


@module.commands('saveimports')
def saveimports(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return
    

    dest = trigger.nick + "_" + str(int(1000*time.time()))
    shutil.copy("/lembrary/imports/" + trigger.nick + ".txt",
                "/lembrary/savedImports/" + dest + ".txt")
    bot.reply("Saved imports: " + dest)

    
@module.commands('loadimports')
def loadimports(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    
    dest = trigger.group(2)

    if re.search(r'\W', dest) != None:
        bot.reply('Imports not found.')
    return

    shutil.copy("/lembrary/savedImports/" + dest + ".txt",
                "/lembrary/imports/" + trigger.nick + ".txt")
    bot.reply("Loaded imports: " + dest)
    
    
@module.commands('clearimports')
def clearimports(bot, trigger):
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return


    saveimports(bot, trigger)
    os.remove('/lembrary/imports/' + trigger.nick + '.txt')
    bot.reply('Imports cleared.')

    

@module.commands('info')
def info(bot,trigger):
    """
    Prints information about commands.  Example: ".info eval" prints information about the "eval" command. 
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    cmds = ["eval", "let", "show", "showall", "pin", "pins", "savepins",
            "loadpins", "clearpins", "info", "update", "type"]
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
        index = -1


    if pinH(function, index, trigger.nick):
        bot.reply(function + " " + str(index) + " pinned.")
    else:
        bot.reply("Pin failed: " + function + " " + str(index))

@module.commands('unpin')
def unpin(bot, trigger):
    """
    Unpins a definition from a name. See also: pin.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    savepins(bot, trigger)
    functions = trigger.group(2).split()
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:

            for function in functions:
                if not function in fmDict:
                    bot.reply("Name not found: " + function)
                else:
                    pinDict.pop(function)
                    pinDict.commit()
                    bot.reply(function + " unpinned.")
            


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
    bot.reply('Pins cleared.')
   

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
    bot.reply("Saved pins: " + dest)
        
    
@module.commands('loadpins')
def loadpins(bot, trigger):
    """
    Load previously saved pins.  Type ".info pin" for more information about pins.
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    
    dest = trigger.group(2)
    
    if re.search(r'\W', dest) != None:
        bot.reply('Pins not found.')
    return

    shutil.copy("/lembrary/savedPins/" + dest + ".sqlite",
                "/lembrary/pins/" + trigger.nick + ".sqlite")
    bot.reply("Loaded pins: " + dest)

@module.commands('type')
def type(bot, trigger):
    
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    expr = trigger.group(2)
    _, _, index = process("e = " + expr, trigger.nick)
    
    path = '/lembrary/Def_e_' + str(index)  + '.hs'    
    cmd = ['ghc', '-i/lembrary', path, "-e", ":t " + expr]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans =  '   '.join(lines)

    bot.reply(ans)
    

def process(expr, nick):
    function, args, tokens = exprData(expr)
    imports = getImports(tokens, nick)
    ans, index = makeFile(function, expr, imports)
    return ans, function, index



# Update pins in a module
def processM(module, nick, depth, fmDict, pinDict):
    expr, imports, otherImports = moduleData(module)
    function, args, tokens = exprData(expr)

    print("Processing imports...")
    for t in tokens:
        if t in fmDict:
            if t in pinDict:
                imports[t] = fmDict[t][pinDict[t]]
            elif (t in imports) and (depth > 0):
                _, _, index = processM(imports[t], nick, depth - 1, fmDict, pinDict)
                imports[t] = fmDict[t][index]

    print("Making file...")
    totalImports = otherImports + "\n"
    
    for i in imports.values():
        totalImports += "import " + i + "\n"
        
    ans, index = makeFile(function, expr, totalImports)
    return ans, function, index

    
def makeFile(function, expr, imports):
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        if function in fmDict:
            index = len(fmDict[function])
        else:
            index = 0

    module = "Def_" + function + "_" +  str(index)
    contents = "module " + module + " where \n" 
    contents += imports + "\n"

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

    # Sopel must be run from /lembrary for this to work
    subprocess.run(["git", "add", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.run(["git", "commit", "-m", "Auto"],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.run(["git", "push"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
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
    ans, _, _ = process("main = print (" + expr + ")", trigger.nick)
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
    """
    Update function name based on pins.  Typical workflow: ".clearpins, .pin x <num>, .update y"
    """
    if re.search(r'\W', trigger.nick) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return
    
    args = trigger.group(2).split()
    function = args[0]
    module = getModule(function, trigger.nick)
    recursionDepth = 100
    if len(args) == 2:
        recursionDepth = int(args[1])

    print("Processing update...")
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + trigger.nick + '.sqlite') as pinDict:
            ans, function, index = processM(module, trigger.nick, recursionDepth, fmDict, pinDict)

    if pinH(function, index, trigger.nick):
        bot.reply(ans)
    else:
        bot.reply("Update failed.")


## FIXME: need to make sure processM imports work (dict vs string). Also pins, etc
def moduleData(module):
    path = '/lembrary/' + module + '.hs'
    print("Opening " + path)
    otherImports = ""
    
    with open(path, "r") as f:
        contents = f.read()
        print("Contents: \n" + contents)

        lines = contents.splitlines()
        i = 0
        imports = dict()
        while not '=' in lines[i]:
            if 'import Def_' in lines[i]:
                module = lines[i].split(" ")[1]
                function = module.split("_")[1]
                imports[function] = module
                print("Import added: " + function + ":" + module)
            elif 'import' in lines[i]:
                otherImports += lines[i] + "\n"
                
            i += 1
            if i >= len(lines):
                print("Malformed file.")
                return 
                    
        expr = "\n".join(lines[i:])

        print("Imports: " + str(imports))
        print("Expr: " + str(expr))
        return expr, imports, otherImports



def exprData(expr):
    print("Parsing expression...")
    eqSign = expr.index('=')
    args = expr[:eqSign].split()

    keywords = ["case","class","data","default","deriving","do","else","forall"
                ,"if","import","in","infix","infixl","infixr","instance","let","module"
                ,"newtype","of","qualified","then","type","where","_"
                ,"foreign","ccall","as","safe","unsafe"]

    function = ""
    
    for a in args:
        if not a in keywords:
            function = a
            break

    #FIXME: bot not in scope, add another return value
    if not function:
        bot.reply('Illegal function name: ' + args[0])
        return

    if re.search(r'\W', function) != None:
        bot.reply(
            'Illegal function name: only alphanumerics and underscores allowed')
        return
            
    allTokens = set(re.split('\W+', expr[eqSign:]))
    tokens = allTokens.difference(set(args))
    
    return function, args, tokens

def getImports(tokens, nick):
    imports = ""
    path = "/lembrary/imports/" + nick  + ".txt"
    if os.path.isfile(path):
        with open(path, "r") as f:
            imports = f.read()
        
    with SqliteDict(filename='/lembrary/fn_mod_dict.sqlite') as fmDict:
        with SqliteDict(filename='/lembrary/pins/' + nick + '.sqlite') as pinDict:
            for t in tokens:
                if t in fmDict:
                    if t in pinDict:
                        imports += "import " + fmDict[t][pinDict[t]] + "\n"
                    else:
                        imports += "import " + fmDict[t][-1] + "\n"

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
        




