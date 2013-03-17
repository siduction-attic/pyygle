'''
Created on 20.11.2012

@author: hm
'''
import re
import xml.sax.saxutils as saxutils

def cmpTuples(a, b):
    '''Compares two tuples  by the first element
    @param a: the first tuple
    @param b: the second tuple
    @return: < 0: a[0] < b[0]<br>
            0: a[0] == b[0]<br>
            > 0: a[0] > b[0]
    '''
    return a[0] - b[0]

class SearchEngine(object):
    '''
    Search for documents with given words and phrases
    and build a html result page. 
    '''


    def __init__(self, db):
        '''
        Constructor.
        @param db: the database with the search index
        '''
        self._db = db
        self._resultsPerPage = 5
        self._indexCurrentPage = 0
        self._pageNo = 0
        self._lengthOfTheSpot = 150
        self._rexprSeparator = re.compile(r'[:.!?\n]')
        self._rexprFirstWord = re.compile(r'^(\w+|\W+\w*)')
        self._rexprLastWord = re.compile(r'(\W*\w+|\W+)$')
     
    def buildExcerpt(self, index, length, text):
        '''Builds an excerpt from the text around the word at index.
        @param index: the index of the word in the result
        @param length: the length of the word
        @param text: the full text
        @return: a phrase around the given word
        '''
        lengthOfSpot = self._lengthOfTheSpot
        start = index - lengthOfSpot
        if start < 0:
            start = 0
        # head begins at the sentence start or at the first word
        # inside the given distance:
        head = text[start: index]
        lengthHead = len(head)
        # Look for the beginning of the sentence:
        while True:
            matcher = self._rexprSeparator.search(head)
            if matcher is None:
                break
            start += matcher.start()
            head = head[matcher.start()+1:]
        
        if len(head) == lengthHead and start > 0:
            matcher = self._rexprFirstWord.match(head)
            if matcher != None:
                head = head[matcher.end():]
                if head[0:1] == ' ':
                    head = head[1:]
                
        # tail ends with the sentence end 
        # or the last word in the given distance:
        pos = index + length
        tail = text[pos:pos + lengthOfSpot]
        matcher = self._rexprSeparator.search(tail)
        if matcher != None:
            start += matcher.start()
            tail = tail[0:matcher.start()+1]
        while len(head) + len(tail) > lengthOfSpot:
            if len(tail) >= len(head):
                matcher = self._rexprLastWord.search(tail)
                if matcher is None:
                    tail = "" if len(tail) <= 10 else tail[0, len(tail) - 10]
                else:
                    tail = tail[0:matcher.start()]
            else:
                matcher = self._rexprFirstWord.match(head)
                if matcher is None:
                    head = "" if len(head) <= 10 else head[0, len(head) - 10]
                else:
                    pos = matcher.end()
                    head = head[pos:]
                    
        return head + text[index:index+length] + tail
        
    def findFirstHitOfTheWord(self, word, text):
        '''Finds the first find spot of the word.
        More precisely: all similar words will be searched.
        @param word: the word to search
        @param text: the text for searching
        @result: None: word or phrase not found<br>
                a tuple: (offset in the text, length of the matching word, wordlist)
        '''
        rc = None
        wordList = self._db.getRelatedWords(word)
        words = r'\b(%s)\b' % (wordList,)
        matcher = re.search(words, text, re.IGNORECASE)
        if matcher != None:
            position = matcher.start()
            rc = (position, matcher.end() - position, wordList)
        return rc 
    
    def findHits(self, words, source, title, docName, link):
        '''Builds a html text for the first find spot of all given words.
        @param words: a list of words to search and mark
        @param title: the title of the text
        @param source: the full text of the chapter
        @param link: the link of the chapter
        @return the html text of the find spots
        '''
        link = saxutils.escape(link)
        title = saxutils.escape(title)
        html = '<p class="sm_link"><a href="%s">%s</a></p>%s' % (link, title, "\n")
        html += '<p class="sm_doc">%s</p>%s' % (docName, "\n")
        hitList = ()
        wordList = None
        matcher = re.compile(r'((or|and|[&|])$|-)', re.IGNORECASE)
        for word in words:
            word = word.strip()
            if word != '' and not matcher.match(word):
                if word.startswith('='):
                    word = word[1:]
                hit = self.findFirstHitOfTheWord(word, source)
                if hit != None:
                    hitList += (hit,)
                    if wordList is None:
                        wordList = hit[2]
                    else:
                        wordList += '|' + hit[2] 
        hitList = sorted(hitList, cmpTuples)
        hitList = self.joinHits(hitList)
        if hitList is None:
            html = None
        else:
            for hit in hitList:
                text = self.buildExcerpt(hit[0], hit[1], source)
                pattern = r'\b(' + wordList + r')\b'
                text = re.sub(pattern, "\v\\1\t", text)
                text = saxutils.escape(text)
                text = text.replace("\v", '<b>').replace("\t", '</b>')
                html += '<p class="sm_hit">' + text + "</p>\n"
        return html
    
    def joinHits(self, hitList):
        '''Joins hit spots which have a short distance.
        @param histList: a sorted list of find spots: 
                        tuples: (position, length)
        @return: a possible reduced hit list
        '''    
        lastTuple = None
        rc = ()
        for hit in hitList:
            if lastTuple is None:
                lastTuple = hit
            else:
                if lastTuple[0] + lastTuple[1] + self._lengthOfTheSpot >= hit[0]:
                    lastTuple = (lastTuple[0], hit[0] - lastTuple[0] + hit[1])
                else:
                    rc += (lastTuple,)
                    lastTuple = hit
        if lastTuple != None:
            rc += (lastTuple,)
        return rc
    
    def buildHtmlHeader(self, title):
        rc = '''<!DOCTYPE HTML">
<html>
<head>
<title>%s</title>
<style type="text/css">
.sm_link { margin: 0.5em 0 0 0; color: blue; font-size: 1.1em; }
.sm_doc { margin: 0.1em 0 0 0; color: green; font-size: 0.8em; } 
.sm_hit { margin: 0.25em 0 0 0; color: black; } 
</style>
</head>
<body>
        ''' % (title,)
        return rc
    
    def search(self, phrases, url, withFrame, urlHandler = None):
        '''Search for all chapters containing the given words and phrases.
        @param phrases: words or phrases to search or excluding words
        @param url:    None or the prefix of the links in the result
        @param withFrame: True: result is a valid html document.<br>
                        False: the result contains not the <html><body>...</html> frame
        @param urlHandler: None or an object with a method buildUrl(url) 
        '''
        if phrases != None and len(phrases) == 0:
            phrases = None
        count =  self._resultsPerPage if phrases is None else 500
        db = self._db
        html = '' if not withFrame else self.buildHtmlHeader(None)
        chapters = db.find(phrases, self._indexCurrentPage, self._indexCurrentPage + count)
        ix = 0
        if chapters is not None:
            for chapter in chapters:
                docName = chapter._document._link
                (path, sep, node) = docName.rpartition('/')
                anchor = '' if chapter._anchor == None else '#' + chapter._anchor
                if urlHandler != None:
                    link = urlHandler.buildUrl(docName, anchor)
                else:
                    link = url + docName + anchor
                hits = self.findHits(phrases, chapter._pureText, chapter._title, node, link)
                if hits != None:
                    ix += 1
                    if ix >= self._indexCurrentPage:
                        html += hits
                        if ix - self._indexCurrentPage >= self._resultsPerPage:
                            break
        if withFrame:
            html += "</body>\n</html>\n"
        return html

            
          
        