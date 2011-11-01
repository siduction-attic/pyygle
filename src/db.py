'''
Created on 09.11.2012

@author: hm
'''
class Chapter:
    '''A 'bean' containing the data of one record of chapter.
    '''
    def __init__(self, chapterId, docId, size, anchor, title, pureText, rating):
        '''Constructor.
        @param chapterId: the primary key
        @param docId: the forign key to table document
        @param size: the size of the text
        @param anchor: the link of the chapter inside the document
        @param title: the title of the chapter
        @param pureText: the text without formatting
        @param rating: the rating
        '''
        self._id = chapterId
        self._docId = docId
        self._size = size
        self._anchor = anchor
        self._pureText = pureText
        self._rating = rating
        self._document = None
        self._title = title

class Document:
    '''A 'bean' containing the data of one record of table.
    @param param: docId: the primary key
    @param docType: 1: raw text 2: xml
    @param link: the link of the document
    @param date: the creation date of the document
    @param size: the size of the document
    @param docTreeId: the root of the document tree
    '''
    def __init__(self, docId, docType, link, date, size, docTreeId):
        self._id = docId
        self._docType = docType
        self._docTreeId = docTreeId
        self._link = link
        self._date = date
        self._size = size
        self._docTree = None

class DocTree:
    '''A 'bean' containing the data of one record of docTree.
    '''
    def __init__(self, docTreeId, url, path):
        '''Constructor.
        @param docTreeId: the primary key
        @param url: the url used from webservers
        @param path: the path of the local filesystem. Used by filebrowsers
        '''
        self._id = docTreeId
        self._url = url
        self._path = path
 
          
class DbStatistic:
    '''A 'bean' containing statistic data of the db.
    @param documentCount: the number of documents
    @param chapterCount: the number of chapters
    @param wordCount: the number of words
    @param rawWordCount: the number of raw words
    '''
    def __init__(self, documentCount, chapterCount, wordCount, wordOfChapterCount, rawWordCount):
        self._docs = documentCount
        self._chapters = chapterCount
        self._words = wordCount        
        self._rawWords = rawWordCount
        self._wordsOfChapter = wordOfChapterCount
