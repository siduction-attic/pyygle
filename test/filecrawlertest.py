'''
Created on 15.11.2012

@author: hm
'''
import unittest, os.path
from pyygle import Logger
from filecrawler import RExprDocFinder, FileCrawler;
import pyygle

class DummyXmlParser:
    def __init__(self):
        self._files = dict()
        self._chapters = list()
        
    def scanXmlDocument(self, xml, date, link, db):
        self._files[link] = 1
        
    def scanChapter(self, anchor, title, pureText, db):
        self._chapters.append(len(pureText))

class DummyDb:
    def __init__(self, storage):
        self._storage = storage
        
    def putDocument(self, link, date, docType, size):
        self._storage._files[link] = docType
        
    def putDocTree(self, url, dirName):
        self._path = dirName
           
class Test(unittest.TestCase):


    def testDocType(self):
        x = RExprDocFinder(None)
        extList = ('txt', 'pl', 'cpp', 'h', 'log', 'py', 'php', 'sh', 'conf', 'ini')
        for ext in extList:
            name = '/opt/abc.' + ext
            self.assertEqual(1, x.docType(name))
        extList = ('xhtml', 'htm', 'html', 'xml')
        for ext in extList:
            name = 'abc.' + ext
            self.assertEqual(2, x.docType(name), 'Name: ' + name)
        x = RExprDocFinder('[-_]de[.]conf$')
        name = 'conf/siguibui_DE.conf'
        self.assertEqual(1, x.docType(name))
        name = 'conf/siguibui-de.CONF'
        self.assertEqual(1, x.docType(name))
        name = 'conf/heide.conf'
        self.assertEqual(0, x.docType(name))

    def buildFile(self, name):
        fp = open(name, "w");
        fp.close
    def buildDir(self, name):
        if not os.path.exists(name):
            os.mkdir(name)
            
    def testFileCrawler(self):
        logger = pyygle.Logger("/tmp/test.log")
        base = '/tmp/test.crawler'
        self.buildDir(base)
        f1 = base + '/x1.xml'
        self.buildFile(f1)
        self.buildDir(base + "/dir1")
        f2 = base + '/dir1/x1.xhtml'
        self.buildFile(f2)
        f3 = base + '/dir1/x2.pl'
        self.buildFile(f3)
        d4 = base + "/dir1/dir2"
        self.buildDir(d4)
        f5 = base + "/dir1/dir2/a1.conf"
        self.buildFile(f5)
        f6 = base + "/dir1/dir2/a2.xml"
        self.buildFile(f6)
        
        crawler = FileCrawler(logger)
        parser =  DummyXmlParser()
        db = DummyDb(parser)
        crawler._parser = parser
        validator = RExprDocFinder(None)
        crawler.scanDocumentTree(base, validator, db, 'http://pyygle-test/index.php')
        self.assertTrue(f1 in parser._files)
        self.assertTrue(f2 in parser._files)
        self.assertTrue(f3 in parser._files)
        self.assertTrue(f5 in parser._files)
        self.assertTrue(f6 in parser._files)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDocType']
    unittest.main()