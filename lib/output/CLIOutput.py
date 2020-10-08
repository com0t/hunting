from lib.utils.TerminalSize import get_terminal_size
import threading, sys, platform, time
from colored import fg, bg, attr

class CLIOutput(object):
    def __init__(self):
        self.lastLength = 0
        self.lastOutput = ''
        self.lastInLine = False
        self.mutex = threading.Lock()
        self.blacklists = {}
        self.mutexCheckedPaths = threading.Lock()
        self.basePath = None
        self.errors = 0

    def inLine(self, string):
        self.erase()
        sys.stdout.write(string)
        sys.stdout.flush()
        self.lastInLine = True

    def erase(self):
        if platform.system() == 'Windows':
            csbi = GetConsoleScreenBufferInfo()
            line = "\b" * int(csbi.dwCursorPosition.X)
            sys.stdout.write(line)
            width = csbi.dwCursorPosition.X
            csbi.dwCursorPosition.X = 0
            FillConsoleOutputCharacter(STDOUT, ' ', width, csbi.dwCursorPosition)
            sys.stdout.write(line)
            sys.stdout.flush()

        else:
            sys.stdout.write('\033[1K')
            sys.stdout.write('\033[0G')

    def newLine(self, string):
        if self.lastInLine == True:
            self.erase()

        if platform.system() == 'Windows':
            sys.stdout.write(string)
            sys.stdout.flush()
            sys.stdout.write('\n')
            sys.stdout.flush()

        else:
            sys.stdout.write(string + '\n')

        sys.stdout.flush()
        self.lastInLine = False
        sys.stdout.flush()


    def lastPath(self, path, index, length):
        with self.mutex:
            percentage = lambda x, y: float(x) / float(y) * 100

            x, y = get_terminal_size()

            message = '{0:.2f}% - '.format(percentage(index, length))

            if self.errors > 0:
                message += Style.BRIGHT + Fore.RED
                message += 'Errors: {0}'.format(self.errors)
                message += Style.RESET_ALL
                message += ' - '

            message += 'Last request to: {0}'.format(path)

            if len(message) > x:
                message = message[:x]

            self.inLine(message)
    
    def checking(self, domain, index, length):
        with self.mutex:
            percentage = lambda x, y: float(x) / float(y) * 100

            x, y = get_terminal_size()

            message = fg('yellow')+'{0:.2f}% - '.format(percentage(index, length))+attr('reset')
            message += 'Checking: {0}'.format(domain)

            if len(message) > x:
                message = message[:x]

            self.inLine(message)