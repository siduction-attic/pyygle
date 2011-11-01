'''
Created on 20.11.2012

@author: hm
'''
import unittest
from searchengine import SearchEngine , cmpTuples

class DummyDb:
    def __init__(self, wordlist):
        self._wordList = wordlist
        
    def getRelatedWords(self, word):
        return word + '|' + self._wordList
    
class Logger:
    def log(self):
        pass

class SearchEngineTest(unittest.TestCase):


    def test10BuildExcerpt(self):
        db = DummyDb(None)
        engine = SearchEngine(db)
        engine._lengthOfTheSpot = 10

        text = '123456789_123 abcd X a b c d e f'
        index = text.index('X')
        length = len('X')
        phrase = engine.buildExcerpt(index, length, text)
        self.assertEquals('abcd X a b', phrase)

        text = "123456789_123 a X abcd de\nfhhi"
        index = text.index('X')
        length = len('X')
        phrase = engine.buildExcerpt(index, length, text)
        self.assertEquals('a X abcd', phrase)

        engine._lengthOfTheSpot = 40
        #              123456789 123456789 123456789 1
        text = 'Muell. Hier steht das Zauberwort in einem langen Satz, der nie endet.'
        index = text.index('Zauberwort')
        length = len('Zauberwort')
        phrase = engine.buildExcerpt(index, length, text)
        self.assertEquals(' Hier steht das Zauberwort in einem langen Satz', phrase)

        engine._lengthOfTheSpot = 15
        text = '12345 XXX abc defghijklmnopqrst'
        index = text.index('XXX')
        length = len('XXX')
        phrase = engine.buildExcerpt(index, length, text)
        self.assertEquals('12345 XXX abc', phrase)

    def test20findFirstHitOfTheWord(self):
        db = DummyDb('Y|XX')
        engine = SearchEngine(db)
        engine._lengthOfTheSpot = 10

        text = '123456789_123 abcd X a b c d e f'
        (position, length, wordList) = engine.findFirstHitOfTheWord('x', text)
        self.assertEquals(1 , length)
        self.assertEqual(19, position)
        self.assertEqual('x|Y|XX', wordList)
 
    def test30cmpTuples(self):
        self.assertTrue(cmpTuples((1, 3), (2, 1)) < 0)
        self.assertTrue(cmpTuples((3000, 3), (4, 1)) > 0)
        self.assertEquals(0, cmpTuples((3000, 3), (3000, 1)))
        
    def test40joinHits(self):
        db = DummyDb('Y|XX')
        engine = SearchEngine(db)
        engine._lengthOfTheSpot = 10
        x = ((1, 3, 'x'), (15, 4, 'y'), (20, 1, 'x'))
        x2 = engine.joinHits(x)
        self.assertEquals(2, len(x2))
        self.assertEquals(x2[0][0], 1)
        self.assertEquals(x2[0][1], 3)
        self.assertEquals(x2[1][0], 15)
        self.assertEquals(x2[1][1], 6)
        
    def test50findHits(self):
        db = DummyDb('Z')
        engine = SearchEngine(db)
        engine._lengthOfTheSpot = 10
        words = ('a', '123', 'f')
        title = 'Header'
        link = 'http://sidu-manual/index.php/why.htm'
        text = '123 45 6789_1 abcd X a b c d e f'
        doc = 'test_01.htm'
        html = engine.findHits(words, text, title, doc, link)
        print html
        html2 = '''<p class="sm_link"><a href="http://sidu-manual/index.php/why.htm">Header</a></p>
<p class="sm_doc">test_01.htm</p>
<p class="sm_hit"><b>123</b> 45 6789_1</p>
<p class="sm_hit">abcd X <b>a</b> b c d e <b>f</b></p>
'''
        self.assertEquals(html, html2)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBuildExcerpt']
    unittest.main()