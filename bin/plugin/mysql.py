#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time
import json
import traceback
import MySQLdb

class MySQLQuery:
    def __init__(self, db, user='root', passwd='', host='127.0.0.1', port=3306):
        self.host = host
        self.port = port 
        self.user = user
        self.passwd = passwd
        self.db = db
        self.charset = 'utf8'
        self.timeout = 10
    
        self.conn = None
        self.connect()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def connect(self):
        self.conn = MySQLdb.connect(host = self.host,
                                    port = self.port,
                                    user = self.user,
                                    passwd = self.passwd,
                                    db = self.db,
                                    charset = self.charset,
                                    connect_timeout = self.timeout,
                                    )
 
        self.conn.autocommit(1)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


    def execute(self, sql, param=None):
        cur = self.conn.cursor()
        if param:
            if not isinstance(param, (types.DictType, types.TupleType)):
                param = tuple([param])
            ret = cur.execute(sql, param)
        else:
            ret = cur.execute(sql)
        self._lastid = cur.lastrowid or 0
        cur.close()
        return ret

    def query(self, sql, param=None, isdict=True):
        cur = self.conn.cursor()
        if not param:
            cur.execute(sql)
        else:
            if not isinstance(param, (types.DictType, types.TupleType)):
                param = tuple([param])
            cur.execute(sql, param)
        res = cur.fetchall()
        cur.close()
        if res and isdict:
            ret = []
            xkeys = [ i[0] for i in cur.description]
            for item in res:
                ret.append(dict(zip(xkeys, item)))
        else:
            ret = res
        return ret

conn = None


def mysql(argv=None):
    global conn
    if not conn:
        conn = MySQLQuery('test', 'root', '654321', '127.0.0.1', 3306)
    result = []
    try:
        rows = conn.query('show status')
        statusval = {}
        if rows:
            for row in rows:
                try:
                    statusval[row['Variable_name']] = int(row['Value'])
                except:
                    statusval[row['Variable_name']] = row['Value']
        keys = statusval.keys()
        keys.sort()
        
        result.append(keys)

        row = []
        for k in keys:
            row.append(statusval[k])
        result.append(row)

        #print result
        return result
    except:
        traceback.print_exc()
        conn = None



#mysql()



