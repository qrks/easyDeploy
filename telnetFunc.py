# encoding=utf-8
import sys
import os
import logging
import logging.config
import time
import telnetlib
# import pexpect
import fileOperatorWithoutPandas as fo
# import fileOperator

logging.config.fileConfig("logger.conf")
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
            # print 'endstr=%s' % endstr
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
            if ret.rfind(endc) > -1:
                # print '================================'
                # print 'ret=%s,endc=%s' % (ret,endc)
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
    #不打印咯
    pass 
    # logger.debug(str.decode('GBK'))


'''
通过sqlplus，来获取建表语句，建立索引的语句
ddl_obj_list: 一个list，每一个都是一个dict key=type，name
'''
def db_get_ddl(server_info,ddl_obj_list,output_file):

    # hostip = '107.6.13.46'
    # user = 'oracle'
    # pswd = 'pass.123'
    # db_user = 'cospn'
    # db_pswd = 'cospn'

    hostip = server_info['hostip']
    user = server_info['user']
    pswd = server_info['pswd']
    db_user = server_info['db_user']
    db_pswd = server_info['db_pswd']
    db_service_name = server_info['db_service_name']

    #文件清空
    fo.writeFile(output_file,'','w+')

    tn = telnetlib.Telnet(hostip,port=23,timeout=8)
    try:
        tn.set_debuglevel(0)

        doCmd(tn,'gin:',user)
        doCmd(tn,'Password:',pswd)

        checkTty(tn)

        # doCmd(tn,['>','#','$'],'ls -l')

        # doCmd(tn,'>','')

        doCmd(tn,['>','#','$'],'pwd')

        doCmd(tn,['>','#','$'],' sqlplus ' + db_user + '/' + db_pswd + '@' + db_service_name)

        #设置显示，防止分段
        doCmd(tn,['>','#','$'],' set linesize 180 ')

        doCmd(tn,['>','#','$'],' set long 99999 ')

        doCmd(tn,['>','#','$'],' set pagesize 50000 ')

        #去除storage等多余参数
        #execute dbms_metadata.set_transform_param(dbms_metadata.session_transform,'STORAGE',false);
        doCmd(tn,['>','#','$'],' execute dbms_metadata.set_transform_param(dbms_metadata.session_transform,\'STORAGE\',false); ')

        for item in ddl_obj_list:
            type,obj_name = item.items()[0]
            logger.info('get %s:%s ...' % (type,obj_name))
            doCmd(tn,['>','#','$'],' select dbms_metadata.get_ddl(\'' + type + '\',upper(\'' + obj_name + '\')) as ddl from dual; ')
            #获取结果
            rs = doCmd(tn,['>','#','$'],'\n')
            rs = getUsefulText(rs,type)
            rs_list = list(rs.split('\r\n'))

            if type == 'TABLE':
                #获取注释
                cmd_str = ' select \'comment on column \'||\'' + obj_name + '.\'||column_name||\' is \'\'\'||comments||\'\'\';\'  as ccc from user_col_comments  where table_name = upper(\'' + obj_name + '\') and comments is not null; '          
                doCmd(tn,['>','#','$'],cmd_str)
                rs = doCmd(tn,['>','#','$'],'\n')
                rs = getUsefulText(rs,'COMMENT')
                comment_rs_list = list(rs.split('\r\n'))
                rs_list.extend(comment_rs_list)
            fo.writeFile(output_file,rs_list,'a+')
            #写入分隔符
            fo.writeFile(output_file,['----------------------------------------------------------------------'],'a+')

        '''
        #table
        table_name = 'ma8147_hostdetail'
        type = 'TABLE'
        logger.info('get %s:%s ...' % (type,table_name))
        doCmd(tn,['>','#','$'],' select dbms_metadata.get_ddl(\'' + type + '\',upper(\'' + table_name + '\')) from dual; ')
        rs = doCmd(tn,['>','#','$'],'\n')

        #index
        index_name = 'idx_zzd_only'
        type = 'INDEX'
        logger.info('get %s:%s ...' % (type,index_name))
        doCmd(tn,['>','#','$'],' select dbms_metadata.get_ddl(\'' + type + '\',upper(\'' + index_name + '\')) from dual; ')
        rs2 = doCmd(tn,['>','#','$'],'\n')
        '''

        doCmd(tn,['>','#','$'],'exit')

        doCmd(tn,['>','#','$'],'exit')

        # printGBK(tn.read_all())
    finally:
        tn.close()

    # print '---------------'
    # print rs.decode('gbk')

    '''
    #去除干扰内容
    rs = getUsefulText(rs,'TABLE')
    print '---------------'
    print rs.decode('gbk')
    print '---------------'
    rs2 = rs = getUsefulText(rs2,'INDEX')
    print rs2.decode('gbk')
    '''

'''
从sql命令结果中，过滤掉无用的信息
type: COMMENT:
'''
def getUsefulText(str,type):

    ret = str.replace('SQL>','')

    # logger.debug('str=%s' % str)

    if type == 'TABLE':
        str = str.replace('SQL>','')
        start_pos = str.find('CREATE TABLE')
        
    elif type == 'INDEX':
        str = str.replace('SQL>','')
        start_pos = str.find('CREATE')
    elif type == 'COMMENT':
        if str.find('no rows selected') >= 0:
            return ''

        str = str.replace('SQL>','')

        start_pos = str.rfind('-----')  + len('-----')
        end_pos = str.rfind(';')
        logger.debug('start_pos=%s,end_pos=%s' % (start_pos,end_pos))
        ret = str[start_pos:end_pos]
        # ret = str
        return ret
    else:
        str = str.replace('SQL>','')
        start_pos = str.find('CREATE')

    if start_pos < 0:  #没定位到具体的信息
        start_pos = 0
    ret = str[start_pos:]

    return ret


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
    # lsAllFiles(ip,user,pswd)

    db_get_ddl()


if __name__ == '__main__':
    main()