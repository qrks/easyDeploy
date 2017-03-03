# encoding=utf-8
import sys
import os
import logging
import logging.config
import ConfigParser


logging.config.fileConfig("logger.conf")
logger = logging.getLogger("logger01")

def initConfiger(iniFile):
    cf = ConfigParser.ConfigParser()
    cf.read(iniFile)
    return cf


def getSecsions(cf):
    return cf.sections()


def getItems(cf, section, item):
    try:
        ret = cf.get(section,item)
    except Exception,e:
        logger.error(repr(e))
        return None
    return ret

#section下所有内容
def getOptions(cf,option):
    try:
        options = cf.options(option)
    except Exception,e:
        logger.error(repr(e))
        return []
    return options


'''
将section下的内容，映射为dict
'''
def parse2Map(cf,sectionName):
    retMap = {}
    for key in getOptions(cf,sectionName):
        value = getItems(cf,sectionName,key)
        retMap[key]=value
    return retMap


'''
获取需要处理的kyes(是个list)配置
keys=['put','get','move']
'''
def getActions(cf,keys):
    retMap = {}
    for section in getSecsions(cf):
        if section.rfind(':')>0:
            action = section.split(':')[0]
            if(action in keys):
               # retList.append(section)
               valuesMap = parse2Map(cf,section)
               retMap[section] = valuesMap

    return retMap
            
def test1():
    filepath = './tmpData/map.ini'
    cf = initConfiger(filepath)
    #获取索引数字
    index = getItems(cf,'SEQ','index')
    print(index)
    #索引增加1后，写回文件
    cf.set('SEQ','index',int(index)+1)

    #增加一个section
    sections = getSecsions(cf)
    if 'FILEINFO' not in sections:
        cf.add_section('FILEINFO')

    #有映射就读取，没有就设置
    if getItems(cf,'FILEINFO','src1'):
        print getItems(cf,'FILEINFO','src1')
    else :
        cf.set('FILEINFO','src1',index + index)

    cf.write(open(filepath,'wb'))




def main():
    # cf = initConfiger('./deploy.ini')

    # print parse2Map(cf,'varset')

    # print getActions(cf,'')

    print '--------------'
    # print getSecsions(cf)
    # print getOptions(cf,'get:gtcg-config')
    # print getItems(cf,'server:ftp-11','hostip')
    # print getItems(cf,'put:class-config','localdir')
    # print getItems(cf,'get:gtcg-config','remotedir')
    #

    # for item in getSecsions(cf):
    #     if item.startswith('server'):
    #         print 'server! name=%s' % item
    #         print item.split(':')[1:][0]
    #         for key in getOptions(cf,item):
    #             # print 'key=%s' % key
    #             value = getItems(cf,item,key)
    #             print '%s=%s' % (key,value)


    test1()

if __name__ == '__main__':
    main()