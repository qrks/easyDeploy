# -*- coding: utf-8 -*-
# encoding=utf-8
import sys
import os
import logging
import logging.config
import json

import iniReader
import ftpFunc
# import fileOperator
import fileOperatorWithoutPandas as fo
import telnetFunc as tf
import re

logging.config.fileConfig("logger.conf")
logger = logging.getLogger("logger01")

# varMap={}
global local_workinfo_dict
global ini_dir

def main():


    '''
    sys.argv[0] 脚本名
    sys.argv[1] 参数1
    sys.argv[2] 参数2
    ....
    '''
    '''
    #处理传入的参数
    参数1： ini配置文件
    根据ini文件所在目录，新建目录qdata
    '''
    logger.info('<<<<<< START >>>>>>')

    testflag = True
    deploy_ini = ''

    logger.info(sys.argv)

    if testflag:
        deploy_ini = 'E:/pyworkspace/deploy.ini'
    else :
        param_len = len(sys.argv)
        if (param_len != 2):
            logger.error("param mistake!")
            sys.exit(0)

        deploy_ini = str(sys.argv[1])


    global ini_dir
    ini_dir = os.path.dirname(deploy_ini)

    ini_dir = os.path.normpath(ini_dir)
    to_mk_dir = os.path.join(ini_dir,'qdata')
    if not os.path.exists(to_mk_dir):
        os.mkdir(to_mk_dir)


    cf = iniReader.initConfiger(deploy_ini)
    #read var 将所有的变量，转换成dict（key=变量名 value=变量值）
    varMap = iniReader.parse2Map(cf,'varset')
    logger.debug('读取到var=%s' % varMap)  
    #拿本地工作目录
    global local_workinfo_dict
    local_workinfo_dict = iniReader.parse2Map(cf,'server:localhost')
    logger.debug('读取到 工作目录=%s' % local_workinfo_dict)
    #read put/get/move   读取这三个动作的section，并将下面所有的配置，转换成dict
    actionMap = iniReader.getActions(cf,['put','get','move','ddl'])
    logger.debug('读取到 actionMap=%s' % actionMap)
    #读取所有的服务器信息，转换成dict
    serverMap = iniReader.getActions(cf,['server'])
    logger.debug('读取到 serverMap=%s' % serverMap)

    #读取需要获取的数据库DDL信息
    ddl_map = iniReader.getActions(cf,['ddl'])
    logger.debug('读取到 ddl_map=%s' % ddl_map)

    #读取需要做的action列表
    todoActionStr = iniReader.getItems(cf,'sys','todo')
    # logger.debug('todoActionStr=%s' % todoActionStr)
    todoActionList = parseStr2List(todoActionStr)
    logger.info('读取到 todoActionList=%s' % todoActionList)

    #=========================================================================

    # for ddl_section_name,_ in ddl_map.items():
    #     logger.info('开始处理[%s]' % ddl_section_name)
    #     #将该动作标签下的内容，都转换成dict
    #     ddl_allitems_map = iniReader.parse2Map(cf,ddl_section_name)
    #     # ddl_serverinfo_map = ddl_allitems_map.remove('items')
    #     #将items项目，转化成既定的格式
    #     ddl_items = ddl_allitems_map['items']
    #     ddl_item_list = getListByItems(ddl_items)

    #     logger.debug('=====================================')
    #     logger.debug('ddl_item_list = %s' % ddl_item_list)

    #     tf.db_get_ddl(ddl_allitems_map,ddl_item_list,ddl_allitems_map['output_file'])
    

    # print 'actionMap=%s' % actionMap
    
    # print 'actionMap=%s' % actionMap
    #逐个处理action record=section下具体的kv配置项
    for sectionName,record in actionMap.items():

        #put/get/....  获取动作名称
        action = sectionName.split(':')[0] 

        if action not in todoActionList:
            logger.info('%s 不需要处理' % sectionName)
            continue

        logger.info('开始处理[%s]' % sectionName)
        #数据库DDL处理
        if action == 'ddl':
            ddl_section_name = sectionName
            #将该动作标签下的内容，都转换成dict
            ddl_allitems_map = iniReader.parse2Map(cf,ddl_section_name)
            # ddl_serverinfo_map = ddl_allitems_map.remove('items')
            #将items项目，转化成既定的格式
            ddl_items = ddl_allitems_map['items']
            ddl_item_list = getListByItems(ddl_items)

            # logger.debug('=====================================')
            # logger.debug('ddl_item_list = %s' % ddl_item_list)

            tf.db_get_ddl(ddl_allitems_map,ddl_item_list,ddl_allitems_map['output_file'])

        #ftp操作
        elif action in ['put','get','move']:

            #将该动作标签下的内容，都转换成dict
            fieldsMap = iniReader.parse2Map(cf,sectionName)

            # serverName = sectionName.split(':')[1] 
            srcServer = fieldsMap['src']   #获取服务器名称
            destServer = fieldsMap['dest']
            relmap = fieldsMap['relmap']   #获取目录对应关系dict

            srcServerMap = iniReader.parse2Map(cf,'server:' + srcServer)  #获取服务器下的信息，转换成dict
            destServerMap = iniReader.parse2Map(cf,'server:' + destServer)

            # print '---------------------------'
            # print relmap

            reldataList = parseStr2List(relmap) #将对应关系的str，转换成list
            for rsMap in reldataList:
                kvStr = rsMap.split(':')
                dir_key = kvStr[0]   #对应关系的左边key
                dir_value = kvStr[1] #对应关系的右边value
                if dir_value.startswith('['):  #如果右边是以'['开头的，说明是个数组表示
                    valueList = parseStr2List(dir_value)
                    logger.debug('valueList=%s' % valueList)

                    for dir in valueList:
                        doActionInit(cf,sectionName,dir,dir_key,varMap,srcServerMap,destServerMap,action)

                        pass


                else:   #简单的1对1关系
                    doActionInit(cf,sectionName,dir_value,dir_key,varMap,srcServerMap,destServerMap,action)

                    '''
                    #重构
                    real_dir_value = iniReader.getItems(cf,sectionName,dir_value)   #带表达式的路径
                    real_dir_key = iniReader.getItems(cf,sectionName,dir_key)       #带表达式的路径
                    logger.debug('real_dir_key=[%s],real_dir_value=[%s]' % (real_dir_key,real_dir_value))
                    path_src = fillVarInPath(real_dir_key,varMap)     #转换后的真实路径
                    path_dest = fillVarInPath(real_dir_value,varMap)  #转换后的真实路径

                    logger.debug('todo %s:from %s to %s' % (action,srcServer,destServer))

                    doAction(action,srcServerMap,destServerMap,path_src,path_dest)
                    '''
        else:
            logger.error('暂不支持的类型')

    logger.info('<<<<<< END >>>>>>')



'''
执行具体action前的一些操作，包括填充正式路径，判断路径配置是否存在等
'''
def doActionInit(cf,sectionName,dir_value,dir_key,varMap,srcServerMap,destServerMap,action):
    real_dir_value = iniReader.getItems(cf,sectionName,dir_value)   #带表达式的路径
    real_dir_key = iniReader.getItems(cf,sectionName,dir_key)       #带表达式的路径

    if not real_dir_value or not real_dir_key:
        return

    logger.debug('real_dir_key=[%s],real_dir_value=[%s]' % (real_dir_key,real_dir_value))
    path_src = fillVarInPath(real_dir_key,varMap)     #转换后的真实路径
    path_dest = fillVarInPath(real_dir_value,varMap)  #转换后的真实路径

    # logger.debug('todo %s:from %s to %s' % (action,srcServer,destServer))

    doAction(action,srcServerMap,destServerMap,path_src,path_dest)


'''
str = TABLE:ma8811_flcpdx_custinfo,VIEW:[v1,v2],INDEX:idx_zzd_only,CONSTRAINT:PK_ONE,REF_CONSTRAINT:REFPK_TWO
return list(dict,dict,....):
    [{TABLE:ma8811_flcpdx_custinfo},{VIEW:v1},{VIEW:v2},....]
'''
def getListByItems(str):
    retList = []
    reldataList = parseStr2List(str) #将对应关系的str，转换成list

    # logger.debug('reldataList = %s' % reldataList)

    for rsMap in reldataList:
        kvStr = rsMap.split(':')
        key_type = kvStr[0]   #左边key
        value_objname = kvStr[1] #右边value

        # logger.debug('key_type,value_objname = %s:%s' % (key_type,value_objname))

        # new_dict = {}
        if value_objname.startswith('['):  #如果右边是以'['开头的，说明是个数组表示
            valueList = parseStr2List(value_objname)

            for obj in valueList:
                new_dict = {}
                new_dict[key_type] = obj
                retList.append(new_dict)
        else:  #普通的 1 vs 1
            new_dict = {}
            new_dict[key_type] = value_objname
            retList.append(new_dict)

    return retList


def getMapByStr(str):
    if str == None or str.strip() == '':
        return {}
    retMap = {}
    #去掉前后的‘{}’
    # str = str[1:len(str)-1]
    #ss，完整的对应关系记录 类似于dir1：dir2
    ss = str.split(',')
    print 'ss=%s' % ss
    print 'eval(ss)=%s' % eval(str)
    for record in ss:
        print 'record=%s' % record
        rs = record.split(':')
        #value是list
        retMap[rs[0]]=rs[1]
        if rs[1].startswith('['):
            print rs[1][1:len(rs[1])-1]
            rslist = [x for x in rs[1][1:len(rs[1])-1].split(',')]
            retMap[rs[0]]=rslist
        
    print retMap

    pass


'''
将字符串表示的list，转换成list
str='{dir1:dir2,dir3:[dir4,dir5,dir6],dir7:dir8}'
-->
list = ['dir1:dir2', 'dir3:[dir4,dir5,dir6]', 'dir7:dir8']
'''
def parseStr2List(str):
    index = 0;
    str = str[1:len(str)-1]
    flag = 0 #0未遇到[  #1遇到了[,等待] 
    nowSumStr = ''
    retList = []
    for char in str:
        if char == ',' and flag == 0:
            retList.append(nowSumStr)
            nowSumStr = ''
            index += 1
            continue
        elif char == ',' and flag == 1:
            pass
        elif char == '[':
            flag = 1
        elif char == ']':
            flag = 0

        nowSumStr += char
        index += 1

        if index == len(str): #最后一位了，插入
            retList.append(nowSumStr)
    return retList


'''
action: put/get/move
src： 源头一个dict，存放服务器信息
dest：目标一个dict，存放服务器信息
src_dir：源头路径,可能带逗号，表示多个路径
dest_dir：目标路径,可能带逗号，表示多个路径

'''
def doAction(action,src,dest,src_dir,dest_dir):

    logger.debug('step into doAction')
    logger.debug(action)
    logger.debug(src)
    logger.debug(dest)
    logger.debug(src_dir)
    logger.debug(dest_dir)
    logger.debug('doAction params above')

    global local_workinfo_dict

    if action == 'move':
        #TODO 
        #src -> dest
        #从src服务器上，从内容下载到本地工作目录
        workdir = local_workinfo_dict['workdir']
        try:
            ftpSrc = ftpFunc.ftpConnect(src['hostip'],21,src['user'],src['pswd'])
            ftpFunc.download(ftpSrc,src_dir,workdir)
        finally:
            ftpFunc.ftpQuit(ftpSrc)
        pass
    elif action == 'put':
        #src = local
        try:
            
            ftp = ftpFunc.ftpConnect(dest['hostip'],21,dest['user'],dest['pswd'])
            for src_dir_one in src_dir.split(','):
                #增量方式提交
                global ini_dir
                fowp = fo.fileOperatorWithoutPandas(ini_dir)
                fowp.init_file_path()
                to_upload_list = fowp.getDiffs(dest_dir,src_dir_one,dest)   #通过比对，获得增量需要上传的文件列表

                #判断上传的是一个目录还是一个文件
                if os.path.isfile(src_dir_one):
                    if len(to_upload_list) != 0: #是文件的情况下，如果返回的差别列表中有东西，说明需要上传
                        ftpFunc.uploadFile(ftp,src_dir_one,dest_dir)
                elif os.path.isdir(src_dir_one):        

                    for uploadfile in to_upload_list:
                        file = os.path.join(src_dir_one,uploadfile)
                        dest_tmp_dir = os.path.join(dest_dir,os.path.dirname(uploadfile))

                        #服务器端，目录转换'\'为‘/’
                        dest_tmp_dir = dest_tmp_dir.replace('\\','/')

                        # logger.debug('file=%s,dest_tmp_dir=%s' % (file,dest_tmp_dir))
                        ftpFunc.uploadFile(ftp,file,dest_tmp_dir)

                #全量方式
                # ftpFunc.upload(ftp,src_dir_one,dest_dir)

        finally:
            ftpFunc.ftpQuit(ftp)

        pass
    elif action == 'get':
        #src = remote
        try:
            ftp = ftpFunc.ftpConnect(src['hostip'],21,src['user'],src['pswd'])

            for src_dir_one in src_dir.split(','):
                ftpFunc.download(ftp,src_dir_one,dest_dir)
        finally:
            ftpFunc.ftpQuit(ftp)
        
        pass



'''
将路径中的变量，变换为实际值
'''
def fillVarInPath(path,varMap):
    beginFlag = 0 #0未开始 1开始匹配
    index = 0
    varName = ''
    varList = []
    for char in path:
        if char == '$':
            beginFlag = 1
        elif char == '}':
            beginFlag = 0
            varList.append(varName + char)
            varName = ''
        
        if beginFlag == 1:
            varName += char

        index += 1

    for var in varList:
        path = path.replace(var,varMap[var])      
        
    logger.debug('填充后的path=%s' % path)
    return path



if __name__ == '__main__':
    main()
    