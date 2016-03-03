#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time
import json

def interrupt_load():
    result = []
    with open('/proc/interrupts') as f:
        headstr = f.readline()
        header = ['name'] + headstr.split()
        result.append(header)
        cores = len(header) - 1

        lines = f.readlines()
        for line in lines:
            p = line.strip().split()
            row = []
            row.append(p[0].strip(':'))

            for i in range(1, cores+1):
                if len(p) > i:
                     row.append(int(p[i]))
            result.append(row) 
    return result


def cpu_load():
    fields = ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq']

    result = []
    result.append(fields)
    with open('/proc/stat') as f:
        lines = f.readlines()
        for ln in lines:
            if ln.startswith('cpu'):
                p = ln.strip().split()
                row = []
                row.append(p[0])
                row += [ int(x) for x in p[1:]]
                result.append(row)
    return result




def proc_cpu_load(pid):
    fields = [['pid', 0], ['comm', 1], ['task_state', 2], 
              ['min_flt', 9], ['cmin_flt', 10], ['maj_flt', 11], ['cmaj_flt', 12], 
              ['utime', 13], ['stime', 14], ['cutime', 15], ['cstime', 16], 
              ['num_threads', 19], ['rss', 23], ['rlim', 24], ['task_cpu', 38], ['task_policy', 40],
             ]
    result = []
    result.append([x[0] for x in fields])
    with open('/proc/%d/stat' % int(pid)) as f:
        p = f.readline().strip().split()
        row = []
        for f in fields:
            if f[0] in ('comm', 'task_state'):
                row.append(p[f[1]])
            else:
                row.append(int(p[f[1]]))
        result.append(row)
    return result

def mem_load():
    view_fields = ['MemTotal','MemFree','Buffers','Cached','SwapTotal','SwapFree','Mapped','Shmem','Slab']
    result = []
    with open('/proc/meminfo') as f:
        lines = f.readlines()
        
        fields = []
        row = []
        for ln in lines: 
            p = ln.strip().split()
            k = p[0].strip(':')
            if k in view_fields:
                fields.append(k)
                row.append(int(p[1])*1024)
    result.append(fields)
    result.append(row)
    return result




def proc_mem_load(pid):
    result = [['res'], ]
    with open('/proc/%d/statm' % int(pid)) as f:
        p = f.readline().strip().split()
        row = int(p[1])*4096
        result.append([row])
    return result



def diskio_load():
    fields = ['name', 'rio', 'rmerge', 'rsect', 'ruse', 'wio', 'wmerge', 'wsect', 'wuse', 'running', 'use', 'aveq']
    result = [fields]
    with open('/proc/diskstats') as f:
        lines = f.readlines()
        for ln in lines:
            row = ln.strip().split()[2:]
            if int(row[1]) + int(row[5]) == 0:
                continue
            result.append([row[0]] + [ int(x) for x in row[1:]])
    return result


def proc_diskio_load(pid):
    result = []
    with open('/proc/%d/io' % int(pid)) as f:
        lines = f.readlines()
        header = []
        row = []

        for ln in lines:
            p = ln.strip().split()
            header.append(p[0].strip(':'))
            row.append(int(p[1]))
        result.append(header)
        result.append(row)
    return result
        

def netio_load(pid=None):
    result = []
    filename = '/proc/net/dev'
    if pid:
        filename = '/proc/%d/net/dev' % (int(pid))
    with open('/proc/net/dev') as f:
        lines = f.readlines()
        p = lines[1].strip().split('|') 
        p2 = p[1].split()
        header = ['interface'] + ['recv_'+x for x in p2] + ['send_'+x for x in p2]
        
        result.append(header)
        n = len(header)-1
        for x in lines[2:]:
            p = x.strip().split()
            row = p
            row[0] = row[0].strip(':')
            for i in range(1, len(row)):
                row[i] = int(row[i])
            result.append(row)
    return result

def proc_netio_load(pid):
    return netio_load(pid)
 

def create(pid):
    data = {
        'time':time.time(),
        'interrupt': interrupt_load(),
        'cpu': cpu_load(),
        'mem': mem_load(),
        'diskio': diskio_load(),
        'netio': netio_load(),
    }

    if pid:
        pdata = {
            'pcpu': proc_cpu_load(pid),
            'pmem': proc_mem_load(pid),
            'pdiskio': proc_diskio_load(pid),
            'pnetid': proc_netio_load(pid),
        }
        data.update(pdata)

    return data

def main():
    #if len(sys.argv) == 1:
    #    print 'usage monitor datafile [pid]'
    #    return
    
    filename = ''
    f = sys.stdout
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename == 'stdout':
            filename = ''
        
    pid = None
    if len(sys.argv) > 2:
        pid = sys.argv[2]

    #print 'filename:%s pid:%s' % (filename, pid)

    if filename:
        f = open(filename, 'w+')
    try:
        while True:
            result = create(pid)
            wdata = json.dumps(result, separators=(',', ':'))
            #print len(wdata)
            f.write(wdata)
            f.write('\n')
            time.sleep(1)

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



