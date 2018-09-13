# -*- coding:utf-8 -*-
import urllib2
from bs4 import BeautifulSoup
from pysqlite2 import dbapi2 as sqlite


class Crawler(object):
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    def addtoindex(self, page, soup):
        pass

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

