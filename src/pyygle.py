#! /usr/bin/python
'''
Created on 04.11.2012

@author: hm
'''

import sys, os.path, time, re
import cProfile, pstats
sys.path.append('/usr/share/pyygle/src')
import sqlite3db
from filecrawler import FileCrawler, RExprDocFinder
from searchengine import SearchEngine

VERSION = '0.1 (2012.11.11)'
class Options:
    def __init__(self, progName):
        self._progName = progName
        self._logfile = '/tmp/pyyggle.log'
        self._db = '/var/lib/pyygle/default.db'
        self._verbose = True
        

def helpMe(opts, msg):
    '''Displays a description of the program and the error message.
    After that the program exits.
    @param opts: the options
    @param msg:  None or the error message 
    '''
    print '''pyyggle, a simple search engine (C) Hamatoma 2012 Version %s
usage: %s <global_opts> mode <args>
<mode>:
  db      adminstrates the database
  parse   traverse a file tree for indexing text files
  search  search in the database
<global_opts>:
  --db=<path>          name of the database. Default: /var/lib/pyyggle/pyyggle.db
  --logfile=<file>     name of the logfile. Default: /tmp/pyyggle.log
  --quiet              no logging of more info
<db-mode-args>:
  create               initializes the database: create the tables
  import-norm <file>   reads <file> and put the entries into the table normOfWord
  statistic            displays some statistic data
  export-raw-words <file> 
                       writes the table rawWord into <file>
<parse-mode-args>:
  fill-db [--add] [--no-ext-is-text] [<directory> [<pattern>]]
                       scans the directory and inserts the data into the db
    <directory>        the start of the file search. All subdirectories will be
                       inspected too. Default: the current directory
    <pattern>          pattern is a regular expression for the files to index
    --add              the directory data will be added: normally the db 
                       will be created first
    --no-ext-is-text   if there is no file extension the file is treated as a text file
<serch-mode-args>:
  <search-opts> <phrase_1> ...
  --url=<url>          the prefix of the links in the result file
  --output=<file>      the result will be written to this file. Default: stdout
  --browser=<browser>  the result will be shown with this browser
  --no-frame           the result has pure info, no html header
  <phrase_N>:          a word: no prefix
                       a excludes word: prefix '~'
                       an exact matching phrase:  prefix: '='
example for a search:   
burn =iso-file        finds the following chapter: "burn" finds "burned" too, "iso-file" must be exact.
   The downloaded file must be burned as an ISO-file. ....   
    ''' % (VERSION, os.path.basename(opts._progName))
    if msg != None:
        print '+++', msg
    if exit:
        sys.exit(1)
    
    

class Logger:
    '''Displays and stores messages.
    '''
    def __init__(self, logFile):
        'Constructor.'
        self._errors = 0
        self._logFile = logFile
        
    
    def log(self, msg):
        '''Displays a message.
        @param msg: the message to log
        '''
        print msg
        
    def error(self, msg):
        self.log('+++' + msg)

class Task:
    def __init__(self, opts, logger):
        self._logger = logger
        self._opts = opts
        self._dbStats = None
        self._db = None
        self._start = time.time()
        # a tuple: (keyword, value)
        self._currentOption = None
    
    def finish(self):
        if self._db != None:
            self._dbStats = self._db.getStatistic()
            self._db.close()
            if self._opts._verbose:
                print self.getDbStats()
    
    def getRunTime(self):
        duration = time.time() - self._start
        minutes = (int) (duration / 60)
        secs = int(duration % 60)
        msec = (int) (duration * 1000 % 1000)
        rc = "%d:%02d.%03d" % (minutes, secs, msec)
        return rc
    
    def getDbStats(self):
        stats = self._dbStats
        rc = ('%d doc(s), %d chapter(s), %d word(s), %d words in chapters, %d raw words'
              % (stats._docs, stats._chapters, stats._words, 
                 stats._wordsOfChapter, stats._rawWords))
        return rc
        
    def hasOption(self, argv, msgIfNone = None):
        '''Tests whether the first entry of argv is an option.
        If yes the option will be put to self._currentOption
        and removed from the argv
        @param argv: the argument vector
        @param msgIfNone: if not None and there is no value (no '=')
                        this error message will be shown
        @return: True: there is an option in self._currentOption
        '''
        self._currentOption = None
        if argv != None and len(argv) > 0 and argv[0].find('--') == 0:
            arg = argv.pop(0)
            keyword = None
            value = None
            ix = arg.find('=')
            if ix < 0:
                if msgIfNone != None:
                    helpMe(arg, msgIfNone + arg)
                keyword = arg[2:]
            else:
                keyword = arg[2:ix]
            value = None if ix < 0 else arg[ix+1:]
            self._currentOption = (keyword, value)
        return self._currentOption != None
        
class DbAdmin(Task):
    def __init__(self, opts, logger):
        Task.__init__(self, opts, logger)
        
    def run(self, opts, argv):
        if len(argv) == 0:
            helpMe(opts, 'missing <db_mode>')
        
        self._db = sqlite3db.SqLite3Db(opts._db, self._logger)
        dbMode = argv.pop(0)
        
        if dbMode == 'create':
            self._db.create()
        elif dbMode == 'statistic':
            self._dbStats = self._db.getStatistic()
            print self.getDbStats()
        else:
            helpMe(opts, 'unknown option for db: ')

class FileAdmin(Task):
    def __init__(self, opts, logger):
        Task.__init__(self, opts, logger)
        
    def run(self, opts, argv):
        if len(argv) == 0:
            helpMe(opts, 'missing <db_mode>')
        
        self._db = sqlite3db.SqLite3Db(opts._db, self._logger)
        mode = argv.pop(0)
        noExtensionIsText = False
        if mode == 'fill-db':
            create = True
            url = None
            while self.hasOption(argv):
                (keyword, value) = self._currentOption
                if keyword == 'add':
                    create = False
                elif keyword == 'no-ext-is-text':
                    noExtensionIsText = True
                elif keyword == 'url':
                    if value == None or len(value) == 0:
                        helpMe(opts, '--url=<url> needs a URL')
                    url = value
                else:
                    helpMe(opts, 'unknown option for fill-db: ' + keyword)
            if create and os.path.exists(opts._db):
                os.remove(opts._db)
            if not os.path.exists(opts._db):
                self._db.create()
            directory = '.' if len(argv) == 0 else argv.pop(0)
            crawler = FileCrawler(self._logger, opts._verbose)
            pattern = None if len(argv) == 0 else argv.pop(0)
            validator = RExprDocFinder(pattern, True, noExtensionIsText)
            crawler.scanDocumentTree(directory, validator, self._db, url)
            self._dbStats = self._db.getStatistic()
            if opts._verbose:
                info = os.stat(self._db._dbName)
                dbSize = 0 if info == None else info[6]
                msg = ('Scanned: %d dir(s) %d file(s) size: %.3f MiBytes db-size: %.3f MiByte time: %s'
                    % (crawler._dirCount, crawler._fileCount, crawler._mibytes,
                       dbSize / 1024.0 / 1024, self.getRunTime()))
                self._logger.log(msg)
        else:
            helpMe(opts, 'unknown <db_mode>: ' + mode)

class Search(Task):
    def __init__(self, opts, logger):
        Task.__init__(self, opts, logger)
        
    def run(self, opts, argv):
        if len(argv) == 0:
            helpMe(opts, 'missing arguments')
        
        self._db = sqlite3db.SqLite3Db(opts._db, self._logger)
        url = None
        output = None
        browser = None
        withFrame = True
        while self.hasOption(argv):
            (keyword, value) = self._currentOption
            if keyword == 'url':
                url = value
            elif keyword == 'output':
                output = value
            elif keyword == 'browser':
                browser = value
            elif keyword == 'no-frame':
                browser = value
            else:
                helpMe(opts, 'unknown option for search: ' + keyword)
        words = ()
        phrases = ()
        excludes = ()
        while len(argv) > 0:
            arg = argv.pop(0)
            prefix = arg[0:1]
            if prefix == '~':
                excludes += (arg[1:],)
            elif prefix == '=':
                phrases += (arg[1:],)
            else:
                words += (arg,)
        if len(words) + len(phrases) == 0:
            helpMe(opts, 'No search words or phrases given')
        engine = SearchEngine(self._db)
        html = engine.search(words, phrases, excludes, url, withFrame)
        if browser != None and output == None:
            output = '/tmp/pyygle_result.html'
        if output == None:
            print html
        else:
            fp = open(output, "w")
            fp.write(html)
            fp.close()
            if browser != None:
                cmd = browser + ' ' + output
                os.system(cmd)
        
class Pyygle(Task):
    def __init__(self):
        self._task = None
        
    def run(self, argv):
        opts = Options(argv.pop(0))
        while self.hasOption(argv, None):
            (keyword, value) = self._currentOption
            if keyword == 'db':
                if value == None or len(value) == 0:
                    helpMe("--db: empty db is not allowed")
                opts._db = value
            elif keyword == 'logfile':
                if value == None or len(value) == 0:
                    helpMe("--logfile: empty logfile is not allowed")
                opts._logfile = value
            elif keyword == 'quiet':
                opts._verbose = False
            else:
                helpMe(opts, 'unknown global option: ' + keyword)
            
        logger = Logger(opts._logfile)
        if len(argv) == 0:
            helpMe(opts, '<mode> expected')
        mode = argv.pop(0)
        if mode == 'db':
            self._task = DbAdmin(opts, logger)
        elif mode == 'parse':
            self._task = FileAdmin(opts, logger)
        elif mode == 'search':
            self._task = Search(opts, logger)
        else:
            helpMe(opts, 'unknown <mode>: ' + mode)
        if self._task != None:
            self._task.run(opts, argv)
            self._task.finish()

def profileIt():
    argv = re.split(r'\s', 'prog --db=/tmp/profile.db parse fill-db /home/wsl6/php/sidu-manual/static/de hd')
    prog = Pyygle()
    prog.run(argv) 

def profileMain():
    result = '/tmp/pyygle.prof.txt'
    cProfile.run('profileIt()', result)
    profile = pstats.Stats(result)
    profile.strip_dirs().sort_stats('time').print_stats(100)
    
if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 1 and argv[1] == 'profile':
        profileMain()
    else:
        prog = Pyygle()
        prog.run(argv)
