from IPython import embed
import gensafeprime


def RSAGeneratePrimes(n):
    p = gensafeprime.generate(n)
    q = gensafeprime.generate(n)
    return (p, q)

def storeSecret(secret_file, p, q):
    f = open(secret_file, "w")
    s = "p="+str(p)+"\n"
    s += "q="+str(q)+"\n"
    f.write(s)
    f.close()
    return

def loadSecret(secret_file):
    f = open(secret_file)
    p = 0
    q = 0
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        if line[0] == "p":
            p = int(line[2::])
        elif line[0] == "q":
            q = int(line[2::])
    return (p, q)



class Command():
    def __init__(self, string, handler):
        self.string = string
        self.handler = handler
    def match(self, test_string):
        return test_string == self.string
    def handle(self, tail):
        return self.handler(tail)

def checkArgNum(args, num):
    if len(args) < num:
        print("Error! Too few arguments, expected {}, received {}".format(num, len(args)))
        return False
    elif len(args) > num:
        print("Error! Too many arguments, expected {}, received {}".format(num, len(args)))
        return False
    else:
        return True


def printer(arg):
    print(arg)

def setSecretFile(args):
    global secret_file
    if not checkArgNum(args, 1):
        return
    secret_file = args[0]


def main():
    main_commands = []
    main_commands.append(Command("set", printer))
    while True:
        commandStr = raw_input("CNSProj$ ")
        commandItems = commandStr.strip().split()
        if len(commandItems) == 0:
            continue
        command = commandItems.pop(0)
        for c in main_commands:
            if c.match(command):
                c.handle(commandItems)
                break



if __name__ == "__main__":
    #main()

    p, q = RSAGeneratePrimes(128)
    print((p, q))
    embed()
