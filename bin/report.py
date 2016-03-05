#!/usr/bin/python
# coding: utf-8
import os, sys
import datetime
import pygal
import copy
import json
import pprint

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

        #result['interrupt'] = self._format_interrupt(self.data)   
        #result['cpu'] = self._format_cpu(self.data)   
        #result['mem'] = self._format_mem(self.data)   
        #result['swap'] = self._format_swap(self.data)   
        #result['diskio_n'], result['diskio_time'] = self._format_diskio(self.data)   
        #result['netio_n'], result['netio_byte'] = self._format_netio(self.data)   
        result['tcp'], result['tcp_seg'], result['tcp_cur'] = self._format_tcp(self.data)
        result['udp'], result['udp_err'] = self._format_udp(self.data)

        result['pfd'] = self._format_simple('pfd', self.data)
        result['pcpu'], result['pthread'] = self._format_pcpu(self.data)

        result['pmem'] = self._format_simple('pmem', self.data)
        result['pdiskio_n'], result['pdiskio_byte'] = self._format_pdiskio(self.data)   
        result['pnetio_n'], result['pnetio_byte'] = self._format_pnetio(self.data)   

        return result


    def _format_general(self, name, data):
        # data:  chart.cpu.xxxx, eg: rdata['interrupt_name']['cpu_name']
        rows = {'title':name, 'x':[], 'data':{}}
        rdata = rows['data']

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
                    x = {}
                    for k in h:
                        x[k] = []
                    rdata[r[0]] = x
               
                ydata = rdata[r[0]]
                for i in range(0, len(r)-1):
                    ydata[h[i]].append(r[i+1])

        return rows


    def _format_general_cha(self, name, data, nocha_fields=None):
        # data:  chart.cpu.xxxx, eg: rdata['interrupt_name']['cpu_name']
        rows = {'title':name, 'x':[], 'data':{}}
        rdata = rows['data']

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
                    x = {}
                    for k in h:
                        x[k] = []
                    rdata[r[0]] = x
               
                ydata = rdata[r[0]]
                for i in range(0, len(r)-1):
                    ydata[h[i]].append(r[i+1])


        def cha(alist):
            ret = []
            start = alist[0]
            for i in range(0, len(alist)):
                ret.append(alist[i] - start)
                start = alist[i]
            return ret

        rdata2 = {}
        for tk,y in rdata.iteritems():
            newdata = {}
            for yname,ydata in y.iteritems():
                if nocha_fields and yname in nocha_fields:
                    newdata[yname] = ydata
                    continue
                newdata[yname] = cha(ydata)
           
            rdata2[tk] = newdata

        rows['data'] = rdata2

        return rows



    def _format_simple(self, name, data):
        # data:  cpu.xxxx, eg: rdata['cpu_name']
        rows = {'title':name, 'x':[], 'data':{}}
        rdata = rows['data']

        for onecheck in self.data:
            t = datetime.datetime.fromtimestamp(onecheck['time'])
            # time, xdata
            rows['x'].append(str(t)[11:19])
        
            one = onecheck[name]
            h = one[0]

            if not rdata:
                for k in h:
                    rdata[k] = []

            for i in range(1, len(one)):
                r = one[i]
                for k in range(0, len(r)):
                    rdata[h[k]].append(r[k]) 

        return rows

    def _format_simple_cha(self, name, data, nocha_fields=None):
        rows = self._format_simple(name, data)
        def cha(alist):
            ret = []
            start = alist[0]
            for i in range(0, len(alist)):
                ret.append(alist[i] - start)
                start = alist[i]
            return ret

        rdata = rows['data']
        rdata2 = {}

        for yname,ydata in rdata.iteritems():
            if nocha_fields and yname in nocha_fields:
                rdata2[yname] = ydata
                continue
            rdata2[yname] = cha(ydata)
            
        rows['data'] = rdata2

        return rows

    
    def _format_interrupt(self, data):
        # data:  chart.cpu.xxxx, eg: rdata['interrupt_name']['cpu_name']
        rows = {'title':'interrupt', 'x':[], 'data':{}}
        rdata = rows['data']

        for onecheck in self.data:
            t = datetime.datetime.fromtimestamp(onecheck['time'])
            rows['x'].append(str(t)[:19])
            one = onecheck['interrupt']
            h = one[0][1:]
            for i in range(1, len(one)):
                r = one[i]
                if r[0] not in rdata:
                    x = {}
                    for k in h:
                        x[k] = []
                    rdata[r[0]] = x
               
                ydata = rdata[r[0]]
                for i in range(0, len(r)-1):
                    ydata[h[i]].append(r[i+1])

        for k,cpu in rdata.iteritems():
            for cpuid,cpulist in cpu.iteritems():
                start = cpulist[0]
                for i in range(0, len(cpulist)):
                    old = cpulist[i]
                    cpulist[i] = cpulist[i] - start
                    start = old


        return rows


    def _format_cpu(self, data):
        
        def cha(alist):
            ret = []
            start = alist[0]
            for i in range(0, len(alist)):
                ret.append(alist[i] - start)
                start = alist[i]
            return ret


        ret = self._format_general('cpu', data)
        rdata = ret['data']

        rdata2 = {}
        for tk,y in rdata.iteritems():
            newdata = {}
            for yname,ydata in y.iteritems():
                newdata[yname] = cha(ydata)
           
            keys = newdata.keys()
            datan = len(newdata[keys[0]])

            for i in range(0, datan):
                n = sum([ newdata[k][i]  for k in keys ])
                for k in keys:
                    if n > 0:
                        newdata[k][i] = newdata[k][i]/float(n)
                    else:
                        newdata[k][i] = 0

            rdata2[tk] = newdata

        ret['data'] = rdata2

        return ret

    def _format_pcpu(self, data):
        ret = self._format_general_cha('pcpu', data)

        ret_cpu = copy.deepcopy(ret)
        ret_thread = copy.deepcopy(ret)
       
        self._fields_filter(ret_cpu, ['utime', 'stime'])
        self._fields_filter(ret_thread, ['num_threads'])

        return ret_cpu, ret_thread



    def _format_mem(self, data):
        ret = self._format_simple('mem', data)

        rdata = ret['data']
        for k,v in rdata.iteritems():
            for i in range(0, len(v)):
                v[i] = v[i] / float(1024*1024)
        del rdata['SwapTotal']
        del rdata['SwapFree']
        return ret


    def _format_swap(self, data):
        ret = self._format_simple('mem', data)

        rdata = ret['data']
        for k,v in rdata.iteritems():
            for i in range(0, len(v)):
                v[i] = v[i] / float(1024*1024)

        for k in rdata.keys():
            if not k.startswith('Swap'):
                del rdata[k]

        return ret

    def _format_diskio(self, data):
        ret = self._format_general_cha('diskio', data)

        ret_n = copy.deepcopy(ret)
        ret_time = copy.deepcopy(ret)

        def fields_filter(obj, fields):
            rdata = obj['data']
            newdata = {}
            for tk,tdata in rdata.iteritems():
                newdata[tk] = {}
                newx = newdata[tk]
                for k,v in tdata.iteritems():
                    if k in fields:
                        newx[k] = v

            obj['data'] = newdata
       
        fields_filter(ret_n, ['rio', 'rmerge', 'rsect', 'wio', 'wmerge', 'wsect', 'running'])
        fields_filter(ret_time, ['ruse', 'wuse', 'use', 'aveq'])

        return ret_n, ret_time


    def _format_netio(self, data):
        ret = self._format_general_cha('netio', data)

        ret_n = copy.deepcopy(ret)
        ret_byte = copy.deepcopy(ret)
       
        self._fields_filter(ret_n, ["recv_packets","recv_errs","recv_drop","recv_fifo","recv_frame","recv_compressed","recv_multicast","send_packets","send_errs","send_drop","send_fifo","send_frame","send_compressed","send_multicast"])
        self._fields_filter(ret_byte, ["recv_bytes","send_bytes"])

        return ret_n, ret_byte


    def _format_pnetio(self, data):
        ret = self._format_general_cha('pnetio', data)

        ret_n = copy.deepcopy(ret)
        ret_byte = copy.deepcopy(ret)
       
        self._fields_filter(ret_n, ["recv_packets","recv_errs","recv_drop","recv_fifo","recv_frame","recv_compressed","recv_multicast","send_packets","send_errs","send_drop","send_fifo","send_frame","send_compressed","send_multicast"])
        self._fields_filter(ret_byte, ["recv_bytes","send_bytes"])

        return ret_n, ret_byte



    def _format_tcp(self, data):
        ret = self._format_general_cha('tcp', data, ['CurrEstab'])

        ret_tcp = copy.deepcopy(ret)
        ret_seg = copy.deepcopy(ret)
        ret_cur = copy.deepcopy(ret)

        self._fields_filter(ret_tcp, ['ActiveOpens', 'PassiveOpens', 'AttemptFails', 'EstabResets', 'InErrs', 'OutRsts'])
        self._fields_filter(ret_seg, ['InSegs', 'OutSegs','RetransSegs'])
        self._fields_filter(ret_cur, ['CurrEstab'])

        return ret_tcp, ret_seg, ret_cur

    def _format_udp(self, data):
        ret = self._format_general_cha('udp', data)

        ret_udp = copy.deepcopy(ret)
        ret_err = copy.deepcopy(ret)

        self._fields_filter(ret_udp, ['InDatagrams', 'OutDatagrams'])
        self._fields_filter(ret_err, ['InErrors','RcvbufErrors','SndbufErrors'])

        return ret_udp, ret_err


    def _format_pdiskio(self, data):
        ret = self._format_simple_cha('pdiskio', data)
        
        ret_n = copy.deepcopy(ret)
        ret_byte = copy.deepcopy(ret)

        self._fields_filter(ret_n, ['syscr', 'syscw'])
        self._fields_filter(ret_byte, ['rchar', 'wchar', 'read_bytes', 'cancelled_write_bytes'])

        return ret_n, ret_byte



    
    def _fields_filter(self, obj, fields):
        rdata = obj['data']
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

        obj['data'] = newdata


def draw(title, x, data):
    line = pygal.Line()
    line.title = title
    line.x_labels = x

    for k,row in data.iteritems():
        line.add(k, row)

    return line.render()


def main():
    outfile = sys.argv[2]
    outf = open(outfile, 'w')
    mydata = MonitorData(sys.argv[1])
    result = mydata.format()

    def stat(name):
        one = result[name]
        keys = one['data'].keys()
        keys.sort()
        for name in keys:
            value = one['data'][name]
            ret = draw(name, one['x'], value)
            outf.write(ret)

    def stat_simple(name):
        one = result[name]
        ret = draw(name, one['x'], one['data'])
        outf.write(ret)

   
    #stat('interrupt')
    #stat('cpu')
    #stat_simple('mem')
    #stat_simple('swap')
    #stat('diskio_n')
    #stat('diskio_time')
    #stat('netio_n')
    #stat('netio_byte')
    #stat('tcp')
    #stat('tcp_seg')
    #stat('tcp_cur')
    #stat('udp')
    #stat('udp_err')
    #stat_simple('pfd')
    #stat('pcpu')
    #stat('pthread')
    #stat_simple('pmem')
    #stat_simple('pdiskio_n')
    #stat_simple('pdiskio_byte')
    stat('pnetio_n')
    stat('pnetio_byte')

    outf.close()


if __name__ == '__main__':
    main()



