#!/usr/bin/python 
# coding: utf-8 
import os, sys
import time

class Interrupt:
    def __init__(self, id, name, n):
        self.id = id
        self.name = name
        self.n = n

def interrupt_load():
    result = []
    with open('/proc/interrupts') as f:
        headstr = f.readline()
        header = ['id'] + headstr.split() + ['desc']
        print header

        cores = len(header) - 2
        while True:
            line = f.readline()
            if not line:
                break
            row = line.strip().split(None, 2)
            row[0] = row[0].strip(':')
            print row
            result.append(row)
    return result

class CPUCore:
    def __init__(self, user, nice, system, idle,
            iowait, irq, intr):
        self.user = user
        self.nice = nice
        self.system = system
        self.idle = idle
        self.iowait = iowait
        self.irq = irq
        self.intr = intr


def cpu_load(pid):
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
    print result
    return result


class Mem:
    def __init__(self, res):
        self.res = res


def mem_load(pid):
    pass



class DiskIO:
    def __init__(self, rchar, wchar, syscr, syscw,
            read_bytes, write_bytes, cancelled_write_bytes):
        self.rchar = rchar
        self.wchar = wchar
        self.syscr = syscr
        self.syscw = syscw
        self.read_bytes = read_bytes
        self.write_bytes = write_bytes
        self.cancelled_write_bytes = cancelled_write_bytes


def diskio_load():
    pass

class NetIO:
    def __init__(self, interface, recv_bytes, recv_packets, 
            recv_errs, recv_drop, recv_fifo, recv_frame,
            recv_compressed, recv_multicast,
            send_bytes, send_packets, send_errs,
            send_drop, send_fifo, send_frame,
            send_compressed, send_multicast):

        self.interface = interface
        self.recv_bytes = recv_bytes
        self.recv_packets = recv_packets 
        self.recv_errs = recv_errs
        self.recv_drop = recv_drop 
        self.recv_fifo = recv_fifo 
        self.recv_frame = recv_frame
        self.recv_compressed = recv_compressed 
        self.recv_multicast = recv_multicast
        self.send_bytes = send_bytes 
        self.send_packets = send_packets 
        self.send_errs = send_errs
        self.send_drop = send_drop 
        self.send_fifo = send_fifo 
        self.send_frame = send_frame
        self.send_compressed = send_compressed 
        self.send_multicast = send_multicast

def netio_load():
    pass


class DataRow:
    def __init__(self, fd, cpu, mem, diskio, netio):
        self.time = time.time()
        self.fd = fd
        self.cpu = cpu
        self.mem = mem
        self.diskio = diskio
        self.netio = netio




class Proc:
    def __init__(self, pid, count, rows):
        self.pid = pid
        self.count = count
        self.data = rows



if __name__ == '__main__':
    x = globals()[sys.argv[1]]
    if len(sys.argv) > 2:
        x(*sys.argv[2:])
    else:
        x()



