#!/home/qfpay/python/bin/python
# coding: utf-8
from gevent import monkey; monkey.patch_all()
import os, sys
import traceback
import getopt
import gevent
import json
import time
from gevent.pool import Pool
from gevent.event import Event
import urllib2, urllib
from qfcommon.base import logger
from qfcommon.server import client
import qfcommon.thriftclient
import urlparse

def run(result, uri, requests, longconn, timeout):
    global waiting
    waiting.wait()
    
    def _parse_url(uri):
        result = {'server':[{'addr':('', 0), 'timeout':timeout}], 'func':'', 'args':{}}
        p = urlparse.urlparse(uri)
        nc = p.netloc.split(':')
        result['server'][0]['addr'] = (nc[0], int(nc[1]))
        result['func'] = p.path.split('?')[0][1:]
        #result['args'] = p.query.split('=',1)[-1]
       
        query = uri.split('?', 1)
        if len(query) == 2:
            d = []
            for one in query[-1].split('&'):
                d.append(one.split('=', 1))
            result['args'] = dict(d)
        
        result['args']['args'] = json.loads(result['args']['args'])
        print result
        return result
        

    def do_thrift():
        
        u = _parse_url(uri)
        mod = u['args']['mod'].split('.')
        tm = __import__(mod[0])

        for i in range(2, len(mod)+1):
            __import__('.'.join(mod[:i]))

        for x in mod[1:]:
            tm = getattr(tm, x)

        code = 0
        length = 0
        try:
            tstart = time.time()
            tc = client.ThriftClient(u['server'], tm, framed=False)
            print 'args:', u['args']['args']
            ret = tc.call(u['func'], **u['args']['args'])
            tend = time.time()
        except:
            code = -1
       
        ret = 0
        if code == 0:
            ret = 1
        result.append({'start':tstart, 'end':tend, 'ret':ret, 'len':length})

    
    def do_http():
        tstart = time.time()
        response = urllib2.urlopen(uri, timeout=timeout)
        length = len(response.read())
        code = response.getcode()
        tend = time.time()
       
        ret = 0
        if code == 200:
            ret = 1
        result.append({'start':tstart, 'end':tend, 'ret':ret, 'len':length})

    for i in range(0, requests):
        if uri.startswith('http'):
            do_http()
        elif uri.startswith('thrift'):
            do_thrift()


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
        if not v:
            continue
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
        opts, args = getopt.getopt(sys.argv[1:], "c:n:t:lm:", ["concurrency", "requests", "timeout", "longconn","modname"])  
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
        print '\t-t timeout      Seconds to max. wait for each response. Default is 10000 microseconds'
        print 'uri:'
        print '\thttp://127.0.0.1/aaaaa?a=1'
        print '\thttps://127.0.0.1/aaa?a=1'
        print '\tthrift://127.0.0.1:10000?args=json&mod=qfcommon.thriftclient.payprocessor.PayProcessor&name=PayProcessor'
        print 
        return
    
    start(uri, config.get('-c', 1), config.get('-n', 100), config.get('-l', 0), config.get('-t', 10000))


if __name__ == '__main__':
    logger.install('stdout')
    main()


