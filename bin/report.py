#!/usr/bin/python
# coding: utf-8
import os, sys
import datetime
import math
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
        'value_division':1024*1024,
        'format':[
            {'name':'mem', 'title':u'内存(MB)', 'fields':['MemTotal','MemUsed','Buffers','Cached','Shmem'],},
            {'name':'mem_map', 'title':u'内存Mapped(MB)', 'fields':['Mapped']},
            {'name':'mem_slab', 'title':u'内存Slab(MB)', 'fields':['Slab']},
            {'name':'swap', 'title':u'交换分区(MB)', 'fields':['SwapTotal','SwapFree']},
        ]
    },
    'diskio':{
        'diff':True,
        'format':[
            {'name':'diskio_n', 'title':u'磁盘读写次数', 'fields':['rio', 'wio']},
            {'name':'diskio_nmrg', 'title':u'磁盘合并读写次数', 'fields':['rmerge', 'wmerge']},
            {'name':'diskio_nsec', 'title':u'磁盘扇区读写次数', 'fields':['rsect', 'wsect']},
            {'name':'diskio_b', 'title':u'磁盘读写时间(毫秒)', 'fields':['ruse', 'wuse', 'use']},
        ]
    },
    'netio':{
        'diff':True,
        'format':[
            {'name':'netio_n', 'title':u'数据包收发次数', 'fields':["recv_packets","send_packets"]},
            {'name':'netio_nerr', 'title':u'网络读写错误次数', 'fields':["recv_errs","recv_drop","send_errs","send_drop"]},
            {'name':'netio_nfi', 'title':u'网络队列错误次数', 'fields':["recv_fifo","send_fifo"]},
            {'name':'netio_nfr', 'title':u'网络链路层帧错误次数', 'fields':["recv_frame","send_frame"]},
            {'name':'netio_b', 'title':u'网络读写字节', 'fields':["recv_bytes","send_bytes"]},
        ]
    },
    'tcp':{
        'diff':True,
        'nodiff_fields':['CurrEstab'],
        'format':[
            {'name':'tcp', 'title':u'TCP已建立连接统计', 'fields':['ActiveOpens', 'PassiveOpens']},
            {'name':'tcp_err', 'title':u'TCP错误统计', 'fields':['AttemptFails','InErrs']},
            {'name':'tcp_rst', 'title':u'TCP连接reset统计', 'fields':['EstabResets','OutRsts']},
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
        'func':'_format_proc_cpu',
        'format':[
            #{'name':'pcpu', 'title':u'进程CPU统计', 'fields':['utime','stime','cutime','cstime']},
            {'name':'pcpu', 'title':u'进程CPU统计', 'fields':['cpu']},
            {'name':'pth', 'title':u'线程统计', 'fields':['num_threads']},
        ]
    },
    'pmem':{
        'diff':False,
        'value_division':1024,
        'format':[
            {'name':'pmem', 'title':u'进程内存统计 (KB)', 'fields':['res']},
        ]
    },
    'pdiskio':{
        'diff':True,
        'format':[
            {'name':'pdiskio_n', 'title':u'进程系统调用读写次数统计', 'fields':['syscr', 'syscw']},
            {'name':'pdiskio_bsys', 'title':u'进程系统调用读写字节数统计', 'fields':['rchar', 'wchar']},
            {'name':'pdiskio_bsys_real', 'title':u'进程磁盘真实读写字节数统计', 'fields':['read_bytes', 'write_bytes']},
            {'name':'pdiskio_bc', 'title':u'进程取消写入字节数统计', 'fields':['cancelled_write_bytes']},
        ]
    },
    'pnetio':{
        'diff':True,
        'format':[
            {'name':'pnetio_n', 'title':u'进程数据包收发次数', 'fields':["recv_packets","send_packets"]},
            {'name':'pnetio_nerr', 'title':u'进程网络读写错误次数', 'fields':["recv_errs","recv_drop","send_errs","send_drop"]},
            {'name':'pnetio_nfi', 'title':u'进程网络队列错误次数', 'fields':["recv_fifo","send_fifo"]},
            {'name':'pnetio_nfr', 'title':u'进程网络链路层帧错误次数', 'fields':["recv_frame","send_frame"]},
            {'name':'pnetio_b', 'title':u'进程网络读写字节', 'fields':["recv_bytes","send_bytes"]},

        ]
    },
    'pfd':{
        'diff':False,
        'format':[
            {'name':'pfd', 'title':u'进程描述符统计', 'fields':[]},
        ]
    },

}


views = [ 
    {'title':u'内存统计', 'names':['mem', 'mem_map', 'mem_slab', 'pmem'],},
    {'title':u'CPU统计',  'names':['cpu','pcpu'],},
    #{'title':u'磁盘IO',   'names':['diskio_n', 'diskio_nmrg', 'diskio_nsec', 'diskio_b', 'pdiskio_n','pdiskio_bsys','pdiskio_bsys_real','pdiskio_bc'],},
    {'title':u'磁盘IO',   'names':['diskio_n', 'diskio_nmrg', 'diskio_nsec', 'diskio_b', 'pdiskio_n','pdiskio_bsys','pdiskio_bsys_real']},
    #{'title':u'网络IO',   'names':['netio_n','netio_nerr','netio_nfi','netio_nfr','netio_b','pnetio_n','pnetio_nerr','pnetio_nfi','pnetio_nfr','pnetio_b'],},
    {'title':u'网络IO',   'names':['netio_n','netio_nerr','netio_b','pnetio_n','pnetio_nerr','pnetio_b'],},
    {'title':u'TCP统计',  'names':['tcp','tcp_err','tcp_rst', 'tcp_seg', 'tcp_cur'],},
    {'title':u'UDP统计',  'names':['udp', 'udp_err']},
    {'title':u'文件描述符统计', 'names':['pfd']},
    {'title':u'线程统计', 'names':['pth']},
    {'title':u'中断统计', 'names':['interrupt']},
]

class MonitorData:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.view_fields_num = 20
        self.view_skip_none = True
        
        self.load()

    def load(self):
        with open(self.filename) as f:
            while True:
                ln = f.readline()
                if not ln:
                    break
                obj = json.loads(ln.strip())
                self.data.append(obj)


    def merge(self, data):
        '''merge many data to one'''
        rdata = data['data']
        k = rdata.keys()[0]
        kx = rdata[k].keys()[0]
        fn = len(rdata[k][kx])
        if fn <= self.view_fields_num:
            return data
      
        step = fn/self.view_fields_num
        data['x'] = [ data['x'][a] for a in range(0,len(data['x']),step)] 
        #newdata = copy.deepcopy(data)
        newrdata = {}
        for k,v in rdata.iteritems():
            newrdata[k] = {}
            for k2,v2 in v.iteritems():
                newv2 = []
                for i in range(0, len(v2), step):
                    newv2.append(int(math.ceil(float(sum(v2[i:i+step]))/len(v2[i:i+step]))))
                newrdata[k][k2] = newv2
        data['data'] = newrdata

        return data

    def format(self):
        result = {}

        for srcname, setting in config.iteritems():
            diff = setting['diff']
            fmt = setting['format']
            
            if 'func' in setting:
                ret = getattr(self, setting['func'])(srcname, self.data, setting)
            else:
                ret = self._format_general(srcname, self.data, setting)
            for f in fmt:
                retx = copy.deepcopy(ret) 
                self._fields_filter(retx, f)
                result[f['name']] = self.merge(retx)
                #result[f['name']] = retx
                self._skip_none(result[f['name']])

        return result

    def _skip_none(self, data):
        rdata = data['data']
        if self.view_skip_none:
            delk = []
            for k,g in rdata.iteritems():
                n = 0
                for gk, gv in g.iteritems():
                    n += sum(gv)
                if n == 0:
                    delk.append(k)

            for k in delk:
                del rdata[k]


    def _format_proc_cpu(self, name, data, fmt):
        cpu_fmt = copy.deepcopy(config['cpu'])
        cpu_fmt['rate'] = False
        cpu_data  = self._format_general('cpu', data, cpu_fmt)
        pcpu_data = self._format_general(name, data, fmt)

        rdata = pcpu_data['data']
        cpu_stat = cpu_data['data']['cpu']
        cpu_fields = cpu_stat.keys()

        cores = len(cpu_data['data'].keys())-1

        gname = rdata.keys()[0]
        pcpu_fields = ['stime','utime','cstime','cutime']
        rdata2 = {gname:{'cpu':[], 'num_threads':rdata[gname]['num_threads']}}

       
        for i in range(0, len(rdata[gname][pcpu_fields[0]])):
            pn = sum([ rdata[gname][k][i] for k in pcpu_fields ])
            an = sum([ cpu_stat[k][i] for k in cpu_fields ])
            v = 0
            if an > 0:
                v = round(float(pn)/an * 100 * cores, 2)
            rdata2[gname]['cpu'].append(v)

        pcpu_data['data'] = rdata2

        return pcpu_data

      

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
            if not alist:
                return alist
            ret = []
            start = alist[0]
            for i in range(0, len(alist)):
                ret.append(alist[i] - start)
                start = alist[i]
            return ret

        if diff:
            #rdata = rows['data']
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
            rdata = rows['data']
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
                            newdata[k][i] = round(newdata[k][i]/float(n) * 100, 2)
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
    
    def _draw(self, name, title, x, data):
        if name == 'mem':
            #line = pygal.StackedLine(fill=True, x_label_rotation=30, show_x_labels=False)
            line = pygal.Line(x_label_rotation=30, show_x_labels=False)
        else:
            line = pygal.Line(x_label_rotation=30, show_x_labels=False)
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
            ret = self._draw(kname, title, one['x'], value)
            ret = ret.replace('<svg ', '<svg width=600 ')
            self.f.write(ret)

    def drawall_v1(self):
        a1 = '''<html xmlns=http://www.w3.org/1999/xhtml>
<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>测试结果</title>
</head>
<body>
'''
        a2 = '</body></html>'
        self.f.write(a1)
        for k in self.data:
            head = '<div style="height:50px;text-align:center">%s</div>'  % k
            self.f.write(head)
            self.draw(k)

        self.f.write(a2)

    def drawall(self):
        a1 = '''<html xmlns=http://www.w3.org/1999/xhtml>
<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>测试结果</title>
</head>
<body>
'''
        a2 = '</body></html>'
        self.f.write(a1)

        global views
       
        for v in views:
            head = u'<div style="height:50px;text-align:center;margin:10px;font-size:18pt;font-weigth:bold;">%s</div>'  % v['title']
            self.f.write(head.encode('utf-8'))
            for k in v['names']:
                self.draw(k)
                  
        self.f.write(a2)



def main():
    outfile = sys.argv[2]
    mydata = MonitorData(sys.argv[1])
    result = mydata.format()

    dr = Drawer(result, outfile)
    dr.drawall()


if __name__ == '__main__':
    main()



