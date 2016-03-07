#!/usr/bin/python
# coding: utf-8
import os, sys
import datetime
import pygal
import copy
import json
import pprint


config = {
    'interrupt':{
        'diff':True,
        'format':[
            {'name':'interrupt', 'title':u'中断', 'fields':[]},
        ],
    },
    'cpu':{
        'diff':True,
        'rate':True,
        'format':[
            {'name':'cpu', 'title':u'CPU', 'fields':[]},
        ]
    },
    'mem':{
        'diff':False,
        'value_division':1024,
        'format':[
            {'name':'mem', 'title':u'内存(kb)', 'fields':['MemTotal','MemFree','Buffers','Cached','Slab','Shmem','Mapped']},
            {'name':'swap', 'title':u'交换分区(kb)', 'fields':['SwapTotal','SwapFree']},
        ]
    },
    'diskio':{
        'diff':True,
        'format':[
            {'name':'diskio_n', 'title':u'磁盘IO次数', 'fields':['rio', 'rmerge', 'rsect', 'wio', 'wmerge', 'wsect', 'running']},
            {'name':'diskio_time', 'title':u'磁盘IO字节数', 'fields':['ruse', 'wuse', 'use', 'aveq']},
        ]
    },
    'netio':{
        'diff':True,
        'format':[
            {'name':'netio_n', 'title':u'网络IO次数', 'fields':
                ["recv_packets","recv_errs","recv_drop","recv_fifo","recv_frame","recv_compressed","recv_multicast",
                 "send_packets","send_errs","send_drop","send_fifo","send_frame","send_compressed","send_multicast"]},
            {'name':'netio_b', 'title':u'网络IO字节', 'fields':["recv_bytes","send_bytes"]},
        ]
    },
    'tcp':{
        'diff':True,
        'nodiff_fields':['CurrEstab'],
        'format':[
            {'name':'tcp', 'title':u'TCP连接统计', 'fields':
                ['ActiveOpens', 'PassiveOpens', 'AttemptFails', 'EstabResets', 'InErrs', 'OutRsts']},
            {'name':'tcp_seg', 'title':u'TCP报文统计', 'fields':['InSegs', 'OutSegs','RetransSegs']},
            {'name':'tcp_cur', 'title':u'TCP当前连接统计', 'fields':['CurrEstab']},
        ]
    },
    'udp':{
        'diff':True,
        'format':[
            {'name':'udp', 'title':u'UDP报文统计', 'fields':['InDatagrams', 'OutDatagrams']},
            {'name':'udp_err', 'title':u'UDP错误', 'fields':['InErrors','RcvbufErrors','SndbufErrors']},
        ]
    },
    'pcpu':{
        'diff':True,
        'format':[
            {'name':'pcpu', 'title':u'进程CPU统计', 'fields':['utime','stime']},
            {'name':'pth', 'title':u'线程统计', 'fields':['num_threads']},
        ]
    },
    'pmem':{
        'diff':False,
        'format':[
            {'name':'pmem', 'title':u'进程内存统计', 'fields':['res']},
        ]
    },
    'pdiskio':{
        'diff':False,
        'format':[
            {'name':'pdiskio_n', 'title':u'进程磁盘IO次数统计', 'fields':['syscr', 'syscw']},
            {'name':'pdiskio_b', 'title':u'进程磁盘IO字节数统计', 'fields':
                ['rchar', 'wchar', 'read_bytes', 'cancelled_write_bytes']},
        ]
    },
    'pnetio':{
        'diff':True,
        'format':[
            {'name':'pnetio_n', 'title':u'进程网络IO次数统计', 'fields':
                ["recv_packets","recv_errs","recv_drop","recv_fifo","recv_frame","recv_compressed","recv_multicast",
                 "send_packets","send_errs","send_drop","send_fifo","send_frame","send_compressed","send_multicast"]},
            {'name':'pnetio_b', 'title':u'进程网络IO字节数统计', 'fields':["recv_bytes","send_bytes"]},
        ]
    },
    'pfd':{
        'diff':False,
        'format':[
            {'name':'pfd', 'title':u'进程描述符统计', 'fields':[]},
        ]
    },

}

class MonitorData:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        
        self.load()

    def load(self):
        with open(self.filename) as f:
            while True:
                ln = f.readline()
                if not ln:
                    break
                obj = json.loads(ln.strip())
                self.data.append(obj)

    def format(self):
        result = {}

        for srcname, setting in config.iteritems():
            diff = setting['diff']
            fmt = setting['format']

            ret = self._format_general(srcname, self.data, setting)
            for f in fmt:
                retx = copy.deepcopy(ret) 
                self._fields_filter(retx, f)
                result[f['name']] = retx

        return result


    def _format_general(self, name, data, fmt):
        # data:  chart.cpu.xxxx, eg: rdata['interrupt_name']['cpu_name']
        rows = {'title':name, 'x':[], 'data':{}}
        rdata = rows['data']

        diff = fmt.get('diff')
        rate = fmt.get('rate', False)
        nodiff_fields = fmt.get('nodiff_fields')
        value_division = fmt.get('value_division', 1)
        
        #fmtdict = dict( [ (x['name'], x['title']) for x in fmt['format'] ] )

        def create_graph(x, name, header):
            y = {}
            for k in header:
                y[k] = []
            x[name] = y
            return y


        for onecheck in self.data:
            t = datetime.datetime.fromtimestamp(onecheck['time'])
            # time, xdata
            rows['x'].append(str(t)[11:19])
            one = onecheck[name]
            # header
            h = one[0][1:]

            # data => graph.ydata
            for i in range(1, len(one)):
                r = one[i]

                if r[0] not in rdata:
                    create_graph(rdata, r[0], h)
                ydata = rdata[r[0]]
                for i in range(0, len(r)-1):
                    ydata[h[i]].append(r[i+1]/value_division)

        def differ(alist):
            ret = []
            start = alist[0]
            for i in range(0, len(alist)):
                ret.append(alist[i] - start)
                start = alist[i]
            return ret

        if diff:
            rdata2 = {}
            for tk,y in rdata.iteritems():
                newdata = {}
                for yname,ydata in y.iteritems():
                    if nodiff_fields and yname in nodiff_fields:
                        newdata[yname] = ydata
                        continue
                    newdata[yname] = differ(ydata)
               
                rdata2[tk] = newdata

            rows['data'] = rdata2

        if rate:
            rdata2 = {}
            for tk,y in rdata.iteritems():
                keys = y.keys()
                datan = len(y[keys[0]])
                newdata = {}
                for yname, ydata in y.iteritems():
                    newdata[yname] = ydata 
                
                for i in range(0, datan):
                    n = sum([ y[k][i]  for k in keys ])
                    for k in keys:
                        if n > 0:
                            newdata[k][i] = newdata[k][i]/float(n)
                        else:
                            newdata[k][i] = 0
                rdata2[tk] = newdata

            rows['data'] = rdata2

        return rows

    def _fields_filter(self, obj, fmt):
        fields = fmt['fields']
        rdata = obj['data']
        if fields:
            newdata = {}
            for tk,tdata in rdata.iteritems():
                if isinstance(tdata, dict):
                    newdata[tk] = {}
                    newx = newdata[tk]
                    for k,v in tdata.iteritems():
                        if k in fields:
                            newx[k] = v
                else:
                    if tk in fields:
                        newdata[tk] = tdata
            #obj['title'] = fmt['title'] + ' ' + obj['title'].split()[-1]
            obj['data'] = newdata


class Drawer:
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename    

        self.f = open(self.filename, 'w')

        self.conf_title = {}

        for k,s in config.iteritems():
            for one in s['format']:
                self.conf_title[one['name']] = one['title']



    def __del__(self):
        self.f.close()
    
    def _draw(self, title, x, data):
        line = pygal.Line()
        line.title = title
        line.x_labels = x

        for k,row in data.iteritems():
            line.add(k, row)

        return line.render()


    def draw(self, name):
        one = self.data[name]
        keys = one['data'].keys()
        keys.sort()
        for kname in keys:
            value = one['data'][kname]
            title = self.conf_title[name] + ' ' + kname
            ret = self._draw(title, one['x'], value)
            self.f.write(ret)

    def drawall(self):
        for k in self.data:
            self.draw(k)


def main():
    outfile = sys.argv[2]
    mydata = MonitorData(sys.argv[1])
    result = mydata.format()

    dr = Drawer(result, outfile)
    dr.drawall()


if __name__ == '__main__':
    main()



