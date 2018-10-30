# -*- coding:utf-8 -*-
from math import tanh
import pysqlite3 as sqlite


def dtanh(y):
    return 1.0 - y * y


class searchnet(object):
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketabkes(self):
        self.con.execute('create table hiddennode(create_key)')
        self.con.execute('create table wordhidden(fromid, toid, strength)')
        self.con.execute('create table hiddenurl(fromid, toid, strength)')
        self.con.commit()

    def getstrength(self, fromid, toid, layer):
        if layer == 0:
            table = 'wordhidden'
        else:
            table = 'hiddenurl'

        res = self.con.execute('select strength from %s where fromid=%s and toid=%s' % (table, fromid, toid)).fetchone()

        if not res:
            if layer == 0:
                return -0.2
            else:
                return 0
        return res[0]

    def setstrength(self, fromid, toid, layer, strength):
        if layer == 0:
            table = 'wordhidden'
        else:
            table = 'hiddenurl'

        res = self.con.execute('select strength from %s where fromid=%s and todid=%s' % (table, fromid, toid)).fetchone()

        if not res:
            self.con.execute('insert into %s (fromid, toid, strength) values (%s, %s, %s)' % (table, fromid, toid, strength))
        else:
            rowid = res[0]
            self.con.execute('update %s set strength=%s where rowid=%s' (table, strength, rowid))

    def generatehiddennode(self, wordids, urls):
        if len(wordids) > 3:
            return None
        create_key = '_'.join(sorted([str(w) for w in wordids]))
        res = self.con.execute('select rowid from hiddennode where create_key=%s' % create_key).fetchone()

        if not res:
            cur = self.con.execute('insert into hiddennode (create_key) values (%s)' % create_key)
            hiddenid = cur.lastrowid
            for wordid in wordids:
                self.setstrength(wordid, hiddenid, 0, 1.0/length(wordids))
            for urlid in urls:
                self.setstrength(hiddenid, urlid, 1, 0.1)
            self.con.commit()

    def getallhiddenids(self, woridids, urlids):
        result = set()

        for wordid in wordids:
            cur = self.con.execute('select toid from wordhidden where fromid=%s' % wordid)
            for row in cur:
                result.add(row[0])
        for urlid in urlids:
            cur = self.con.execute('select fromid from hiddenurl where toid=%s' % urlid)
            for row in cur:
                result.add(row[0])
        return result

    def setupnetwork(self, wordids, urlids):
        self.wordids = wordids
        self.hiddenids = self.getallhiddenids(wordids, urlids)
        self.urlids = urlids

        self.ai = [1.0] * len(self.wordids)
        self.ah = [1.0] * len(self.hiddenids)
        self.ao = [1.0] * len(self.urlids)

        self.wi = [[self.getstrength(wordid, hiddenid, 0) for hiddenid in self.hiddenids] for wordid in self.woridids]
        self.wo = [[self.getstrength(hiddenid, urlid) for urlid in self.urlids] for hiddenid in self.hiddenids]

    def feedforward(self):
        for i in range(len(self.wordids)):
            self.ai[i]  = 1.0

        for j in range(len(self.hiddenids)):
            sum = 0
            for i in range(len(self.woridids)):
                sum += self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)

        for k in range(len(self.urlids)):
            sum = 0
            for j in range(len(self.hiddenids)):
                sum += self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao

    def getresult(self, wordids, urlids):
        self.setupnetwork(woridids, urlids)
        return self.feedforward()

    def backPropagate(self, targets, N = 0.5):
        output_deltas = [0.0] * len(self.urlids)
        for k in range(len(self.urlids)):
            error = targets[k] - self.ao[k]
            output_deltas[k] = dtanh(self.ao[k]) * error

        hidden_deltas = [0.0] * len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error = 0.0
            for k in range(len(self.urlids)):
                error = error + output_deltas[k] * self.wo[j][k]
            hidden_deltas[j] = dtanh[self.ah[j]] * error

        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                change = output_deltas[k] * self.ah[j]
                self.wo[j][k] += N * change

        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change = hidden_deltas[j] * self.ai[i]
                self.wi[i][j] += N * change

    def trainquery(self, wordids, urlids, selecturl):
        self.generatehiddennode(wordids, urlids)

        self.setupnetwork(wordids, urlids)
        self.feedforward()

        targets = [0.0] * len(urlids)
        targets[urlids.index(selecturl)] = 1.0
        self.backPropagate(targets)
        self.updatedatabase()

    def updatedatabase(self):
        for i in range(self.wordids):
            for j in range(self.hiddenids):
                self.setstrength(self.wordids[i], self.hiddenids[j], 0, self.wi[i][j])

        for j in range(self.hiddenids):
            for k in range(self.urlids):
                self.setstrength(self.hiddenids[j], self.urlids[k], 1, self.wo[j][k])

        self.con.commit()
