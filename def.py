from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict


@module.commands('let')
def fundef(bot, trigger):
    function = trigger.group(2)
    moduleName = trigger.nick + str(int(1000*time.time()))
    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    path = '/home/a/lembrary/' + moduleName + '.hs'
    print("FILE CREATED: " + path)
    
    with open(path, "w+") as f:
        f.write("module " + moduleName + " where\n")
        f.write(function + "\n")

    result = subprocess.run(['ghc', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    for l in lines:
        bot.reply(l)

    functionName = function.split()[0]
    with SqliteDict(filename='/home/a/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict:
            fmDict[functionName] = []
        modList = fmDict[functionName]
        modList.append(moduleName)
        fmDict[functionName] = modList
        fmDict.commit()


@module.commands('print')
def printfun(bot, trigger):
    functionName = trigger.group(2).split()[0]
    with SqliteDict(filename='/home/a/lembrary/fn_mod_dict.sqlite') as fmDict:
        if not functionName in fmDict or len(fmDict[functionName]) == 0:
            bot.reply(functionName + " not found.")
            return
        moduleName = fmDict[functionName][0]

        with open('/home/a/lembrary/' + moduleName + '.hs', 'r') as f:
            lines = f.read().splitlines()

            for l in lines:
                bot.reply(l)
        
    
    
@module.commands('eval')
def eval(bot, trigger):
    expr = trigger.group(2)
    tokens = re.split('\W+', expr)

    imports = []
    
    with SqliteDict(filename='/home/a/lembrary/fn_mod_dict.sqlite') as fmDict:
        for t in tokens:
            if t in fmDict:
                imports.append(fmDict[t][0])

    moduleName = "Eval" + trigger.nick + str(int(1000*time.time()))
    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    contents = "module " + moduleName + " where\n" 
    for i in imports:
        contents += "import " + i + "\n"

    contents += "main = print $ " + expr + "\n"
    path = '/home/a/lembrary/' + moduleName + '.hs'
    print("FILE CREATED: " + path)
    
    with open(path, "w+") as f:
        f.write(contents)
        
    result = subprocess.run(['runghc', '-i/home/a/lembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    for l in lines:
        bot.reply(l)



    


    
                


    
    
