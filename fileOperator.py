# encoding=utf-8
import sys
import os,time
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import telnetFunc as tf

__FILE__OP = './test.txt'
__FILEINFO_IN_SERVER = './test3.txt'

logging.config.fileConfig("./logger.conf")
logger = logging.getLogger("logger01")

def readFile_2(filepath):
    fileHandle = open(filepath,'r')
    try:
        # text = fileHandle.read()
        # print text

        for line in fileHandle:
            print line.decode('gbk')
        
    finally:
        fileHandle.close()


def readFile(filepath):
    with open(filepath,'r') as fileHandle:
        for line in fileHandle:
            print line.decode('gbk')


'''
content：1个待写入的list
'''
def writeFile(filepath,content):
    #模式： w+会清除原有内容 a+会添加
    with open(filepath,'w+') as fileHandle:
        #写入多行
        for line in content:
            fileHandle.writelines(''.join(line))
            fileHandle.write('\n')
        fileHandle.flush()

    pass


def test1(remote_dir_file,local_dir_file):
    #\\s+ 匹配任意空格，names指定列名，index_col指定索引列
    df = pd.read_table(remote_dir_file,sep='\\s+',names=['type','a','user','group','size','mon','day','year','name'],index_col='name',encoding='gbk')
    df.drop(['a','user','group','mon','day','year'],axis=1,inplace=True)

    df2 = pd.read_table(local_dir_file,sep='\\s+',names=['type','a','user','group','size','mon','day','year','name'],index_col='name',encoding='gbk')
    df2.drop(['a','user','group','mon','day','year'],axis=1,inplace=True)

    # print df
    #loc 获取某行
    print df.loc['/home/maps/src/sh/hmd/sql']['size']
    #iloc 通过行号（顺序）来获取
    print df.iloc[0]['type']
    #ix 结合前两种方法
    # print df.ix['size']

    print 'df1,df2 below'
    print df
    print df2

    # index_obj = df.index
    # index_obj2 = df2.index
    # print df.index
    # print df['size']
    # print df.equals(df2)

    print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'

    #遍历dataframe中的数据
    # for item in df2.index:
    #     print 'start'
    #     print 'item=%s' % item
    #     print 'filename=%s' % item.decode('gbk')

    #     print 'size=%s' % (df2.loc[item]['size'])
    #     # print df2.ix[item]['type']
    #     print 'end'

    print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'


    #df2和df进行对比，找出多的部分和变化的部分
    dflist = list(df.index)
    # print dflist
    for item in df2.index:
        if item not in dflist:
            print u'不存在项目：%s' % (item)
        else:
            if df.loc[item]['size'] != df2.loc[item]['size']:
                print u'项目 %s 大小不一致！' % (item)
                print df.loc[item]['size'],df2.loc[item]['size']

    # df.to_table('./test2.txt')


'''
通过telnet拿某个目录下所有文件和目录的信息
'''
def getRemoteFilesInfo(remote_dir):
    ip = '107.6.61.79'
    user = 'maps'
    pswd = 'maps'
    dirname = remote_dir

    tn = tf.telnetlib.Telnet(ip,port=23,timeout=5)
    try:
        tn.set_debuglevel(0)

        tf.doCmd(tn,'login:',user)
        tf.doCmd(tn,'Password:',pswd)

        tf.checkTty(tn)

        # doCmd(tn,'>','')
        tf.doCmd(tn,['>','#','$'],'find ' + dirname + '|xargs ls -ld')

        rs = tf.doCmd(tn,['>','#','$'],'exit')

        print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        rss = rs.split('\r\n')
        # print rss
        # print rs.decode('gbk')
        #写入时，去除头和尾
        writeFile(__FILEINFO_IN_SERVER,rss[1:-1])

        # tf.printGBK(tn.read_all())
    finally:
        tn.close()


#远程和本地对比，给出本地待上传列表
def getDiffs(remote_dir,local_dir):

    getRemoteFilesInfo(remote_dir)

    #格式化本地目录和文件信息
    fileinfo_list = list()
    for parent,dirnames,filenames in os.walk(local_dir):
        for dirname in dirnames:
            # print 'parent is ' + parent
            print 'dirname is ' + dirname
        for filename in filenames:
            # print 'parent is ' + parent
            # print 'filename is ' + filename
            currentPath = os.path.join(parent,filename)
            print 'the full path is ' + currentPath
            size = os.path.getsize(currentPath)
            print 'size is %d' % size
            lastModifyTime = os.path.getmtime(currentPath)
            createTime = os.path.getctime(currentPath)
            lastModifyTime = time.localtime(lastModifyTime)
            lastModifyTime = time.strftime("%Y-%m-%dT%H:%M:%S",lastModifyTime)
            #组合为json字符串
            datajson = {"filename":currentPath,"size":size,"lmtime":lastModifyTime,"ctime":createTime}
            #使用dumps进行格式化
            json_str = json.dumps(datajson)
            #将格式化后的str，转换成python对象
            jd = json.loads(json_str)
            # print jd
            print '================================'
            #将dict，放入list
            fileinfo_list.append(datajson)

            # print 'lastModifyTime=%s,createTime=%s' % (lastModifyTime,createTime)

    # print fileinfo_list
    #将list构建成dataframe
    df_local = pd.DataFrame.from_records(data=fileinfo_list) #,index='filename'   不指定索引
    tmpDir = os.path.dirname(local_dir) #取本地目录的相对路径
    df_local['rel_filename'] = df_local['filename'].apply(lambda x:os.path.relpath(x,tmpDir))
    #新建index列，来作为索引
    df_local['index'] = df_local['rel_filename']
    df_local = df_local.set_index('index')
    # df2.to_csv('./test5.csv')

    remote_info_file = __FILEINFO_IN_SERVER
    df_remote = pd.read_table(remote_info_file,sep='\\s+',names=['type','a','user','group','size','mon','day','year','filename'],encoding='gbk')  #,index_col='filename' 不指定索引
    df_remote.drop(['a','user','group','mon','day','year'],axis=1,inplace=True)

    #计算出相对路径，并新增1列
    df_remote['rel_filename'] = df_remote['filename'].apply(lambda x:os.path.relpath(x,remote_dir))
    df_remote['index'] = df_remote['rel_filename']
    df_remote = df_remote.set_index('index')

    print '------------------------'

    compareLocalRemote(df_local,df_remote,tmpDir,remote_dir)


'''
比较2个dataframe的内容
'''
def compareLocalRemote(df_local,df_remote,local_dir,remote_dir):

    # logger.debug('df_local=%s' % df_local)
    # logger.debug('df_remote=%s' % df_remote)

    retmote_filelist = list(df_remote.index)

    for filename in df_local.index:
        if filename not in retmote_filelist:
            print u'不存在项目：%s' % (filename)
        else:
            remote_size = df_remote.loc[filename]['size']
            local_size = df_local.loc[filename]['size'] 
            # print type(remote_size)
            # print type(local_size)
            # print 'remote_size=%s,local_size=%s' % (remote_size,local_size)
            if remote_size != local_size:
                print u'项目 %s 大小不一致！' % (filename)



def filePathTest():
    print os.path.basename("d:/agasdg/sgasg/asd")  #获取文件名
    print os.path.dirname("d:/asgasg/sgag/sag")    #获取路径
    print os.path.isfile("d:/asgasgas/asdg")       #判断是否是文件
    print os.path.normpath("d:/agasg/asgagsdg/sd/")#规范path字符串形式
    print os.path.relpath("/bak/move/2355.dfh/",'/bak/')#从第二个参数开始计算相对路径


def main():
    # readFile(__FILE__OP)
    # writeFile(__FILE__OP)
    # getRemoteFilesInfo()
    getDiffs(r'/bak/tmp2017',r'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\config\contributions\yffk\opg')



    print 'done'
    pass

if __name__ == '__main__':
    main()
