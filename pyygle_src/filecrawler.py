'''
Created on 14.11.2012

@author: hm
'''

import os, re, stat, codecs
from xmlparser import XmlParser

class FileCrawler:
    '''
    Traverses a filetree and puts the documents into the database
    '''


    def __init__(self, logger, verbose = False):
        '''
        Constructor.
        @param byExtension: True: the file type will be decided 
                        by the file extension, e.g. *.htm is HTML
        '''
        self._logger = logger
        self._parser = XmlParser(logger)
        self._fileCount = 0
        self._dirCount = 0
        self._mibytes = 0
        self._verbose = verbose
        
    def scanDocumentTree(self, dirName, validator, db, url):
        '''Scans one directory and recursively all subdirs.
        @param dirName: name of the directory to scan
        @param validator: an instance with a method docType(filename).
            If the method returns 1, the aFile is a text aFile, 2: the aFile is XML
        @param db: the database to fill 
        @param url: the base URL for webservers
        '''
        db.putDocTree(url, dirName)
        self.scanOneDirectory(dirName, validator, db)
        
    def scanOneDirectory(self, dirName, validator, db):
        '''Scans one directory and recursively all subdirs.
        @param dirName: name of the directory to scan
        @param validator: an instance with a method docType(filename).
            If the method returns 1, the aFile is a text aFile, 2: the aFile is XML
        @param db: the database to fill 
        '''
        files = os.listdir(dirName)
        if self._verbose:
                print('=== ' + dirName)
        self._dirCount += 1
        parser = self._parser
        for aFile in files:
            full = dirName + os.path.sep + aFile
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(full)
            if stat.S_ISDIR(mode):
                continue
            docType = validator.docType(full)
            if self._verbose and docType != 0:
                print "%s (%.3f kbyte)" % (full, size / 1000.0)
            if docType == 1:
                self._fileCount += 1
                self._mibytes += size / 1024 / 1024
                fp = codecs.open(full, encoding='utf-8')
                text =  fp.read();
                fp.close()
                length = len(text)
                db.putDocument(full, mtime, 1, length)
                parser.scanChapter(None, None, text, db)
            elif docType == 2:
                self._fileCount += 1
                self._mibytes += size / 1024.0 / 1024
                fp = codecs.open(full, encoding='utf-8')
                xml =  fp.read();
                fp.close()
                parser.scanXmlDocument(xml, mtime, full, db)
                
        for aFile in files:
            full = dirName + os.path.sep + aFile
            info = os.stat(full)
            if stat.S_ISDIR(info[0]):
                self.scanOneDirectory(full, validator, db)
            
class RExprDocFinder:
    '''Finds the document type by the file extension.
    Can be used as parameter of FileCrawler.scanDocumentTree()
    '''
    def __init__(self, pattern = None, ignoreCase = True, noExtensionIsText = False):
        '''Constructor.
        @param pattern: a regular expression defining the possible documents.
                        None: same as '.*'
        @param ignoreCase: True: case of the names is irrelevant
        @param noExtensionIsText: True: if there is no extension it is a text file
        '''
        if pattern is None:
            self._pattern = None
        elif ignoreCase:
            self._pattern = re.compile(pattern, re.IGNORECASE)
        else:
            self._pattern = re.compile(pattern)
        self._extPattern = re.compile(
            #    1         1 2                  3  3           2
            r'[.](x?html?|xml)|(txt|sh|log|pl|[ch](pp)?|p[yl]|php|co?nf|ini|csv|properties)$', 
            re.IGNORECASE)
        self._noExtensionIsText = noExtensionIsText
        
    def docType(self, name):
        '''
        Detects the document type given by the file extension.
        @param name: filename to inspect
        @return:    0: file to ignore<br>
                    1: text file
                    2: xml or html file
        '''
        rc = 0
        if self._noExtensionIsText:
            ix = name.rfind('.')
            if ix < 0 or name.rfind('/') > ix:
                rc = 1
        if rc == 0 and (self._pattern is None or self._pattern.search(name)):
            matcher = self._extPattern.search(name)
            if matcher != None:
                group1 = matcher.group(1)
                rc = 2 if group1 != None else 1
        return rc       
            