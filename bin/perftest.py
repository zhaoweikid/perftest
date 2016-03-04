#!/usr/bin/python
# coding: utf-8
from gevent import monkey; monkey.patch_all()
import os, sys
import traceback
import getopt
import gevent
import time
from gevent.pool import Pool
from gevent.event import Event
import urllib2, urllib

def run(result, uri, requests, longconn, timeout):
    global waiting
    waiting.wait()

    for i in range(0, requests):
        tstart = time.time()
        response = urllib2.urlopen(uri, timeout=timeout)
        length = len(response.read())
        code = response.getcode()
        tend = time.time()
       
        ret = 0
        if code == 200:
            ret = 1
        result.append({'start':tstart, 'end':tend, 'ret':ret, 'len':length})


def start(uri, concur=1, requests=100, longconn=0, timeout=30):
    global waiting
    waiting = Event()

    result = {}
    ts = []
    for i in range(0, concur):
        result[i] = []
        ts.append(gevent.spawn(run, result[i], uri, requests, longconn, timeout))
   
    waiting.set()
    gevent.joinall(ts)

    allreq = requests * concur

    ts = []
    succ = 0
    trans = 0
    tstart = 999999999999999999999
    tend = 0
    for k,v in result.iteritems():
        if v[0]['start'] < tstart:
            tstart = v[0]['start']
        if v[-1]['end'] > tend:
            tend = v[-1]['end']

        for row in v:
            ts.append(row['end'] - row['start'])
            succ += row['ret']
            trans += row['len']
    succ_rate = float(succ) / allreq * 100
    qps = int(float(allreq) / (tend-tstart))
    avg = float(sum(ts)) / allreq 
    band = int(float(trans) / (tend-tstart) /1024)
    
    print 'time:%f requests:%d, succ:%d %.2f%%, qps:%d, avg:%.3fms, trans:%dk, band:%dk' % \
            (tend-tstart, allreq, succ, succ_rate, qps, avg*1000, int(float(trans)/1024), band)

    print 'end'

def main():
    try:  
        opts, args = getopt.getopt(sys.argv[1:], "c:n:t:l", ["concurrency", "requests", "timeout", "longconn"])  
        for i in range(0, len(opts)):
            x = opts[i]
            if x[0] == '-l' and x[1] == '':
                opts[i] = ('-l', 0)
        config = dict([ (x[0], int(x[1]))  for x in opts ])
        uri = args[0]
    except:  
        traceback.print_exc()
        print 'usage:\n\tperftest.py [options] uri'
        print 'options:'
        print '\t-n requests     Number of requests to perform. Default is 100'
        print '\t-c concurrency  Number of multiple requests to make at a time. Default is 1'
        print '\t-t timeout      Seconds to max. wait for each response. Default is 30 seconds'
        print 'uri:'
        print '\thttp://127.0.0.1/aaaaa?a=1'
        print '\thttps://127.0.0.1/aaa?a=1'
        print '\tthrift://127.0.0.1:10000?args=json'
        print 
        return
    
    start(uri, config.get('-c', 1), config.get('-n', 100), config.get('-l', 0), config.get('-t', 30))


if __name__ == '__main__':
    main()


