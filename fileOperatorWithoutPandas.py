# encoding=utf-8
import sys
import os,time
import json
import logging
import telnetFunc as tf
import cPickle as pickle
import iniReader as ir
import re
import ftpFunc

'''
__FILE__OP = 'tmpData/test.txt'
FILEINFO_IN_SERVER = 'tmpData/remote_file_info'
FILEINFO_LOCAL = 'tmpData/localinfo'
FILEINFO_TMP = 'tmpData/localtmp'
FILEINFO_MAP = 'tmpData/map.ini'   #存放 上次提交记录暂存文件和目录名 的对应关系
'''

logging.config.fileConfig("logger.conf")
logger = logging.getLogger("logger01")


class fileOperatorWithoutPandas(object):

    gen_file_path = './'
    # FILEINFO_IN_SERVER = ''
    # FILEINFO_LOCAL = ''
    # FILEINFO_TMP = ''
    # FILEINFO_MAP = ''

    def __init__(self,gen_file_path):
        self.gen_file_path = gen_file_path

    def init_file_path(self):
        self.FILEINFO_IN_SERVER = os.path.join(self.gen_file_path, 'qdata/remote_file_info')
        self.FILEINFO_LOCAL = os.path.join(self.gen_file_path,'qdata/localinfo')
        self.FILEINFO_TMP = os.path.join(self.gen_file_path,'qdata/localtmp')
        self.FILEINFO_MAP = os.path.join(self.gen_file_path,'qdata/map.ini')   #存放 上次提交记录暂存文件和目录名 的对应关系


    '''
    通过telnet拿某个目录下所有文件和目录的信息
    remote_dir = 需要获取信息的目录
    serverInfo = telnet登录信息的dict
    {'ip':ip,'user':user,'pswd':pswd,'port':port}
    bakflag = 备份服务目录，默认不备份

    tips:目录可能不存在

    '''
    def getRemoteFilesInfo(self,remote_dir,serverInfo,bakflag=False):
        # ip = '107.6.61.79'
        # user = 'maps'
        # pswd = 'maps'

        ip = serverInfo['hostip']
        user = serverInfo['user']
        pswd = serverInfo['pswd']

        dirname = remote_dir

        tn = tf.telnetlib.Telnet(ip,port=23,timeout=5)
        try:
            tn.set_debuglevel(0)

            tf.doCmd(tn,'login:',user)
            tf.doCmd(tn,'Password:',pswd)

            tf.checkTty(tn)

            # doCmd(tn,'>','')
            tf.doCmd(tn,['>','#','$'],'find ' + dirname + '|xargs ls -ld')

            rs = tf.doCmd(tn,['>','#','$'],'\n')

            # print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
            rss = rs.split('\r\n')

            #判断目录是否可能不存在
            #目录不存在的情况下： rss=['find /bak/tmp2017-2/|xargs ls -ld', 'find: 0652-010 The starting directory is not valid.', 'maps@MAPS79/home/maps>']
            if len(rss) == 3 and rss[1].rfind(r'find: 0652') >= 0:
                logger.debug('目录 %s 不存在' % remote_dir)
                rss[1] = '' #目录不存在的情况，将错误信息指置空

            #备份标志位True and 目录存在的情况下，备份
            #TODO 备份时机不对，TO BE FIXED
            if bakflag and rss[1] != '':
                tf.doCmd(tn,['>','#','$'],'cd ' + dirname)
                nowtimestmp = time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime(time.time()))
                tf.doCmd(tn,['>','#','$'],' tar -cvf BAK' + nowtimestmp + '.tar  ' + dirname)

            tf.doCmd(tn,['>','#','$'],'exit')

            #写入时，去除头和尾
            writeFile(self.FILEINFO_IN_SERVER,rss[1:-1])

            # tf.printGBK(tn.read_all())
        finally:
            tn.close()


    '''
    获取本地文件的信息，包括修改时间，大小等
    返回一个json
    filepath： 文件全路径
    '''
    def getLocalFileInfo(self,filepath):
        currentPath = filepath
        size = os.path.getsize(currentPath)
        # print 'size is %d' % size
        lastModifyTime = os.path.getmtime(currentPath)
        createTime = os.path.getctime(currentPath)
        #格式化日期时间
        lastModifyTime = time.localtime(lastModifyTime)
        lastModifyTime = time.strftime("%Y-%m-%dT%H:%M:%S",lastModifyTime)
        createTime = time.localtime(createTime)
        createTime = time.strftime("%Y-%m-%dT%H:%M:%S",createTime)

        #组合为json字符串
        datajson = {"filename":currentPath,"size":size,"lmtime":lastModifyTime,"ctime":createTime}

        return datajson


    '''
    #远程和本地对比，给出本地待上传列表
    remote_dir = 服务器待对比目录
    local_dir = 本地待对比目录
    serverInfo = 服务器telnet登录信息

    返回的是，相对路径表示的文件名路径

    '''
    def getDiffs(self,remote_dir,local_dir,serverInfo):

        #如果文件不存在，就写入一个空的文件头
        # if not os.path.exists(FILEINFO_LOCAL):
        #     writeFile(FILEINFO_LOCAL,["index,ctime,filename,lmtime,size,rel_filename"])

        if not os.path.exists(self.FILEINFO_MAP):
            writeFile(self.FILEINFO_MAP,["[SEQ]\nindex=1\n[FILEINFO]\n"])

        self.getRemoteFilesInfo(remote_dir,serverInfo)

        #格式化本地目录和文件信息
        fileinfo_list = list()
        if os.path.isfile(local_dir): #如果传入的参数是一个文件（只比较一个文件）
            datajson = self.getLocalFileInfo(local_dir)
            fileinfo_list.append(datajson)
        else:
            for parent,dirnames,filenames in os.walk(local_dir):
                for filename in filenames:
                    currentPath = os.path.join(parent,filename)

                    datajson = self.getLocalFileInfo(currentPath)

                    #将dict，放入list
                    fileinfo_list.append(datajson)


        #取本地目录的相对路径
        tmpDir = os.path.dirname(local_dir) 
        # tmpDir = os.path.dirname(tmpDir) 
        # _,dir_name = ftpFunc.checkType(None,local_dir)
        for json in fileinfo_list:
            json['rel_filename'] = os.path.relpath(json['filename'],tmpDir)

        # print 'fileinfo_list=%s' % fileinfo_list
        # print fileinfo_list
        #把本地的文件信息记录下来，作为最新的本地比对信息,把信息追加到文件
        self.saveDf(self.FILEINFO_TMP,fileinfo_list)

        # remote_info_file = FILEINFO_IN_SERVER
        # df_remote = pd.read_table(remote_info_file,sep='\\s+',names=['type','a','user','group','size','mon','day','year','filename'],encoding='gbk')  #,index_col='filename' 不指定索引
        # df_remote.drop(['a','user','group','mon','day','year'],axis=1,inplace=True)

        # #计算出相对路径，并新增1列
        # df_remote['rel_filename'] = df_remote['filename'].apply(lambda x:os.path.relpath(x,remote_dir))
        # df_remote['index'] = df_remote['rel_filename']
        # df_remote = df_remote.set_index('index')

        remote_fileinfo_list = self.readRemoteFileinfo(self.FILEINFO_IN_SERVER,remote_dir)

        print '--------------------------------------------------------------'

        # print 'remote_fileinfo_list=%s' % remote_fileinfo_list

        # print('aaaaaaaaaaaaaaaaaaa=\n%s\n%s\n%s\n%s\n' % (fileinfo_list,remote_fileinfo_list,local_dir,remote_dir))
        return self.compareLocalRemote(fileinfo_list,remote_fileinfo_list,local_dir,remote_dir)

    '''
    将服务器上的文件信息保存的文件，读取到list中
    '''
    def readRemoteFileinfo(self,filepath,remote_dir):
        relist = list()
        with open(filepath,'r') as fileHandle:
            for line in fileHandle:
                line = line.strip()
                # line = line.replace('\n','').replace('\r','')
                # print 'line=%s' % line

                if line == None or line == '':
                    continue

                ss = re.split('\\s+',line)
                # print 'ss=%s' % ss
                size = ss[4]
                filename = ss[8]
                rel_filename = os.path.relpath(filename,remote_dir)
                relist.append({'filename':filename,'size':size,'rel_filename':rel_filename})
        return relist



    '''
    比较2个list的内容

    返回最终需要上传的列表
    '''
    def compareLocalRemote(self,fileinfo_list,remote_fileinfo_list,local_dir = None,remote_dir = None):

        cf = ir.initConfiger(self.FILEINFO_MAP)

        #本地上次提交的dataframe
        last_df_save_filename,exist_flag = self.getDfFileName(cf,local_dir)
        # print 'last_df_save_filename=%s' % last_df_save_filename
        if not exist_flag:
            local_last_filelist = None
        else:
            local_last_filelist = self.loadDf(last_df_save_filename)

        # print 'local_last_filelist = %s' % local_last_filelist

        resultList1 = list()
        resultList2 = list()

        remote_index_list = self.getListByKey(remote_fileinfo_list,'rel_filename')
        local_index_list = self.getListByKey(fileinfo_list,'rel_filename')

        # logger.debug('remote_index_list = %s' % remote_index_list)
        # logger.debug('local_index_list = %s' % local_index_list)

        #第一步，比较远程和本地信息
        #第二部，比较本地信息和上次提交信息，如果修改时间和大小都没变，则不提交
        for rel_filename in local_index_list:
            file_dict = self.find_value(fileinfo_list,rel_filename,col='rel_filename')
            remote_file_dict = self.find_value(remote_fileinfo_list,rel_filename,col='rel_filename')
            # wholeFileName = file_dict['filename']
            if rel_filename not in remote_index_list:
                logger.debug('服务器端不存在文件 %s' % (rel_filename))
                resultList1.append(rel_filename)
            else:
                remote_size = long(file_dict['size'])
                local_size = long(remote_file_dict['size'])
                if remote_size != local_size:
                    logger.debug('服务器端文件 %s 大小不一致！' % (rel_filename))
                    logger.debug('remote_size = %s,type=%s' % (remote_size,type(remote_size)))
                    logger.debug('local_size = %s,type=%s' % (local_size,type(local_size)))
                    resultList1.append(rel_filename)

        # logger.debug( '待上传列表1= %s ' % resultList1 )
     
        if not exist_flag: #没有本地上次上传的记录,将这次的全部文件都要上传
            logger.debug('没有本地上次上传的记录,将这次的全部文件都要上传')
            resultList2 = self.getListByKey(fileinfo_list,'rel_filename')
        else:

            # print 'local_last_filelist = %s' % local_last_filelist
            local_last_index_list = self.getListByKey(local_last_filelist,'rel_filename')

            for filename in local_index_list:
                #如果已经确定需要上传，这里就不比较了
                if filename in resultList1:
                    continue
                if filename not in local_last_index_list:
                    #不在已有的传送记录中，需要上传
                    resultList2.append(filename)
                    continue

                last_file_dict = self.find_value(local_last_filelist,rel_filename,col='rel_filename')
                now_file_dict = self.find_value(fileinfo_list,rel_filename,col='rel_filename')

                last_size = last_file_dict['size']
                last_mtime = last_file_dict['lmtime']

                now_size = now_file_dict['size']
                now_mtime = now_file_dict['lmtime']

                # logger.debug('filename_index=%s' % filename)
                # logger.debug('last_size=%s,now_size=%s,last_mtime=%s,now_mtime=%s' % (last_size,now_size,last_mtime,now_mtime))

                if last_size != now_size or last_mtime != now_mtime:
                    logger.debug('大小或者修改时间与之前的记录不相符，需要提交:%s' % df_local.loc[filename]['filename'])
                    resultList2.append(filename)

        # logger.debug( '待上传列表2= %s ' % resultList2 )

        #2个list求并集
        # to_commit_list = [filename for filename in resultList1 if filename in resultList2]  #求交集
        to_commit_list = list(set(resultList1).union(set(resultList2)))
        print ''
        if len(to_commit_list) == 0:
            logger.info('%s:没有需要上传的文件' % (local_dir))
        else:
            logger.info('%s:需要上传的文件列表=\n %s' % (local_dir,to_commit_list))

        #最后，更新本地最新的文件记录,使用重命名的方式
        oldfile = self.FILEINFO_TMP
        newfile = last_df_save_filename

        if os.path.exists(newfile):
            os.remove(newfile)
        os.rename(oldfile ,newfile)
      
        return to_commit_list

    '''
    返回dataframe当时序列化的文件名路径
    如果不存在，则第二个返回None
    '''
    def getDfFileName(self,cf,localdir):
        #增加一个section
        sections = ir.getSecsions(cf)
        if 'FILEINFO' not in sections:
            cf.add_section('FILEINFO')

        localdir = os.path.normpath(localdir)
        localdir = localdir.replace(':','|').replace('=','-')  #将字符':','=' 替换成其他字符，防止ini文件解析异常

        #有映射就读取，没有就设置
        localdir_filename = ir.getItems(cf,'FILEINFO',localdir)
        if localdir_filename:
            # print ('在map文件中，存在 %s ' % localdir_filename)
            if not os.path.isfile(localdir_filename):  #文件不存在了
                return localdir_filename,None
            return localdir_filename,'Y'
        else :
            #不存在，就新增一个
            # print ('在map文件中，不存在 %s !!!' % localdir_filename)
            index = str(self.getNowIndex(cf,self.FILEINFO_MAP))
            # print ('获取的当前index=%s' % index)
            newfile = self.FILEINFO_LOCAL + '.' + index
            # print ('newfile=%s' % newfile)
            cf.set('FILEINFO',localdir,newfile)

        cf.write(open(self.FILEINFO_MAP,'wb'))
        return newfile,None


    def saveDf(self,filepath,df):
        #序列化
        with open(filepath,'w+') as fileHandle:
            pickle.dump(df,fileHandle) #protocol 0文本形式   1二进制


    def loadDf(self,filepath):
        #反序列化:
        f = file(filepath)
        df_t = pickle.load(f)
        return df_t

    #获取当前索引，取出后+1
    def getNowIndex(self,cf,filepath):
        #获取索引数字
        index = ir.getItems(cf,'SEQ','index')
        #索引增加1后，写回文件
        cf.set('SEQ','index',int(index)+1)
        cf.write(open(filepath,'wb'))
        return index


    def find_value(self,list,key,col = 'index'):
        for dict in list:
            if dict[col] == key:
                return dict


    def getListByKey(self,datalist,col):
        retlist = list()
        for dict in datalist:
            retlist.append(dict[col])
        return retlist





#========================================================================
#========================================================================


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
def writeFile(filepath,content,mode='w+'):
    #模式： w+会清除原有内容 a+会添加
    with open(filepath,mode) as fileHandle:
        #写入多行
        for line in content:
            fileHandle.writelines(''.join(line))
            fileHandle.write('\n')
        fileHandle.flush()



def main():
    # readFile(__FILE__OP)
    # writeFile(__FILE__OP)
    # getRemoteFilesInfo()



    serverInfo = {'hostip':'107.6.61.79','user':'maps','pswd':'maps'}
    # getDiffs(r'/bak/tmp2017',r'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\classes\com\icbc\cosp\yffk\tt.txt',serverInfo)

    # if not os.path.exists(FILEINFO_LOCAL):
    #     writeFile(FILEINFO_LOCAL,["index,ctime,filename,lmtime,size,rel_filename"])

    fowp = fileOperatorWithoutPandas('E:/pyworkspace/')
    fowp.init_file_path()
    fowp.getDiffs(r'/bak/tmp2017',r'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\classes\com\icbc\cosp\yffk\tt.txt',serverInfo)


    print 'done'
    pass

if __name__ == '__main__':
    main()
