'''
Created on 14.11.2012

@author: hm
'''
import unittest
from source.xmlparser import XmlParser
from source.pyygle import Logger

class DummyDb:
    def __init__(self):
        self._chapters = dict()
        self._words = dict()
        self._docs = dict()
        
    def putChapter(self, anchor, title, text, rating):
        self._chapters[anchor] = text
      
    def putWord(self, word, dummy = True):  
        self._words[word] = 1
    
    def normalizeWord(self, word):
        return word.lower()
    
    def contains(self, word):
        rc = word in self._words
        return rc
    
    def putDocument(self, link, date, docType, size):
        self._docs[link] = docType

class Test(unittest.TestCase):


    def testUnescape(self):
        self._logger = Logger('/tmp/test.log')
        self._parser = XmlParser(self._logger)
        parser = self._parser
        self.assertEquals('1 < 2', parser.unescape('1 &lt; 2'))
        self.assertEquals('2>1', parser.unescape('2&gt;1'))
        self.assertEquals('Hinz&Co', parser.unescape('Hinz&amp;Co'))
        self.assertEquals('"Go" he said', parser.unescape('&quot;Go&quot; he said'))
        self.assertEquals('<>&"Text', 
            parser.unescape('<html><body>&lt;&gt;&amp;&quot;Text</body></html>'))
        
    def testHandleChapter(self):
        db = DummyDb()
        logger = Logger('/tmp/test.log')
        parser = XmlParser(logger)
        xml = '''<h2 id="c1"><a name="x1" />Test</h1>
        <!-- No comment --><p>This is a test.</p>
        '''
        parser.scanXmlChapter(xml, db)
        self.assertEqual("Test\n This is a test.\n ", db._chapters['x1'])
        self.assertTrue(db.contains('test'))
        self.assertTrue(db.contains('this'))
        self.assertTrue(db.contains('is'))
        self.assertTrue(db.contains('a'))

    def testParse(self):
        db = DummyDb()
        logger = Logger('/tmp/test.log')
        parser = XmlParser(logger)
        xml = '''<html><body><a name=start><p>Intro:</a> &lt;example&gt;</p>
        <h1 id="c1"><a name="x1" />Test</h1>
        <!-- No comment --><p>This is a test.</p>
        <H2><a name="h2">Header2</a></H2>
        <div>Remember it!</div>
        <h3>header3</h3>
        <h1><a name="h1-2">Header1</a></H2>
        <div>Important!</div>
        </body></html>
        '''
        parser.scanXmlDocument(xml, '2012-11-14 03:04:12', '//test.html', db)
        self.assertEqual(2, db._docs['//test.html'])
        self.assertEqual("Intro: <example> ", db._chapters['start'])
        self.assertEqual('Test This is a test. ', db._chapters['x1'])
        self.assertEqual("Header2 Remember it! header3 ", db._chapters['h2'])
        self.assertTrue(db.contains('test'))
        self.assertTrue(db.contains('this'))
        self.assertTrue(db.contains('is'))
        self.assertTrue(db.contains('a'))
        self.assertTrue(db.contains('intro'))
        self.assertTrue(db.contains('header1'))
        self.assertTrue(db.contains('important'))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testParser']
    unittest.main()
