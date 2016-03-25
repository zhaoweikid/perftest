#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time
import json
import types
import getopt
import traceback
import plugin

HOME = os.path.dirname(os.path.abspath(__file__))

funcs = {}

def create(pid):
    data = {
        't':time.time(),
    } 
    
    for name,func in funcs.iteritems():
        ret = None
        if name.startswith('proc_'):
            if pid:
                ret = func(pid)
        else:
            ret = func()

        if ret:
            data[name] = ret

    return data

def split_header(data):
    header = {}
    body = {}
    for k,v in data.iteritems():
        if k == 't':
            body[k] = v
            continue
        header[k] = v[0]
        body[k] = v[1:]

    return header, body

def main():
    try:  
        opts, args = getopt.getopt(sys.argv[1:], "o:p:t:", ["outfile", "pid", "second"])  
        config = dict([ (x[0], int(x[1]))  for x in opts ])
    except:  
        traceback.print_exc()
        print 'usage:\n\tmonitor [options]'
        print 'options:'
        print '\t-o filename    output file'
        print '\t-p pid         process id'
        print '\t-t second      check interval. default 1'
        print 
        print 'eg: ./monitor.py -o outfile -p 1234'
        print
        return

    filename = config.get('-o', 'stdout')
    pid = config.get('-p', None)
    interval = int(config.get('-t', 1))

    #print 'outfile:%s pid:%s' % (filename, pid)

    global funcs
    for k, v in plugin.__dict__.iteritems():
        if type(v) == types.ModuleType and v.__name__.startswith('plugin'):
            for name, func in v.__dict__.iteritems():
                if type(func) == types.FunctionType and not name.startswith('_'):
                    funcs[name] = func 


        
    f = sys.stdout
    if filename and filename != 'stdout':
        f = open(filename, 'w+')

    write_header = False
    try:
        while True:
            result = create(pid)
            head, body = split_header(result)
            if not write_header:
                write_header = True
                f.write(json.dumps(head, separators=(',', ':')))
                f.write('\n')
            #wdata = json.dumps(result, separators=(',', ':'))
            wdata = json.dumps(body, separators=(',', ':'))
            #print len(wdata)
            f.write(wdata)
            f.write('\n')
            time.sleep(interval)

    finally:
        if filename:
            f.close()



def test():
    import pprint
    x = globals()[sys.argv[1]]
    if len(sys.argv) > 2:
        ret = x(*sys.argv[2:])
    else:
        ret = x()

    head = ret[0]
    for x in ret[1:]:
        pprint.pprint(dict(zip(head, x)))


if __name__ == '__main__':
    main()



