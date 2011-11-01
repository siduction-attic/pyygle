'''
Created on 10.11.2012

@author: hm
'''
import unittest, os.path
import sqlite3db
import pyygle

class Test(unittest.TestCase):
#    def __init__(self):
#        self._db = None
#        pass
    def init(self):
        self._logger = pyygle.Logger('/tmp/test.log')
        self._dbName = '/tmp/sqlite3test.db'
        
    def connect(self):
        self.init()
        db = sqlite3db.SqLite3Db(self._dbName, self._logger)
        db._commitOften = False
        self._db = db
        return db

    def emptyDb(self):
        self.init()
        if os.path.exists(self._dbName):
            os.remove(self._dbName)
        db = self.connect()
        db.create()
        return db
    
    def testWord0Count(self):
        db = self.emptyDb()
        word = 'bob'
        for ix in range(5):
            db.putWord(word, ix < 0)
        self.assertEquals(5, db.getCountOfWord(word))
        db.close()
        
    def test10Creation(self):
        db = self.emptyDb()
        self.failUnless(os.path.exists(self._dbName))
        statistic = db.getStatistic()
        self.assertEquals(0, statistic._docs)
        self.assertEquals(0, statistic._chapters)
        self.assertEquals(0, statistic._words)
        db.close()

    def test20Populate(self):
        db = self.connect()
        db.putVariants('a', ('an', ))
        db.putDocTree('http://sidu-manual/index.php', '/usr/share/sidu-manual/static/de')
        db.putDocument('/tmp/docu1', '2012-11-11 8:00:00', 2, 123);
        db.putChapter('chapter1', 'Demo-Header', 'Chapter 1 This is an example of a text', 20)
        db.putWord(db.normalizeWord('Chapter'))
        db.putWord(db.normalizeWord('1'))
        db.putWord(db.normalizeWord('This'))
        db.putWord(db.normalizeWord('is'))
        db.putWord(db.normalizeWord('an'))
        db.putWord(db.normalizeWord('example'))
        db.putWord(db.normalizeWord('of'))
        db.putWord(db.normalizeWord('a'))
        db.putWord(db.normalizeWord('text'))
        db.putChapter('chapter2', 'Demo-2', 'Chapter 2 This is an example of a text', 10)
        db.putWord(db.normalizeWord('Chapter'))
        db.putWord(db.normalizeWord('2'))
        db.putWord(db.normalizeWord('This'))
        db.putWord(db.normalizeWord('is'))
        db.putWord(db.normalizeWord('an'))
        db.putWord(db.normalizeWord('example'))
        db.putWord(db.normalizeWord('of'))
        db.putWord(db.normalizeWord('a'))
        db.putWord(db.normalizeWord('text'))
        db.putDocument('/tmp/docu2', '2012-11-11 8:00:00', 2, 123);
        db.putChapter('chapter2-1', 'Demo 2-1', 'Chapter: Any other text', 30)
        db.putWord(db.normalizeWord('Chapter'))
        db.putWord(db.normalizeWord('Any'))
        db.putWord(db.normalizeWord('other'))
        db.putWord(db.normalizeWord('Text'))
        statistic = db.getStatistic()
        self.assertEquals(2, statistic._docs)
        self.assertEquals(3, statistic._chapters)
        self.assertEquals(11, statistic._words)
        db.close()

    def test30Find(self):
        db = self.connect()
        words = ('Chapter', 'text')
        phrases = (' ', 'a')
        chapters = self._db.find(words, phrases, True, None, 0, 100)
        count = 0
        for chapter in chapters:
            if chapter._anchor == 'chapter1':
                self.assertEqual(chapter._pureText, 
                    'Chapter 1 This is an example of a text')
                doc = chapter._document
                self.assertTrue(doc != None)
                self.assertEqual(doc._link, '/tmp/docu1')
                docTree = doc._docTree
                self.assertTrue(docTree != None)
                self.assertEqual('Demo-Header', chapter._title)
                self.assertEqual('http://sidu-manual/index.php', 
                   docTree._url)
                count += 1
            elif chapter._anchor == 'chapter2':
                self.assertEqual(chapter._pureText, 
                    'Chapter 2 This is an example of a text')
                self.assertEqual(chapter._document._link, '/tmp/docu1')
                self.assertEqual('Demo-2', chapter._title)
                count += 1
            elif chapter._anchor == 'chapter2-1':
                self.assertEqual(chapter._pureText, 'Chapter: Any other text')
                self.assertEqual(chapter._document._link, '/tmp/docu2')
                count += 1
                self.assertEqual('Demo 2-1', chapter._title)
            else:
                self.assertTrue(False)
        self.assertEqual(3, count)
        db.close()
    
    def test40Variants(self):
        db = self.connect()
        self.assertEquals(-1, db.getCountOfWord('-'))
        self.assertEquals(4, db.getCountOfWord('a'))
        db.close()
        
    def test50RawWords(self):
        db = self.connect()
        db.putRawWord('abc')
        db.putRawWord('abc')
        db.putRawWord('123')
        statistic = db.getStatistic()
        self.assertEquals(2, statistic._rawWords)
        db.close()
        
    def test60getRelatedWords(self):
        db = self.connect()
        db.putVariants('abc', ('ac', 'cba'))
        wordList = db.getRelatedWords('abc')
        self.assertTrue(wordList.find('abc') >= 0)
        self.assertTrue(wordList.find('ac') >= 0)
        self.assertTrue(wordList.find('cba') >= 0)
        wordList = db.getRelatedWords('ac')
        self.assertTrue(wordList.find('abc') >= 0)
        self.assertTrue(wordList.find('ac') >= 0)
        self.assertTrue(wordList.find('cba') >= 0)
        db.close()
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()