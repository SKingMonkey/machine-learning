# -*- coding:utf-8 -*-
import feedparser
import re


def getwords(html):
    txt = re.compile(r'<[^>]+>]').sub('', html)

    words = re.compile(r'[^A-Z^a-z]+').split(txt)

    return [word.lower() for word in words]


def getwordcounts(url):
    d = feedparser.parse(url)
    wc = {}

    try:
        title = d.feed.title
    except Exception:
        return None, {}

    for e in d.entries:
        if 'summary' in e: summary = e.summary
        else: summary = e.description

        try:
            words = getwords(e.title + ' ' + summary)
        except Exception:
            print e.keys()
            continue

        for word in words:
            wc.setdefault(word, 0)
            wc[word] += 1

    return title, wc


if __name__ == '__main__':
    apcount = {}
    wordcounts = {}

    feedlist = [line for line in file('feedlist.txt')]
    for feedurl in feedlist:
        title, wc = getwordcounts(feedurl)
        if not title:
            print 'Skip %s' % feedurl
            continue
        print 'Get title: %s' % title
        wordcounts[title] = wc

        for word, count in wc.iteritems():
            apcount.setdefault(word, 0)
            if count >= 1:
                apcount[word] += 1

    wordlist = []
    for w, bc in apcount.iteritems():
        frac = float(bc) / len(feedlist)
        if 0.5 > frac > 0.1:
            wordlist.append(w)

    with open('blogdata.txt', 'w') as f:
        f.write('Blog')
        for word in wordlist:
            f.write('\t%s' % word)
        f.write('\n')
        for blog, wc in wordcounts.iteritems():
            f.write(blog)
            for word in wordlist:
                if word in wc:
                    f.write('\t%d' % wc[word])
                else:
                    f.write('\t0')
            f.write('\n')
