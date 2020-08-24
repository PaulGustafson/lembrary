from sopel import module
import time
import re
import subprocess
from sqlitedict import SqliteDict




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

            for l in lines[1:]:
                bot.reply(l)
        
    
    
@module.commands('eval', 'let')
def eval(bot, trigger):
    expr = trigger.group(2)
    tokens = re.split('\W+', expr)

    imports = []
    
    with SqliteDict(filename='/home/a/lembrary/fn_mod_dict.sqlite') as fmDict:
        for t in tokens:
            if t in fmDict:
                imports.append(fmDict[t][-1])

    if trigger.group(1) == 'eval':
        moduleName = "Eval_" + trigger.nick + "_" + str(int(1000*time.time()))
    else:
        moduleName = "Fun_" + trigger.nick + "_" +  str(int(1000*time.time()))

    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    contents = "module " + moduleName + " where\n" 
    for i in imports:
        contents += "import " + i + "\n"

    if trigger.group(1) == 'eval':
        contents += "main = print $ " + expr + "\n"
    else:
        contents += expr + "\n"
        
    path = '/home/a/lembrary/' + moduleName + '.hs'    
    with open(path, "w+") as f:
        print("FILE CREATED: " + path)
        f.write(contents)

    if trigger.group(1) == 'eval':
        cmd = 'runghc'
    else:
        cmd = 'ghc'
        
    result = subprocess.run([cmd, '-i/home/a/lembrary',  path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = result.stdout.decode('UTF-8').splitlines()
    ans = '   '.join(lines)
    bot.reply(ans)
    

    if trigger.group(1) == 'let':
        functionName = expr.split()[0]
        with SqliteDict(filename='/home/a/lembrary/fn_mod_dict.sqlite') as fmDict:
            if not functionName in fmDict:
                fmDict[functionName] = []
            modList = fmDict[functionName]
            modList.append(moduleName)
            fmDict[functionName] = modList
            fmDict.commit()


    
                


    
    
