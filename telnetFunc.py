# encoding=utf-8
import sys
import os
import logging
import logging.config
import time
import telnetlib
# import pexpect

logging.config.fileConfig("./logger.conf")
logger = logging.getLogger("logger01")

def doTelnet(ip,user,pswd):
    tn = telnetlib.Telnet(ip,port=23,timeout=10)
    tn.set_debuglevel(5)

    doCmd(tn,'login:',user)
    doCmd(tn,'Password:',pswd)

    checkTty(tn)

    doCmd(tn,'>','ls -l')

    # doCmd(tn,'>','')

    doCmd(tn,'>','pwd')

    doCmd(tn,'>','exit')

    printGBK(tn.read_all())

    tn.close()

def doTar(ip,user,pswd):
    tn = telnetlib.Telnet(ip,port=23,timeout=5)
    tn.set_debuglevel(5)

    doCmd(tn,'login:',user)
    doCmd(tn,'Password:',pswd)

    checkTty(tn)

    doCmd(tn,['>','#','$'],'ls -l')

    # doCmd(tn,'>','')

    doCmd(tn,['>','#','$'],'pwd')
    # doCmd(tn,'>','tar -cvf test-20170213.tar ./precomm ')

    doCmd(tn,['>','#','$'],'exit')

    printGBK(tn.read_all())

    tn.close()


def lsAllFiles(ip,user,pswd):
    tn = telnetlib.Telnet(ip,port=23,timeout=5)
    tn.set_debuglevel(0)

    doCmd(tn,'gin:',user)
    doCmd(tn,'Password:',pswd)

    checkTty(tn)

    # doCmd(tn,['>','#','$'],'ls -l')

    # doCmd(tn,'>','')

    doCmd(tn,['>','#','$'],'pwd')

    doCmd(tn,['>','#','$'],'find "/bak/move"|xargs ls -ld')

    rs = doCmd(tn,['>','#','$'],'exit')

    printGBK(tn.read_all())

    tn.close()

    print '---------------'
    print rs.decode('gbk')


def doCmd(tn,endstr,writestr):
    if isinstance(endstr,list):
        return doCmdWithEndstrList(tn,endstr,writestr)
    elif isinstance(endstr,str):
        return doCmdWithEndstr(tn,endstr,writestr)


def doCmdWithEndstr(tn,endstr,writestr):
    outstr = ''
    while True:
        # time.sleep()
        ret = tn.read_very_eager()
        if ret.strip() != '':
            outstr += ret

        # print 'ret=%s' % ret

        if outstr.rfind(endstr)>-1:
            print 'endstr=%s' % endstr
            printGBK(outstr)
            tn.write(writestr + '\n')
            break
    return outstr


def doCmdWithEndstrList(tn,endstrs,writestr):
    outstr = ''
    while True:
        # time.sleep()
        ret = tn.read_very_eager()
        if ret.strip() != '':
            outstr += ret

        # print 'ret=%s' % ret

        for endc in endstrs:
            # print 'endc=%s' % endc
            if ret.rfind(endc)>-1:
                print '================================'
                print 'ret=%s,endc=%s' % (ret,endc)
                printGBK(outstr)
                tn.write(writestr + '\n')
                return outstr
        

'''
提示输入终端类型
'''
def checkTty(tn,endstr='>'):
    outstr = ''
    while True:
        # time.sleep()
        ret = tn.read_very_eager()
        if ret.strip() != '':
            outstr += ret
        if ret.rfind('>')>-1:
            printGBK(outstr)
            tn.write('' + '\n')
            break
        if ret.rfind('Terminal type?')>-1:
            printGBK(outstr)
            tn.write('vt100' + '\n')
            break
    return

def printGBK(str=''):
    # print str.decode('GBK')
    logger.debug(str.decode('GBK'))




def main():
    # ip = '107.6.141.134'
    # user = 'wasup'
    # pswd = 'pass.123'
    # doTar(ip,user,pswd)


    # ip = '107.6.61.103'
    # user = 'gtcg'
    # pswd = 'gtcg'

    # doTelnet(ip,user,pswd)

    ip = '107.6.61.79'
    user = 'maps'
    pswd = 'maps'    
    lsAllFiles(ip,user,pswd)


if __name__ == '__main__':
    main()