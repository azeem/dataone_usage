#!/usr/bin/python
import urllib, getopt, sys, datetime, shelve, lxml
from lxml.html import parse

def get_usage(accno, date):
    params = urllib.urlencode({'accNo' : accno, 'UsgMnth' : '%s-UnBilled' % date.strftime('%b-%Y'), 'serviceuserid':'null'})
    result = urllib.urlopen('http://data.bsnl.in/wps/PA_SfCareUsageDetails/UsageRecords?%s' % params)
    doc_tree = parse(result).getroot()
    elmnts= doc_tree.cssselect('.Table_Grid .content div')
    values = (float(elmnts[3].text), float(elmnts[4].text), float(elmnts[7].text))
    return values

def get_uptime():
    f = open( "/proc/uptime" )
    contents = f.read().split()
    f.close()
    return float(contents[0])

def help():
    print 'USAGE: ./bsnl.py -n<accno> [OPTIONS]'
    print '-h, --help       Print this help'
    print '-n, --accno=     Account Number'
    print '-m, --max=       Maximum usage in MB'
    print '-f, --format=    Output format in python str.format() syntax'
    print '                 defaults to "{chargeable:.1f}MB ({percent_chargeable:.1f}%)"'
    print '                     The following variables are available :'
    print '                     downlink           : Total downlink units (float)'
    print '                     uplink             : Total uplink units (float)'
    print '                     chargeable         : Total chargeable units (float)'
    print '                     percent_chargeable : Percentage chargeable units of --max'
    print '-c, --forcecache Force use of cache'
    print '-e, --cacheerror Use cached value in case of an error'
    print '-u, --uptime=    Use cached value if system uptime is less than given number'
    print '                 of seconds'
    print 'Author : Azeem Arshad'

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hn:m:f:u:ec', ['help', 'accno=', 'max=', 'format=', 'uptime=', 'cacheerror', 'forcecache'])
    except getopt.GetoptError:
        print 'Invalid Usage'
        help()
        return
    
    accno = None
    maximum = None
    uptime = None
    cache_error = False
    force_cache = False
    format = '{chargeable:.1f}MB ({percent_chargeable:.1f}%)'
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            return
        elif opt in ('-n', '--accno'):
            accno = int(arg)
        elif opt in ('-m', '--max'):
            maximum = int(arg)
        elif opt in ('-f', '--format'):
            format = arg
        elif opt in ('-e', '--cacheerror'):
            cache_error = True
        elif opt in ('-u', '--uptime'):
            uptime = int(arg)
        elif opt in ('-c', '--forcecache'):
            force_cache = True
    
    if not accno:
        print 'A valid Account Number is required'
        return
    
    cache = shelve.open('.bbs_%s.txt' % accno)
    flag = False

    if (uptime is not None and get_uptime() < uptime) or force_cache:
        flag = True
    else:
        try:
            usage = get_usage(accno, datetime.datetime.now())
            cache['usage'] = usage
            cache.sync()
        except (lxml.etree.XMLSyntaxError, pycurl.error, IndexError), e:
            if cache_error:
                flag = True
            else:
                print str(e)
                return
       
    if flag:
        if 'usage' not in cache:
            print 'No Cache Available'
            return
        usage = cache['usage']
    
    downlink, uplink, chargeable = usage
    percent_chargeable = (chargeable/maximum)*100 if maximum is not None else 0
    print format.format(downlink = downlink,
                        uplink = uplink,
                        chargeable = chargeable,
                        percent_chargeable = percent_chargeable)

if __name__ == '__main__':
    main(sys.argv[1:])
