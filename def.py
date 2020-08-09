from sopel import module
import time
import re
import subprocess


@module.commands('let')
def fundef(bot, trigger):
    function = trigger.group(2)
    moduleName = trigger.nick + str(int(1000*time.time()))
    if re.search(r'\W', moduleName) != None:
        bot.reply('Illegal nick: only alphanumerics and underscores allowed')
        return

    path = '/home/a/lembrary/' + moduleName + '.hs'
    print("FILE CREATED: " + path)
    
    f = open(path, "w+")
    f.write("module " + moduleName + " where\n")
    f.write(function + "\n")
    f.close()

    result = subprocess.run(['ghc', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    bot.reply(result.stdout)




    

    
    
