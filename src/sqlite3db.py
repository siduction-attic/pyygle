'''
Created on 09.11.2012

@author: hm
'''
import sys, os.path
import sqlite3
import db
from db import Chapter, Document, DocTree

class SqLite3Db:
    '''
    classdocs
    '''


    def __init__(self, dbName, logger):
        '''
        Constructor.
        @param dbName:    the filename of the db (with path)
        @param logger:    the logger
        '''
        self._dbName = dbName
        self._logger = logger
        self._cursor = None
        self._insertCount = 0
        self._maxCommit = 1
        self._currentDocTree = None
        self._currentChapter = None
        self._currentDocument = None
        self._conn = None
        self._commitOften = False
        self._maxRowsToSort = 50
        
    def commit(self):
        'Performs a commit.'
        self._insertCount += 1
        if self._insertCount % self._maxCommit == 0:
            self._conn.commit()
 
    def getCursor(self):
        '''Returns the cached cursor
        @return the current db cursor
        '''
        if self._conn is None:
            self._conn = sqlite3.connect(self._dbName)

        if self._cursor is None:
            self._cursor = self._conn.cursor()
        return self._cursor
    
    def create(self):
        '''Creates the tables of the db.
        If a database exists it will deleted before.
        '''
        if self._conn != None:
            self._conn.close()
        if os.path.exists(self._dbName):
            self._logger.log('removing db: ' + self._dbName)
            os.remove(self._dbName)
        self._conn = sqlite3.connect(self._dbName)
        cursor = self.getCursor()
        self._logger.log('creating db: ' + self._dbName)
        sql = '''
create table word (
 word_id integer PRIMARY KEY,
 word varchar(64),
 count integer,
 hits integer
);
create table document (
 doc_id integer PRIMARY KEY,
 doc_type integer,
 link varchar(255),
 date integer,
 size integer,
 doctree_id integer
);
create table chapter (
 chapter_id integer PRIMARY KEY,
 doc_id integer,
 size integer,
 anchor varchar(255),
 pure_text text,
 rating integer,
 title varchar(255)
 );
create table wordOfChapter (
 word_id integer,
 chapter_id integer,
 count integer
);
create table normOfWord (
 variant varchar(64),
 word_id integer
);
create table rawWord (
 word varchar(64)
);
create table docTree (
 doctree_id integer PRIMARY KEY,
 url varchar(255),
 path varchar(255)
);
            '''
        cursor.executescript(sql)
        self.commit()
        
    def close(self):
        'Frees the resources.'
        if self._conn != None:
            self.commit()
        if self._cursor != None:
            self._cursor.close()
            self._cursor = None
        if self._conn != None:
            self._conn.close()
            self._conn = None
     
    def putDocTree(self, url, path):
        '''Stores a document tree and defines the current document tree.
        @param url: http URL of the document tree
        @param path: path in the local filesystem
        '''
        sql = '''insert into doctree (url, path) 
            values(?, ?);'''
        cursor = self.getCursor()
        cursor.execute(sql, (url if url != None else 'NULL',
                path if path != None else 'NULL'))
        self._currentDocTree = db.DocTree(cursor.lastrowid, url, path) 
        self.commit()
        
    def putDocument(self, link, date, docType, size):
        '''Stores a document and defines the current document.
        @param link: URL of the document
        @param date: the creation date of the document
        @param docType: 1: raw text 2: xml
        @param size: the document size
        '''
        sql = '''insert into document (doc_type, link, date, size, doctree_id) 
            values(?, ?, ?, ?, ?);'''
        cursor = self.getCursor()
        cursor.execute(sql, (docType, link, date, size, self._currentDocTree._id))
        self._currentDocument = db.Document(cursor.lastrowid, docType, 
            link, date, size, self._currentDocTree._id)
        self.commit()
        
    def putChapter(self, anchor, title, text, rating):
        '''Stores the chapter and defines the current chapter.
        @param anchor: last part of the URL, e.g. #introduction
        @param text: the raw text
        @param title: the title of the chapter
        @param rating: the rating of the chapter. 
                    Can change the order of the search results
        '''
        sql = 'insert into chapter(doc_id,size,anchor,title,pure_text)values(?,?,?,?,?)' 
        cursor = self.getCursor()
        cursor.execute(sql, (self._currentDocument._id, len(text), anchor, title, text))
        self._currentChapter = db.Chapter(cursor.lastrowid,
            self._currentDocument._id, len(text), anchor, title, text, rating)
        self.commit()
        
    def putWord(self, word, insertIntoChapter = True, canExist = True):
        '''Stores the word.
        If the word exists in the table word the field count will be incremented.
        If insertOnly == False storage in the table wordOfChapter.
        @param word:   the word to store
        @param insertOnly: True: only storage in the table word
        @param mayExist: True: if the word exists in the db the count will be incremented
        @return: the word_id of the word
        '''
        cursor = self.getCursor()
        insertIntoWord = True
        if canExist:
            # We try to increment the count.
            sql = 'select word_id from word where word=?'
            cursor.execute(sql, (word,))
            wordId = cursor.fetchone()
            if wordId != None:
                rc = wordId[0]
                sql = 'update word set count=count+1 where word_id=%d' % (rc,)
                cursor.execute(sql)
                insertIntoWord = False
        if insertIntoWord:
            sql = 'insert into word (word, count, hits)values(?, ?, 0)' 
            cursor.execute(sql, (word, 1 if canExist else 0))
            rc = cursor.lastrowid
        if insertIntoChapter:
            count = self._conn.total_changes
            sql = ('update wordOfChapter set count=count+1 where word_id=%d and chapter_id=%d'
                % (rc, self._currentChapter._id))
            cursor.execute(sql)
            # Update successful?
            if count == self._conn.total_changes:
                # No, then we will insert
                sql = ('insert into wordofchapter (word_id, chapter_id, count)values(%d, %d, 1)'
                       % (rc, self._currentChapter._id))
                cursor.execute(sql)
        if self._commitOften:
            self._conn.commit()
        return rc

    def putRawWord(self, word):
        '''Stores the word in the table rawwords if does not exist.
        @param word    the word to store
        '''
        cursor = self.getCursor()
        # We try to increment the count.
        sql = 'select count(*) from rawWord where word=?'
        cursor.execute(sql, (word,))
        if cursor.fetchone()[0] == 0:
            sql = 'insert into rawWord (word)values(?)' 
            cursor.execute(sql, (word,))

    def putVariants(self, norm, variants):
        '''Puts a normalized word and its variants into the database
        @param norm: a normalized word
        @param variants: a sequence of the other forms of <code>norm</code>. 
        '''
        cursor = self.getCursor()
        word_id = self.putWord(norm, False, False)
        sql = 'insert into normOfWord (word_id, variant) values(?, ?)'
        for variant in variants:
            cursor.execute(sql, (word_id, variant))    
           
    
    def getCount(self, table):
        '''Returns the row count of the given table.
        @param table: the table to inspect
        @return: the count of rows in the table
        '''
        if len(table) > 10:
            return 0
        sql = 'select count(*) from ' + table
        cursor = self.getCursor()
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        return count
    
    def getCountOfWord(self, word):
        '''Gets the count of a word in all documents
        @param word: the word to inspect
        @return: the number of hits
        '''
        sql = 'select count from word where word=?'
        cursor = self.getCursor()
        cursor.execute(sql, (word,))
        count = cursor.fetchone()
        rc = -1 if count is None else count[0]
        return rc
        
         
    def getStatistic(self):
        '''Returns the database statistic.
        @return: an instance of DbStatistic
        '''
        docs = self.getCount('document')
        chapters = self.getCount('chapter')
        words = self.getCount('word')
        rawWords = self.getCount('rawword')
        wordsOfChapter = self.getCount('wordOfChapter')
        stat = db.DbStatistic(docs, chapters, words, wordsOfChapter, rawWords)
        return stat
    
    def completeDocTrees(self, cursor, docTreeList, docs):
        '''Supplies the document and doctree info to the chapters
        @param cursor:    the db cursor
        @param docTreeList:   a comma separated list of document tree ids
        @param docs:  the dirctionary of documents
        '''
        docTrees = dict()
        sql = 'select doctree_id, url, path from doctree where doctree_id in (%s)' % (docTreeList,)
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            docTreeId = row[0] 
            docTree = DocTree(docTreeId, row[1], row[2])
            docTrees[docTreeId] = docTree
                
        for docId in docs.iterkeys():
            doc = docs[docId]
            doc._docTree = docTrees[doc._docTreeId]
    
    def completeDocuments(self, cursor, docList, chapters):
        '''Supplies the document and doctree info to the chapters.
        @param cursor:    the db cursor
        @param doclist:   a comma separated list of document ids
        @param chapters:  the list of chapters
        '''
        documents = dict()
        docTrees = ()
        sql = '''select doc_id,doc_type,link,date,size,doctree_id 
            from document where doc_id in (%s)''' % (docList,)
        cursor.execute(sql)
        docTreeList = None
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            docTreeId = row[5] 
            doc = Document(row[0], row[1], row[2], row[3], row[4], docTreeId)
            documents[doc._id] = doc
            if not docTreeId in docTrees:
                if docTreeList is None:
                    docTreeList = ''
                else:
                    docTreeList += ','
                docTreeList += str(docTreeId)
                docTrees += (docTreeId,)
        
        self.completeDocTrees(cursor, docTreeList, documents)        
        for chapter in chapters:
            chapter._document = documents[chapter._docId]
                
    def getChapters(self, idList, cursor):
        '''Builds a list of chapters with a given id list
        @param idList: a comma separated list of chapter ids
        @param cursor: the db cursor
        @return: a list of Chapter instances
        '''
        sql = '''select chapter_id,doc_id,size,anchor,title,pure_text,rating 
            from chapter where chapter_id in (%s)''' % (idList,)
        chapters = ()
        docIds = ()
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            chapter = Chapter(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            chapters += (chapter,)
            if not (chapter._docId in docIds):
                docIds += (chapter._docId,)
        docList = None
        for doc in docIds:
            if docList is None:
                docList = ''
            else:
                docList += ','
            docList += str(doc)
        self.completeDocuments(cursor, docList, chapters)
        return chapters

    def find(self, words, phrases, andCondition, excluded, first, count):
        '''Finds a list of chapters matching the search conditions.
        @param words:        list of words to search
        @param phrases:      list of phrases to search
        @param andCondition: True: all words and phrases must be present in the chapter
                            thereby the chapter matches.
        @param excluded: array of words which must not exist in a matching 
                            chapter
        @param first: the offset of the result list inside the matching list.
                            This is for pagenation.
        @param count: the maximal number of elements in the result
        @return None: nothing found.<br>
                otherwise: the list of Chapter instances
        '''
        if not andCondition:
            wordList = ''
            for word in words:
                wordList += "'" + self.normalizeWord(word) + "',"
            wordList = wordList[0:-1]
            sql = '''select chapter_id from word w, wordOfchapter x
                where w.word in (%s) and w.word_id=x.word_id
            ''' % (wordList,)
        else :
            sql = None
            for word in words:
                if sql is None:
                    sql = ''
                else:
                    sql += "\nintersect "
                word = self.normalizeWord(word)
                sql += '''select chapter_id from word w, wordOfchapter x
                    where w.word = '%s' and w.word_id=x.word_id''' % (word,)
            for phrase in phrases:
                if sql is None:
                    sql = ''
                else:
                    sql += "\nintersect "
                phrase = '%' + phrase.replace('%', '_').replace("'", '_') + '%'
                sql += "select chapter_id from chapter where pure_text like '" + phrase + "'"
        cursor = self.getCursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(self._maxRowsToSort)
        if rows is None or len(rows) == 0:
            chapters = None
        else:
            idList = None
            for row in rows:
                if idList is None:
                    idList = ''
                else:
                    idList +=','
                idList += str(row[0])
            chapters = self.getChapters(idList, cursor)
        return chapters 
        
    def normalizeWord(self, word):
        '''Searches for a normalized form of the word.
        @param word:    word to search
        @return word: no normalized form exists.<br>
                <normalized word>: otherwise
        '''
        word = word.lower()
        sql = '''select word from word, normOfWord
            where variant=? and word.word_id=normOfWord.word_id'''
        cursor = self.getCursor()
        cursor.execute(sql, (word, ))
        found = cursor.fetchone()
        if found != None:
            word = found[0]
        return word

    def getRelatedWords(self, word):
        '''Returns all words which have the same normalized form.
        Example: word='breaks' rc='breaks|break|broken'
        @param word: the start of the search
        @return: a list of words with the same normalized form as word separated by '|'
        '''
        words = word.lower()
        sql = '''select variant from normofword where word_id in
            (select word_id from normofword where variant=?)
            union
            select w.word from normofword n, word w 
            where n.variant=? and n.word_id=w.word_id'''
        cursor = self.getCursor()
        cursor.execute(sql, (words, words))
        while True:
            raw = cursor.fetchone()
            if raw is None:
                break
            words += '|' + raw[0]
        if words.find('|') < 0:
            sql = '''select variant from normofword where word_id in
                (select word_id from word where word=?)
                union
                select w.word from normofword n, word w 
                where n.variant=? and n.word_id=w.word_id'''
            cursor = self.getCursor()
            cursor.execute(sql, (words, words))
            while True:
                raw = cursor.fetchone()
                if raw is None:
                    break
                words += '|' + raw[0]
            
        return words
        