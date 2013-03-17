'''
Created on 10.11.2012

@author: hm
'''
import unittest, os.path
from source.sqlite3db import SqLite3Db
from source.pyygle import Logger

class Test(unittest.TestCase):
#    def __init__(self):
#        self._db = None
#        pass
    def init(self):
        self._logger = Logger('/tmp/test.log')
        self._dbName = '/tmp/sqlite3test.db'
        
    def connect(self):
        self.init()
        db = SqLite3Db(self._dbName, self._logger)
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
        db.putChapter('chapter1', 'Demo-Header', 'Chapter 1 This is an example of a good text', 20)
        db.putWord(db.normalizeWord('Chapter'))
        db.putWord(db.normalizeWord('1'))
        db.putWord(db.normalizeWord('This'))
        db.putWord(db.normalizeWord('is'))
        db.putWord(db.normalizeWord('an'))
        db.putWord(db.normalizeWord('example'))
        db.putWord(db.normalizeWord('of'))
        db.putWord(db.normalizeWord('a'))
        db.putWord(db.normalizeWord('good'))
        db.putWord(db.normalizeWord('text'))
        db.putChapter('chapter2', 'Demo-2', 'Chapter 2 This is an example of a bad text', 10)
        db.putWord(db.normalizeWord('Chapter'))
        db.putWord(db.normalizeWord('2'))
        db.putWord(db.normalizeWord('This'))
        db.putWord(db.normalizeWord('is'))
        db.putWord(db.normalizeWord('an'))
        db.putWord(db.normalizeWord('example'))
        db.putWord(db.normalizeWord('of'))
        db.putWord(db.normalizeWord('a'))
        db.putWord(db.normalizeWord('bad'))
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
        self.assertEquals(13, statistic._words)
        db.close()

    def checkChapter(self, chapters):
        count = 0
        for chapter in chapters:
            if chapter._anchor == 'chapter1':
                self.assertEqual(chapter._pureText, 
                    'Chapter 1 This is an example of a good text')
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
                    'Chapter 2 This is an example of a bad text')
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
        return count
        
    def test30Find(self):
        db = self.connect()
        if True:
            phrases = ('Chapter', '=a', 'text')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(3, count)

            phrases = ('Chapter', '=a', 'text', '-bad')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(2, count)

            phrases = ('=good t', 'or', 'bad')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(2, count)

            phrases = ('=good x', 'or', 'bad')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(1, count)

            phrases = ('-good', 'text', 'example')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(1, count)

        if False:
            phrases = ('(', 'good', 'or', 'bad', ')', 'and', 'example')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(2, count)
    
            phrases = ('(', 'good', '|', 'bad', ')', 'example')
            chapters = self._db.find(phrases, 0, 100)
            self.assertNotEqual(None, chapters)
            count = self.checkChapter(chapters)
            self.assertEqual(2, count)

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
        
    def test70writeWords(self):
        db = self.connect()
        filename = '/tmp/words_test_01.txt'
        db.writeWords(filename, True)
        fp = open(filename)
        lines = fp.readlines()
        self.assertEquals("1\t1\t0\n", lines[0])
        self.assertEquals(14, len(lines))
        self.assertEquals("this\t2\t0\n", lines[-1])
        
if __name__ == "__main__":
    
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()