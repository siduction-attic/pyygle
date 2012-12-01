'''
Created on 09.11.2012

@author: hm
'''
import re

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

class SqlDB:
    '''Implements basic services for all SQL databases
    '''
    def buildSelectWords(self, word):
        '''Build the SQL statement for searching a word.
        @param word: the word to search
        @return: the sql statement
        '''
        word = self.normalizeWord(word)
        sql = '''select chapter_id from word w, wordOfchapter x
            where w.word = '%s' and w.word_id=x.word_id''' % (word,)
        return sql
        
    def buildSelectChapters(self, phrases):
        '''Builds the  SQL statement for the central search
        for chapters.
        @param phrases: the words and phrases to search
        @return: the sql statement
        '''
        sql = "select chapter_id from chapter where chapter_id in (\n"
        level = 0
        op = None
        delayedExlude = None
        for phrase in phrases:
            phrase = phrase.strip()
            if phrase == '':
                pass
            elif phrase == '(':
                sql += '('
                level += 1
                op = ''
            elif phrase == ')':
                if level > 0:
                    level -= 1
                    if delayedExlude is not None and op is not None:
                        sql += "\nexcept " + self.buildSelectWords(delayedExlude)
                        delayedExlude = None
                    sql += ')'
                op = "\nintersect "
            elif phrase == '&' or phrase.lower() == 'and':
                op = "\nintersect "
            elif phrase == '|' or phrase.lower() == 'or':
                op = "\nunion "
            elif phrase.startswith('=') or re.search(r'\W', phrase) and not phrase.startswith('-'):
                # search a phrase:
                if op is not None:
                    sql += op
                if phrase.startswith('='):
                    phrase = phrase[1:]
                phrase = '%' + phrase.replace('%', '_').replace("'", '_').replace('*', '%') + '%'
                sql += "select chapter_id from chapter where pure_text like '" + phrase + "'"
                op = "\nintersect "
            else:
                # seerch a word
                valid = True
                if phrase.startswith('-'):
                    phrase = phrase[1:]
                    if op is None:
                        delayedExlude = phrase
                        valid = False
                    else:
                        op = "\nexcept "
                if valid:
                    if op is not None:
                        sql += op
                    sql += self.buildSelectWords(phrase)
                    op = "\nintersect "
        if delayedExlude is not None:
            sql += "\nexcept " + self.buildSelectWords(delayedExlude)
        while level > 0:
            level -= 1
            sql += ')'
        sql += "\n) order  by rating desc"
        return sql
    
    def buildSelectDocTree(self):
        sql = '''insert into doctree (url, path) 
            values(?, ?);'''
        return sql
        
    def buildSelectDocument(self):  
        sql = '''insert into document (doc_type, link, date, size, doctree_id) 
            values(?, ?, ?, ?, ?);'''
        return sql

    def buildInsertChapter(self):
        sql = 'insert into chapter(doc_id,size,anchor,title,pure_text, rating)values(?,?,?,?,?,?)'
        return sql
    
    def buildSelectWord(self):
        sql = 'select word_id from word where word=?'
        return sql
    
    def buildUpdateWordCount(self, value):
        sql = 'update word set count=count+1 where word_id=%d' % (value,)
        return sql        

    def buildInsertWord(self):
        sql = 'insert into word (word, count, hits)values(?, ?, 0)'
        return sql        

    def buildUpdateWordOfChapter(self, wordId, chapterId):
        sql = ('update wordOfChapter set count=count+1 where word_id=%d and chapter_id=%d'
                % (wordId, chapterId))
        return sql
            
    def buildInsertWordOfChapter(self, wordId, chapterId):
        sql = ('insert into wordofchapter (word_id, chapter_id, count)values(%d, %d, 1)'
                % (wordId, chapterId))
        return sql        

    def buildSelectCountRawWords(self):
        sql = 'select count(*) from rawWord where word=?'
        return sql
        
    def buildInsertRawWords(self):
        sql = 'insert into rawWord (word)values(?)'
        return sql
        
    def buildInsertVariants(self):
        sql = 'insert into normOfWord (word_id, variant) values(?, ?)'
        return sql
        
    def buildSelectDocTrees(self, docTreeList):
        sql = 'select doctree_id, url, path from doctree where doctree_id in (%s)' % (docTreeList,)
        return sql
    
    def buildSelectChapter(self, idList):
        sql = '''select chapter_id,doc_id,size,anchor,title,pure_text,rating 
            from chapter where chapter_id in (%s)''' % (idList,)
        return sql
               
    def buildSelectNormWord(self):
        sql = '''select word from word, normOfWord
            where variant=? and word.word_id=normOfWord.word_id'''
        return sql
       
    def buildSelectRelatedWords(self):
        sql = '''select variant from normofword where word_id in
            (select word_id from normofword where variant=?)
            union
            select w.word from normofword n, word w 
            where n.variant=? and n.word_id=w.word_id'''
        return sql

    def buildSelectRelatedWords2(self):
        sql = '''select variant from normofword where word_id in
                (select word_id from word where word=?)
                union
                select w.word from normofword n, word w 
                where n.variant=? and n.word_id=w.word_id'''
        return sql

