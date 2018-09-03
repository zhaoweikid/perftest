#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time
import json
import traceback


def interrupt(argv=None):
    result = []
    with open('/proc/interrupts') as f:
        headstr = f.readline()
        header = ['name'] + headstr.split()
        result.append(header)
        cores = len(header) - 1

        lines = f.readlines()
        for line in lines:
            if not ('Rescheduling' in line or 'Function call' in line or 'PCI-MSI' in line):
                continue
            p = line.strip().split()
            row = []
            name = ' '.join(p[cores+1:])
            row.append(name)

            for i in range(1, cores+1):
                if len(p) > i:
                     row.append(int(p[i]))
            if p[1]+p[2] == 0:
                continue
            result.append(row) 
    return result


def cpu(argv=None):
    fields = ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq','steal','quest','quest_nice']

    result = []
    result.append(fields)
    with open('/proc/stat') as f:
        lines = f.readlines()
        for ln in lines:
            if ln.startswith('cpu'):
                p = ln.strip().split()
                row = []
                row.append(p[0])
                row += [ int(x) for x in p[1:len(fields)]]
                result.append(row)
    return result




def proc_cpu(pid):
    fields = [['pid', 0],  
              ['min_flt', 9], ['cmin_flt', 10], ['maj_flt', 11], ['cmaj_flt', 12], 
              ['utime', 13], ['stime', 14], ['cutime', 15], ['cstime', 16], 
              ['num_threads', 19], ['rss', 23], ['rlim', 24], ['task_cpu', 38], ['task_policy', 40],
             ]
    result = []
    result.append(['name'] + [x[0] for x in fields])
    with open('/proc/%d/stat' % int(pid)) as f:
        p = f.readline().strip().split()
        row = []
        row.append(p[1][1:-1])

        for f in fields:
            if f[0] in ('comm', 'task_state'):
                row.append(p[f[1]])
            else:
                row.append(int(p[f[1]]))
        result.append(row)
    return result

def mem(argv=None):
    view_fields = ['MemTotal','MemFree','Buffers','Cached','SwapTotal','SwapFree','Mapped','Shmem','Slab','MemUsed']
    result = []
    with open('/proc/meminfo') as f:
        lines = f.readlines()
        
        fields = []
        row = ['mem']
        for ln in lines: 
            p = ln.strip().split()
            k = p[0].strip(':')
            if k in view_fields:
                fields.append(k)
                row.append(int(p[1])*1024)
        row.append(row[1]-row[2])
    result.append(['name'] + fields + view_fields[-1:])
    result.append(row)
    return result




def proc_mem(pid):
    result = [['name','res'], ]
    with open('/proc/%d/statm' % int(pid)) as f:
        p = f.readline().strip().split()
        row = int(p[1])*4096
        result.append(['mem', row])
    return result



def diskio(argv=None):
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


def proc_diskio(pid):
    result = []
    with open('/proc/%d/io' % int(pid)) as f:
        lines = f.readlines()
        header = ['name']
        row = ['io']

        for ln in lines:
            p = ln.strip().split()
            header.append(p[0].strip(':'))
            row.append(int(p[1]))
        result.append(header)
        result.append(row)
    return result
        

def netio(pid=None):
    result = []
    filename = '/proc/net/dev'
    if pid:
        filename = '/proc/%d/net/dev' % (int(pid))
    with open('/proc/net/dev') as f:
        lines = f.readlines()
        p = lines[1].strip().split('|') 
        p2 = p[1].split()
        header = ['name'] + ['recv_'+x for x in p2] + ['send_'+x for x in p2]
        
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

def proc_netio(pid):
    return netio_load(pid)



def proc_fd(pid):
    dirname = '/proc/%d/fd' % int(pid)
    result = [['name', 'fds'], ['fd', len(os.listdir(dirname))]]
    return result

def tcp(argv=None):
    filename = '/proc/net/snmp'
    result = []
    with open(filename) as f:
        lines = f.readlines()

        dataline = []
        for ln in lines:
            if not ln.startswith('Tcp:'):
                continue
            dataline.append(ln)

        header = ['name'] + dataline[0].strip().split()[5:]
        result.append(header)
        p = dataline[1].strip().split()[5:]
        result.append(['tcp'] + [ int(x) for x in p ])
    return result
             
def udp(argv=None):
    filename = '/proc/net/snmp'
    result = []
    with open(filename) as f:
        lines = f.readlines()

        dataline = []
        for ln in lines:
            if not ln.startswith('Udp:'):
                continue
            dataline.append(ln)

        header = ['name'] + dataline[0].strip().split()[1:]
        result.append(header)
        p = dataline[1].strip().split()[1:]
        result.append(['udp'] + [ int(x) for x in p ])
    return result
 


