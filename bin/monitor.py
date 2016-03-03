#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time

def interrupt_load():
    result = []
    with open('/proc/interrupts') as f:
        headstr = f.readline()
        header = ['id'] + headstr.split() + ['desc']

        cores = len(header) - 2
        while True:
            line = f.readline()
            if not line:
                break
            row = line.strip().split(None, 2)
            row[0] = row[0].strip(':')
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
                result.append(ln.strip().split())

    return




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
            row.append(p[f[1]])
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
            result.append(row)
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
            row.append(p[1]) 
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
            result.append(row)
    return result

def proc_netio_load(pid):
    return netio_load(pid)
 

def main(pid):
    data = {
        'interrupt': interrupt_load(),
        'cpu': cpu_load(),
        'pcpu': proc_cpu_load(pid),
        'mem': mem_load(),
        'pmem': proc_mem_load(pid),
        'diskio': diskio_load(),
        'pdiskio': proc_diskio_load(pid),
        'netio': netio_load(),
        'pnetid': proc_netio_load(pid),
    }



if __name__ == '__main__':
    import pprint
    x = globals()[sys.argv[1]]
    if len(sys.argv) > 2:
        ret = x(*sys.argv[2:])
    else:
        ret = x()

    head = ret[0]
    for x in ret[1:]:
        pprint.pprint(dict(zip(head, x)))





