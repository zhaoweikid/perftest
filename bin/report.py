#!/usr/bin/python
# coding: utf-8
import os, sys
import datetime
import math
import pygal
import copy
import json
import pprint
import getopt
import traceback

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
    'mysql': {
        'diff':True,
        'format':[
            {'name':'mysql_aborted_clients', 'title':u'客户端异常关闭连接', 'fields':['Aborted_clients']},
            {'name':'mysql_conn', 'title':u'MySQL连接数', 'fields':['Connections','Aborted_connects']},
            {'name':'mysql_bytes', 'title':u'接受发送字节', 'fields':['Bytes_received','Bytes_sent']},
            {'name':'mysql_tmp_table', 'title':u'内存临时表数', 'fields':['Created_tmp_tables']},
            {'name':'mysql_tmp_disk_table', 'title':u'磁盘临时表数', 'fields':['Created_tmp_disk_tables']},
            {'name':'mysql_tmp_file', 'title':u'临时文件数', 'fields':['Created_tmp_files']},
            {'name':'mysql_read_first', 'title':u'索引第一条读取数，可能有全索引扫描', 'fields':['Handler_read_first']},
            {'name':'mysql_read_key', 'title':u'索引读取一条数', 'fields':['Handler_read_key']},
            {'name':'mysql_read_next', 'title':u'索引顺序读下一条数，有索引扫描', 'fields':['Handler_read_next']},
            {'name':'mysql_read_prev', 'title':u'索引顺序读上一条数，可能有逆排序', 'fields':['Handler_read_prev']},
            {'name':'mysql_read_rnd', 'title':u'根据固定位置读记录数，索引使用有问题', 'fields':['Handler_read_rnd']},
            {'name':'mysql_read_rnd_next', 'title':u'根据位置读下一条数，索引使用有问题', 'fields':['Handler_read_rnd_next']},
            {'name':'mysql_handler_write', 'title':u'插入一行数', 'fields':['Handler_write']},
            {'name':'mysql_handler_update', 'title':u'更新一行数', 'fields':['Handler_update']},
            {'name':'mysql_pool_reads', 'title':u'从磁盘/内存读取页数', 'fields':['Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests']},
            {'name':'mysql_data_fsync', 'title':u'数据fsync到磁盘数', 'fields':['Innodb_data_fsyncs', 'Innodb_data_pending_fsyncs']},
            {'name':'mysql_data_rw', 'title':u'从磁盘读写数据字节', 'fields':['Innodb_data_read', 'Innodb_data_write', 'Innodb_data_written']},
            {'name':'mysql_data_rws', 'title':u'从磁盘读写次数', 'fields':['Innodb_data_reads', 'Innodb_data_writes']},
            {'name':'mysql_log_write', 'title':u'日志写请求数', 'fields':['Innodb_log_writes', 'Innodb_log_write_requests', 'Innodb_os_log_pending_writes']},
            {'name':'mysql_log_write_byte', 'title':u'日志写入字节数', 'fields':['Innodb_os_log_written']},
            {'name':'mysql_log_pend', 'title':u'日志操作挂起数', 'fields':['Innodb_os_log_pending_fsyncs', 'Innodb_os_log_pending_writes']},
            {'name':'mysql_page', 'title':u'页操作数', 'fields':['Innodb_pages_created', 'Innodb_pages_read', 'Innodb_pages_written']},
            {'name':'mysql_lock_time', 'title':u'锁时间（毫秒）', 'fields':['Innodb_row_lock_time_avg', 'Innodb_row_lock_time_max']},
            {'name':'mysql_lock_time_all', 'title':u'锁总时间（毫秒）', 'fields':['Innodb_row_lock_time', 'Innodb_row_lock_time']},
            {'name':'mysql_lock_num', 'title':u'锁数量', 'fields':['Innodb_row_lock_waits']},
            {'name':'mysql_lock_wait', 'title':u'当前等待锁数量', 'fields':['Innodb_row_lock_current_waits']},
            {'name':'mysql_lock', 'title':u'立即完成/等待的锁数量', 'fields':['Table_locks_immediate','Table_locks_waited']},
            {'name':'mysql_row_read', 'title':u'读取行数', 'fields':['Innodb_rows_read']},
            {'name':'mysql_row_insert', 'title':u'插入行数', 'fields':['Innodb_rows_inserted']},
            {'name':'mysql_row_update', 'title':u'更新行数', 'fields':['Innodb_rows_updated']},
            {'name':'mysql_row_delete', 'title':u'删除行数', 'fields':['Innodb_rows_deleted']},
            {'name':'mysql_key_read', 'title':u'从内存/磁盘读取索引数', 'fields':['Key_reads', 'Key_read_requests']},
            {'name':'mysql_key_write', 'title':u'写入索引数据到内存/磁盘数', 'fields':['Key_writes', 'Key_write_requests']},
            {'name':'mysql_key_block', 'title':u'索引块使用数', 'fields':['Key_blocks_used','Key_blocks_unused','Key_blocks_not_flushed']},
            {'name':'mysql_open_file', 'title':u'当前打开文件数', 'fields':['Open_files']},
            {'name':'mysql_opened_file', 'title':u'打开文件数', 'fields':['Opened_files']},
            {'name':'mysql_open_tables', 'title':u'当前打开表数', 'fields':['Open_tables']},
            {'name':'mysql_opened_tables', 'title':u'打开表数', 'fields':['Opened_tables']},
            {'name':'mysql_query', 'title':u'执行请求数', 'fields':['Queries']},
            {'name':'mysql_slow_queries', 'title':u'慢查询数', 'fields':['Slow_queries']},
            {'name':'mysql_qcache', 'title':u'查询缓存命中数', 'fields':['Qcache_hits','Qcache_inserts']},
            {'name':'mysql_qcache_s', 'title':u'查询缓存中查询数', 'fields':['Qcache_queries_in_cache']},
            {'name':'mysql_select_full_join', 'title':u'没使用索引的联接数', 'fields':['Select_full_join']},
            {'name':'mysql_select_full_range_join', 'title':u'使用范围搜索的联接数', 'fields':['Select_full_range_join']},
            {'name':'mysql_select_range', 'title':u'在第一个表中使用范围联接数', 'fields':['Select_range']},
            {'name':'mysql_select_range_check', 'title':u'每一行数据后对键值进行检查的不带键值的联接数', 'fields':['Select_range_check']},
            {'name':'mysql_select_scan', 'title':u'对第一个表进行完全扫描的联接数', 'fields':['Select_scan']},
            {'name':'mysql_sort_scan', 'title':u'通过扫描表完成的排序的数量', 'fields':['Sort_scan']},
            {'name':'mysql_sort_rows', 'title':u'已经排序的行数', 'fields':['Sort_rows']},
            {'name':'mysql_sort_range', 'title':u'在范围内执行的排序的数量', 'fields':['Sort_range']},
            {'name':'mysql_sort_merge_passes', 'title':u'排序算法已经执行的合并的数量', 'fields':['Sort_merge_passes']},
            {'name':'mysql_threads_connected', 'title':u'当前打开的连接数', 'fields':['Threads_connected']},
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
    {'title':u'数据库', 'names':[ x['name'] for x in config['mysql']['format']]},
]

class MonitorData:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.view_fields_num = 20
        self.view_skip_none = True

        self.header = {}
        self.fields = []
        
        self.load()

    def load(self):
        with open(self.filename) as f:
            ln = f.readline()
            self.header = json.loads(ln.strip())
            self.fields = self.header.keys()

            while True:
                ln = f.readline()
                if not ln:
                    break
                obj = json.loads(ln.strip())
                for k in obj:
                    if k == 't':
                        continue
                    obj[k].insert(0, self.header[k])
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
        if not self.data:
            return
        
        result = {}
        for srcname, setting in config.iteritems():
            diff = setting['diff']
            fmt = setting['format']

        
            if srcname not in self.fields:
                continue

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
            t = datetime.datetime.fromtimestamp(onecheck['t'])
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
    def __init__(self, monitordata, data, filename):
        self.data = data
        self.filename = filename    
        self.monitor = monitordata

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
            names = v['names']
            for k in names:
                if k in self.monitor.fields:
                    self.draw(k)
                  
        self.f.write(a2)


def usage():
    print 'usage:\n\treport.py [options]'
    print 'options:'
    print '\t-o filename    output file'
    print '\t-m filename    monitor data file'
    print 
    print 'eg: ./report.py -o outfile -m monitor.dat'
    print


def main():
    try:  
        opts, args = getopt.getopt(sys.argv[1:], "o:m:", ["outfile", "monitor"])  
        config = dict([ (x[0], x[1])  for x in opts ])
    except:  
        traceback.print_exc()
        usage()
        return

    outfile = config.get('-o')
    mondata = config.get('-m')

    if not outfile or not mondata:
        usage()
        return

    mydata = MonitorData(mondata)
    result = mydata.format()

    dr = Drawer(mydata, result, outfile)
    dr.drawall()

if __name__ == '__main__':
    main()



