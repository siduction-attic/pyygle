'''
Created on 17.11.2012

@author: hm
'''
import unittest,os.path

import pyygle
from pyygle import Pyygle

class Test(unittest.TestCase):

    def buildFile(self, name, content):
        fp = open(name, "w");
        fp.write(content)
        fp.close
    def buildDir(self, name):
        if not os.path.exists(name):
            os.mkdir(name)
    def buildTree(self):
        base = '/tmp/pyygletest.tree/'
        self.buildDir(base)
        self.buildDir(base + 'xml')
        self.buildDir(base + 'txt')
        self.buildFile(base + 'xml/d1.htm',
            '<html><body><a name="start"><h1>Demo</h1>Alles geht!<p></body></html>')
        self.buildFile(base + 'txt/t1.txt',
            'Demo\nAuch einfache Texte funktionieren!')
        self.buildFile(base + 'muell.txt',
            'Muell! Nichts als Muell!')
        return base
  
    def checkStatistic(self, docs, chapters, words, rawWords, stats):
        self.assertEquals(docs, stats._docs)
        self.assertEquals(chapters, stats._chapters)
        self.assertEquals(words, stats._words)
        self.assertEquals(rawWords, stats._rawWords)
          
    def testDb(self):
        dbName = '/tmp/testpyggle.01.db'
        if os.path.exists(dbName):
            os.remove(dbName)
        logname = '/tmp/testpyggle.02.log'
        prog = Pyygle()
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'db', 'create']
        prog.run(argv)
        self.assertTrue(os.path.exists(dbName))
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'db', 'statistic']
        prog.run(argv)
        stats = prog._task._dbStats
        self.checkStatistic(0, 0, 0, 0, stats)

    def testFileCrawler(self):
        dbName = '/tmp/testpyggle.02.db'
        if os.path.exists(dbName):
            os.remove(dbName)
        logname = '/tmp/testpyggle.02.log'
        base = self.buildTree()
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'parse', 
            'fill-db', base, r'\d']
        prog = Pyygle()
        prog.run(argv)
        stats = prog._task._dbStats
        self.checkStatistic(2, 3, 7, 0, stats)

    def compareFiles(self, file1, file2):
        fp1 = open(file1)
        lines1 = fp1.readlines()
        fp1.close
        fp2 = open(file2)
        lines2 = fp2.readlines()
        fp2.close
        for no in xrange(len(lines1)):
            line1 = lines1[no]
            line2 = lines2[no]
            if line1 != line2:
                print file1, " / ", file2, "line:", no + 1,  "\n", line1, "\n", line2, "\n"
                self.assertEquals(line1, line2)
            
    def testSearch(self):
        dbName = '/tmp/pyygle-doc.db'
        logname = '/tmp/testpyggle.03.log'
        base = '../doc'
        base2 = '../debian'
        fnOutput = '/tmp/pyygle_test.03.htm'
        prog = Pyygle()
        
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'parse', 
            'fill-db', '--no-ext-is-text', base2]
        prog.run(argv)
        
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'parse', 
            'fill-db', '--add', base, r'[.]htm']
        prog = Pyygle()
        prog.run(argv)
        
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'search', 
            '--output=' + fnOutput, '--url=file://home/wsl6/py/pyygle/test/',
            'simple', 'search', 'normalized']
        prog = Pyygle()
        prog.run(argv)
        self.compareFiles(fnOutput, 'resources/pyygle_doc_01.html')

        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'search', 
            '--output=' + fnOutput, '--url=file://home/wsl6/py/pyygle/test/',
            'normalized']
        prog = Pyygle()
        prog.run(argv)
        self.compareFiles(fnOutput, 'resources/pyygle_doc_02.html')

    def writeFile(self, filename, content):
        fp = open(filename, "w")
        fp.write(content)
        fp.close()
        
    def testSearchQueryFile(self):
        dbName = '/tmp/pyygle-doc.db'
        logname = '/tmp/testpyggle.03.log'
        fnOutput = '/tmp/pyygle_test.04.htm'
        prog = Pyygle()
        fnQuery = '/tmp/pyygle_query_01.txt'
        
        self.writeFile(fnQuery, '''
db
or
database
and
word
-table
''')
        argv = ['pyygle.py', '--db=' + dbName, '--logfile=' + logname, 'search', 
            '--output=' + fnOutput, '--url=file://home/wsl6/py/pyygle/test/',
            '--no-frame', '--query=' + fnQuery]
        prog.run(argv)
        self.compareFiles(fnOutput, 'resources/pyygle_doc_03.html')
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDb']
    unittest.main()