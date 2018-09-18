# -*- coding:utf-8 -*-
import urllib2
import re
from bs4 import BeautifulSoup
from pysqlite2 import dbapi2 as sqlite
from urlparse import urljoin

pages = ['https://kiwitobes.com/2013/09/26/twitter-lights-and-memory-limits-with-arduino-yun/']

ignorewords = ['the', 'a', 'is']

class Crawler(object):
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    def gettextonly(self, soup):
        v = soup.string

        if not v:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext + '\n'
            return resulttext
        else:
            return v.strip()

    def crawl(self, pages, depth=2):
        for i in range(depth):
            newpages = set()

            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except:
                    print "Could not open %s" % page
                    continue

                soup = BeautifulSoup(c.read())
                self.addtoindex(page, soup)

                links = soup('a')
                for link in links:
                    if 'href' in dict(link.attrs):
                        url = urljoin(page, link['href'])

                        if url.find("'") != -1:
                            continue

                        url = url.split('#')[0]
                        if url[0: 4] == 'http' and not self.isindexed(url):
                            newpages.add(url)

                        linkText = self.gettextonly(link)
                        self.addlinkref(page, url, linkText)
                self.dbcommit()

            pages = newpages

    def addtoindex(self, url, soup):
        if self.isindexed(url):
            return

        print "Indexing " + url

        text = self.gettextonly(soup)
        words = self.separatewords(text)

        urlid = self.getentryid('urllist', 'url', url)

        for i in range(len(words)):
            word = words[i]
            if word in ignorewords:
                continue
            wordid = self.getentryid('wordlist', 'word', word)

            self.con.execute("insert into wordlocation(urlid, wordid, location) values (%d, %d, %d)" % (urlid, wordid, i))

    def addlinkref(self, urlFrom, urlTo, linkText):
        pass

    def isindexed(self, url):
        u = self.con.execute('select rowid from urllist where url="%s"' % url).fetchone()
        if u:
            v = self.con.execute('select * from wordlocation where urlid=%d' % u[0]).fetchone()
            if v:
                return True
        return False

    def separatewords(self, text):
        spliter = re.compile('\\W*')
        return [s.lower() for s in spliter.split(text) if s != '']

    def getentryid(self, table, field, value, createnew=True):
        cur = self.con.execute('select rowid from %s where %s="%s"' % (table, field, value))
        res = cur.fetchone()
        if not res:
            cur = self.con.execute('insert into %s (%s) values ("%s")' % (table, field, value))
            return cur.lastrowid
        else:
            return res[0]

    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integer,toid integer)')
        self.con.execute('create table linkwords(wordid,linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')


class Searcher(object):
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def getmatchrows(self, q):
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []

        words = q.split(' ')
        tablenumber = 0

        for word in words:
            wordrow = self.con.execute('select rowid from wordlist where word="%s"' % word).fetchone()

            if not wordrow:
                wordid = wordrow[0]
                wordids.append(wordid)

                if tablenumber > 0:
                    tablelist = ','
                    clauselist += ' and '
                    clauselist += 'w%d.urlid=w%d.urlid and ' % (tablenumber - 1, tablenumber)
                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid=%d' % (tablenumber, wordid)

                tablenumber += 1

        fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]

        return rows, wordids

