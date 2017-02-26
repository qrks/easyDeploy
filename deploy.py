# encoding=utf-8
import sys
import os
import logging
import logging.config
import json

import iniReader
import ftpFunc

logging.config.fileConfig("./logger.conf")
logger = logging.getLogger("logger01")

# varMap={}
global local_workinfo_dict

def main():

    cf = iniReader.initConfiger('./deploy.ini')
    #read var 将所有的变量，转换成dict（key=变量名 value=变量值）
    varMap = iniReader.parse2Map(cf,'varset')
    logger.debug('读取到var=%s' % varMap)  
    #read put/get/move   读取这三个动作的section，并将下面所有的配置，转换成dict
    actionMap = iniReader.getActions(cf,['put','get','move'])
    logger.debug('读取到 actionMap=%s' % actionMap)
    #读取所有的服务器信息，转换成dict
    serverMap = iniReader.getActions(cf,['server'])
    logger.debug('读取到 serverMap=%s' % serverMap)

    #读取需要做的action列表
    todoActionStr = iniReader.getItems(cf,'actions','todo')
    todoActionList = parseStr2List(todoActionStr)
    logger.info('读取到 todoActionList=%s' % todoActionList)

    #拿本地工作目录
    global local_workinfo_dict
    local_workinfo_dict = iniReader.parse2Map(cf,'server:localhost')
    logger.debug('读取到 工作目录=%s' % local_workinfo_dict)


    #逐个处理action 
    for sectionName,record in actionMap.items():
        logger.info('开始处理[%s]' % sectionName)
        #将该动作标签下的内容，都转换成dict
        fieldsMap = iniReader.parse2Map(cf,sectionName)

        #put/get/move  获取动作名称
        action = sectionName.split(':')[0] 

        if action not in todoActionList:
            logger.info('%s 不需要处理' % sectionName)
            continue

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

    pass


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
                ftpFunc.upload(ftp,src_dir_one,dest_dir)
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
        
    logger.info('填充后的path=%s' % path)
    return path



if __name__ == '__main__':
    main()
    