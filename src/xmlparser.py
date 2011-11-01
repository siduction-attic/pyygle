'''
Created on 09.11.2012

@author: hm
'''
import re, os

class XmlParser:
    '''
    Extracts the chapters and words from a XML file and puts it into a db
    '''


    def __init__(self, logger):
        '''
        Constructor
        '''
        self._logger = logger
    
    def unescape(self, xml):
        '''Removes meta data from an XML text.
        @param xml: xml text
        @return: the raw text without xml tags and expanded special chars
        '''
        pureText = xml
        if len(xml) != 0:
            pureText = re.sub(r'\<[^>]+\>', '', xml)
            if pureText.find('&') >= 0:
                pureText = pureText.replace('&lt;', '<')
                pureText = pureText.replace('&gt;', '>')
                pureText = pureText.replace('&amp;', '&')
                pureText = pureText.replace('&quot;', '"')
        return pureText
    
    def scanChapter(self, anchor, title, pureText, db):
        '''Puts a chapter into the database.
        The chapter and the words will be inserted.
        @param anchor: None or the anchor for addressing the chapter
        @param pureText: the text without formating metadata
        @param db: the database
        '''
        pureText = re.sub(r'[ \t]+', ' ', pureText)
        if title is None or title == '':
            title = pureText[:50]
            matcher = re.search(r'[\n!?]', title)
            if matcher != None:
                title = title[:matcher.start()]
            else:
                matcher = re.search(r'[.]\W', title)
                if matcher != None:
                    title = title[:matcher.start()] 
        lastLen = 0
        current = len(pureText)
        while lastLen != current:
            pureText = pureText.replace('  ', ' ')
            lastLen = current
            current = len(pureText)
        db.putChapter(anchor, title, pureText, 10 + 2 * len(str(current)))
        
        precomp = re.compile(r'\W*(\w+)')
        while len(pureText) != 0:
            matcher = precomp.match(pureText)
            if matcher == None:
                break
            word = matcher.group(1)
            length = matcher.end() - matcher.start()
            pureText = pureText[length:]
            word = word.lower()
            word = db.normalizeWord(word)
            db.putWord(word) 
        
    def scanXmlChapter(self, xml, db):
        '''Scans a chapter from a XML document.
        Puts the content of the chapter into the db.
        @param xml: the xml text
        @param db: the database
        '''
        matcher = re.search(r'\<a[^>]*?name="?([^ "\>]+)', xml)
        if matcher != None:
            self._lastAnchor = matcher.group(1)
        matcher = re.search(r'<[Hh][12].*?[>](.*?)[<]/[hH]', xml)
        title = self.unescape(matcher.group(1)) if matcher != None else None
        pureText = self.unescape(xml)
        self.scanChapter(self._lastAnchor, title, pureText, db)
        
    def scanXmlDocument(self, xml, date, link, db):
        '''Parses an XML text and put the data into the database.
        @param xml: the XML text
        @param link: the URL of the document
        @param db: the database where the data will be stored
        '''
        length = len(xml)
        db.putDocument(link, date, 2, length)
        # Remove all comments:
        xml = re.sub(r'[<]--.*?--[>]', '', xml)
        # Replace the whitespaces to blanks:
        xml = re.sub(r' *[\r\n\t]+ *', ' ', xml)
        self._lastAnchor = None

        # over all chapters:
        precompiled = re.compile(r'.\<[hH][12]')
        while xml != None:
            matcher = precompiled.search(xml)
            if matcher == None:
                self.scanXmlChapter(xml, db)
                xml = None
            else:
                ix = matcher.start() + 1
                chapter = xml[0:ix]
                xml = xml[ix:]
                self.scanXmlChapter(chapter, db)
 
