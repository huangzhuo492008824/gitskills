#/usr/bin/py
#-*-coding:utf-8
import time,os
import sys
import MySQLdb
import logging

def get_ip_extend():
    ip_all = os.popen('ifconfig').read().split('\n\n')
    for i in ip_all:
        if i.find('eth')!=-1:

            tmp=' '.join(i.split('\n')[1].split())
            if tmp.split()[1].find(':')!=-1:
                ipaddress=tmp.split()[1].split(':')[1]
            else:
                ipaddress=tmp.split()[1]
            if ipaddress.find('172.16.1') != -1:
                ipaddress_nei = ipaddress

            else:
                net_device_wai = i.split(' ')[0].split(':')[0]
    return net_device_wai,ipaddress_nei
   # return None,None,None,None

def get_hostname():
    return os.popen('hostname').read().split('\n')[0]

def get_date():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

def get_cpu_memory():
    '''
    return idle memory string MB
    return cpu_use % string
    '''
    global kernel
    if kernel > 3.0:
    #    print os.popen('top -bi -n 2 -d 0.02').read()
        top_cmd = os.popen('top -bi -n 2 -d 0.02').read().split('\n\n')[2]
        tmp = ' '.join(top_cmd.split('\n')[3].split(',')[2].split())
        memory_idle = "%.2f"%(float(tmp.split()[0])/1024)
        cpu_use="%.2f"%(100.00-float(top_cmd.split('\n')[2].split(',')[3].split()[0]))
        print memory_idle
    else:
        top_cmd = os.popen('top -bi -n 2 -d 0.02').read().split('\n\n\n')[1]
        memory_idle = "%.2f"%(float(top_cmd.split('\n')[3].split(',')[2].split('k')[0])/1024)
        cpu_use = "%.2f"%(100.00-float(top_cmd.split('\n')[2].split(',')[3].split('%')[0]))
    #print top_cmd
    


    return cpu_use,memory_idle

######################## get localdisk ######################
def get_localdisk():
    df_cmd = os.popen('df -l').read().split('\n')[1]
    idle_str = ' '.join(df_cmd.split())

    idle_MB = "%.2f"%(float(idle_str.split(' ')[3])/1024)
    return idle_MB

####################get net ################

def     rx():
        ifstat = open('/proc/net/dev').readlines()
        for interface in  ifstat:
                if INTERFACE in interface:
                        stat = float(interface.split()[1])
                        STATS[0:] = [stat]

def     tx(INTERFACE):
        ifstat = open('/proc/net/dev').readlines()
        for interface in  ifstat:
                if INTERFACE in interface:
                        return float(interface.split()[9])


def get_net_tx(INTERFACE):

    pre_byte = tx(INTERFACE)
    time.sleep(1)
    post_byte = tx(INTERFACE)

    print 'pre_byte',pre_byte
    print 'post_byte',post_byte
    return round((post_byte*1.00-pre_byte)/1024,2)

#######################  running ping cmd ###########
def run_ping(ip, times):

    os.popen('ping %s -c %d' % (ip,times))

if __name__ == '__main__':
    logging.basicConfig(filename='/var/log/get_cpu.log', level=logging.INFO, format='%(asctime)s %(message)s')
    time.sleep(80)
    logging.info('get_cpu.py start')
    global kernel
    pre_byte = -1
#set collect time:
    collect_time=120
    tmp=os.popen('uname -r').read().split('-')[0].split('.')
    kernel = float(tmp[0] + '.' + tmp[1])

    ip = '172.16.1.201'

    logging.info('starting ping 172.16.1.201 ten times')
    run_ping(ip, 10)
    logging.info(' ping 172.16.1.201 finished')
    logging.info('starting get cpu mem info')

    while True:
        logging.info('starting get internal ip and external ip')
        INTERFACE_WAI,IPADDRESS_NEI = get_ip_extend()
        logging.info('get internal ip and external ip finished')
    #    print get_net_tx(INTERFACE),"KB"
        if pre_byte == -1:
            pre_byte=tx(INTERFACE_WAI)
            time.sleep(1)
            post_byte=tx(INTERFACE_WAI)
            net_rate=round((post_byte*1.00-pre_byte)/1024,2)
            pre_byte=post_byte
        else:
            post_byte=tx(INTERFACE_WAI)
            net_rate=round((post_byte*1.00-pre_byte)/(1024*collect_time),2)
            pre_byte=post_byte

        logging.info('get net rate finished')

        hostname = get_hostname()
        cpu_use,memory_idle =  get_cpu_memory()
        date =  get_date()
        local_disk = get_localdisk()
        logging.info('get localdisk finished')

#        print date,INTERFACE,IPADDRESS,hostname,cpu_use,memory_idle,net_rate,local_disk

        logging.info('starting connect mysql and write monitor data')
        conn = MySQLdb.connect(host='172.16.1.201', user='root', passwd='123.com', port=3306)
        cursor = conn.cursor()

        sql_processor = "null, '%s', '%s', '%s', '%s', 'Processor', '"%(hostname, IPADDRESS_NEI, cpu_use, date)+ "% Processor Time', '_Total'"
        sql_memory = "null, '%s', '%s', '%s', '%s', 'Memory', 'Available MBytes', ''"%(hostname, IPADDRESS_NEI, memory_idle, date)
        sql_disk = "null, '%s', '%s', '%s', '%s', 'LogicalDisk', '"%(hostname, IPADDRESS_NEI, local_disk, date)+ "% Free Space', '_Total'"
        sql_net = "null, '%s', '%s', '%s', '%s', 'Network Interface', 'Bytes Total/sec', ''"%(hostname, IPADDRESS_NEI, net_rate, date)

        insert = cursor.execute("INSERT INTO privatecloud_hardware.performance VALUES(%s);" % sql_processor)
        insert = cursor.execute("INSERT INTO privatecloud_hardware.performance VALUES(%s);" % sql_memory)
        insert = cursor.execute("INSERT INTO privatecloud_hardware.performance VALUES(%s);" % sql_disk)
        insert = cursor.execute("INSERT INTO privatecloud_hardware.performance VALUES(%s);" % sql_net)
        conn.commit()


        cursor.close()
        conn.close()
        logging.info('write monitor data finished')

        time.sleep(collect_time)
        logging.info('one time collect finished')
  
