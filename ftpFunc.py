# encoding=utf-8
import sys
import ftplib
import os
import logging
import logging.config

__TYPE_FILE = 'FILE'
__TYPE_DIR = 'DIR'
__REMOTE_OS_SEP = '/'

logging.config.fileConfig("./logger.conf")
logger = logging.getLogger("logger01")

def ftpConnect(ip,port,user,pswd):
    try:
        ftp = ftplib.FTP()
        logger.info('connecting %s' % ip)
        ftp.connect(ip,port)
        ftp.login(user,pswd)
    except:
        logger.error('connect to %s failed!' % (ip))
        sys.exit(0)
    logger.info ('%s login success!' % ip)
    return ftp


def ftpQuit(ftp):
    try:
        if ftp:
            ftp.quit()
    finally:
        if ftp:
            ftp = None


'''
上传localdir目录下所有的内容到remotedir
结果和ftp客户端保持一致
例如： 传入 d:/work/ /home/maps/
结果：
d:/work/ -> /home/maps/work/ (会新建work目录)
'''
def uploadDir(ftp,localdir='./',remotedir='./'):
    #目录尾部判断
    localdir = checkDirEndstr(localdir)
    remotedir = checkDirEndstr(remotedir)

    if not os.path.isdir(localdir):
        return

    tmps = removeEndstr(localdir)
    #解析出本地目录最后的目录名
    to_mk_local_dir = os.path.split(tmps)[-1:][0]

    #判断远程目录是否存在，并cd
    remotedir = remotedir + to_mk_local_dir
    remotedir = checkDirEndstr(remotedir)
    cwdAndMkdir(ftp,remotedir)

    for file in os.listdir(localdir):
        src = os.path.join(localdir,file)
        # logger.debug( 'src:%s' % src )
        if os.path.isfile(src):
            _uploadFile(ftp,src,remotedir + file)
        elif os.path.isdir(src):
            try:
                # ftp.mkd(file) 
                pass
            except:
                pass
                # logger.debug('dir [%s] is exists' % (file))
            # uploadDir(ftp,src,remotedir + file)
            uploadDir(ftp,src,remotedir)
    ftp.cwd('..')


'''
localdir = path + name
remotedir = path + name
如果远程目录不存在，会报错
内部使用
'''
def _uploadFile(ftp,localdir,remotedir='./'):
    logger.debug('localdir,remotedir=%s,%s' % (localdir,remotedir))
    if not os.path.isfile(localdir):
        return
    logger.info('upload file [%s] ...' % localdir)
    ftp.storbinary('STOR ' + remotedir,open(localdir,'rb'))


'''
localfile = path + name 文件名
remotedir = path 目录
如果远程目录不存在，会建立
'''
def uploadFile(ftp,localfile,remotedir='./'):
    # logger.debug('localfile,remotedir=%s,%s' % (localfile,remotedir))
    if not os.path.isfile(localfile):
        return
    logger.info('upload file [%s] ...' % localfile)
    cwdAndMkdir(ftp,remotedir)
    remotedir = checkDirEndstr(remotedir)
    filetype,filename = checkType(ftp,localfile)
    ftp.storbinary('STOR ' + remotedir + filename,open(localfile,'rb'))



#判断src是文件还是目录，是文件的话，解析出文件名
def checkType(ftp,src):
    if os.path.isfile(src):
        src = removeEndstr(src)
        filename = os.path.split(src)[-1:][0]
        return __TYPE_FILE,filename
    elif os.path.isdir(src):
        return __TYPE_DIR,''


def checkType_old(ftp,src):
    if os.path.isfile(src):
        index = src.rfind('\\')
        if index == -1:
            index = src.rfind(r'/')
        return __TYPE_FILE,src[index+1:]
    elif os.path.isdir(src):
        return __TYPE_DIR,''


'''
src:  本地目录和文件名/本地目录
dest: 目标目录
'''
def upload(ftp,src,dest='./'):
    filetype,filename = checkType(ftp,src)
    # print('%s,%s' % (filetype,filename))
    if filetype == __TYPE_DIR:
        # print('uploadDir..')
        uploadDir(ftp,src,dest)
    elif filetype == __TYPE_FILE:
        # print('uploadFile..')
        #上传文件，需要拼接成完成的目标目录+文件名
        _uploadFile(ftp,src,dest)


'''
下载文件函数，
localdir = path + dir  本地目录
remoteFile = path + filename  远程文件
和ftp客户端下载后的结果保持一致
'''
def downloadFile(ftp,remoteFile,localdir):

    print 'in func:downloadFile:%s,%s' % (remoteFile,localdir)

    logger.info('download file [%s] ...' %  remoteFile)

    remote_dirFile = os.path.split(remoteFile)
    #split path and filename
    remote_filename = remote_dirFile[-1:][0]
    remote_dir = remote_dirFile[0:-1][0]

    ftp.cwd(remote_dir)
    # localdir = removeEndstr(localdir)
    # localdir = os.path.join(localdir,remote_dir)
    # localdir += remote_dir

    print 'localdir=%s' % localdir
    #本地目录如果不存在，则建立
    if not os.path.isdir(localdir):
        os.makedirs(localdir)
    localdir = checkDirEndstr(localdir)
    wFile = open(localdir + remote_filename,'wb')
    ftp.retrbinary('RETR ' + remoteFile,wFile.write)
    wFile.close()


'''
/home/maps/ -> d:/work/
下载目录下所有内容到本地
2个参数都是目录
等于在ftp客户端中，选中一个目录，下载下来
'''
def downloadDir(ftp,remotedir,localdir):
    #目录尾部判断
    localdir = checkDirEndstr(localdir)
    
    logger.debug('localdir,remotedir=%s,%s' % (localdir,remotedir))

    #去除目录结尾的'/'符号，不然split获取最后一个目录名时会有问题
    remotedir = removeEndstr(remotedir)
    #rs = '/home/' , 'maps'
    rs = os.path.split(remotedir)
    #本地新建存放下载结果的目录
    localPutInDir = localdir + rs[-1:][0] 

    if not os.path.isdir(localPutInDir):
        logger.info('mkdir localPutInDir=%s' % localPutInDir)
        os.makedirs(localPutInDir)


    remotedir = checkDirEndstr(remotedir)
    ftp.cwd(remotedir)
    # nowRemotePath = ftp.pwd()
    linelist = []
    ftp.dir("",linelist.append)
    file_arr = get_file_list(linelist)
    logger.debug('file_arr=%s' % file_arr)
    #TODO
    for remoteFile in file_arr:
        remoteFileType = remoteFile[0]
        remoteFileName = remoteFile[1]
        
        if remoteFileType == '-':
            downloadFile(ftp,remotedir+remoteFileName,localPutInDir)
        elif remoteFileType == 'd':
            # local = os.path.join(localPutInDir,remoteFileName)
            downloadDir(ftp,remotedir+remoteFileName, localPutInDir)
    ftp.cwd('..')


'''
下载通用方法，可以下载 文件or目录
'''
def download(ftp,remote,local):
    remote_type = checkRemoteIsDir(ftp,remote)
    localdir = checkDirEndstr(local)
    if remote_type == __TYPE_DIR:
        downloadDir(ftp,remote, localdir)
    elif remote_type == __TYPE_FILE:
        downloadFile(ftp,remote,localdir)


'''
判断远程ftp某个路径是文件还是目录
返回 目录 or 文件
'''
def checkRemoteIsDir(ftp,remote):
    #目录尾部判断
    remote = removeEndstr(remote)
    #先判断远端待下载的是文件还是目录
    dirFile = os.path.split(remote)
    #split path and filename
    filename = dirFile[-1:][0]
    dir = dirFile[0:-1][0]

    try:
        ftp.cwd(remote)
    except ftplib.error_perm,e:
        info = repr(e)
        # print info
        if info.find('Failed to change directory') > 0:
            #说明不是目录
            return __TYPE_FILE

    #否则的话，是目录
    return __TYPE_DIR


#tips：目录中不能共有空格
def get_filename(line):
    pos = line.rfind(' ')
    # print 'pos=%s' % pos
    pos += 1
    file_arr = [line[0],line[pos:]]  #fileType,fileName
    # print 'get_filename return=%s' % file_arr
    return file_arr

def get_file_list(linelist):
    ret_arr = []
    for line in linelist:
        file_arr = get_filename(line)
        if file_arr[1] not in ['.','..']:
            ret_arr.append(file_arr)
    return ret_arr


'''
检查目录尾部是否有'/',没有则添上
'''
def checkDirEndstr(dir):
    if not (dir.endswith('/') or dir.endswith('\\')):
        dir = dir + "/"
    return dir


'''
去除目录尾部'/'
'''
def removeEndstr(dir):
    if dir.endswith('/') or dir.endswith('\\'):
        dir = dir[:-1]
    return dir


'''
ftp操作中，切换目录时，如果目录不存在，则新建目录
ftp:ftp句柄
remotedir:需要cd的目录
toMkdir:需要新建的目录list
'''
def cwdAndMkdir(ftp,remotedir,toMkdirList=list()):
    try:
        ftp.cwd(remotedir)
        # print 'cd %s ok!' % remotedir
        # print 'toMkdirList=%s' % toMkdirList
        # print len(toMkdirList)
        if toMkdirList and len(toMkdirList) !=0:
            toMkdir = toMkdirList[-1]
            ftp.mkd(toMkdir)

            logger.info('mkdir %s @ %s' % (toMkdir,ftp.pwd())) 
            ftp.cwd(toMkdir)
            toMkdirList.remove(toMkdirList[-1])
            cwdAndMkdir(ftp,ftp.pwd(),toMkdirList)

    except ftplib.error_perm,e:
        # print repr(e)
        info = repr(e)
        if info.find('A file or directory in the path name does not exist') > 0:
            path_front = os.path.split(remotedir)[0]
            path_end = os.path.split(remotedir)[1]
            toMkdirList.append(path_end)
            # print 'path_front,toMkdirList=%s,%s' % (path_front,toMkdirList)
            cwdAndMkdir(ftp,path_front,toMkdirList)


def test1():
    try:
        # ftp = ftpConnect('107.6.141.134',21,'wasup','pass.123')
        # ftp = ftpConnect('107.6.61.11',21,'wasup','pass.123')
        ftp = ftpConnect('107.6.61.79',21,'maps','maps')
        # ftp = ftpConnect('107.6.61.103',21,'gtcg','gtcg')
        ftp.getwelcome()
        # print ftp.pwd()
        # print ftp.dir()
        # ftp.dir() 
        # fileUpolad = open('D:/sync2.log','rb')
        
        # upload(ftp,'D:/ImageTest','/home/wasup/tmp')
        # downloadFile(ftp,'/home/wasup/tmp/aaa.txt','d:/aaa.txt')

        # downloadDir(ftp,'/home/wasup/tmp/','D:/tmp/')
        # downloadDir(ftp,'/home/wasup/src/sh/ups/','D:/tmp/')
        # downloadDir(ftp,'/home/wasup/IBM/WebSphere/AppServer/profiles/AppSrv02/installedApps/TSHFHCOSPAPP01Node01Cell/G1S2_war.ear/G1S2.war/WEB-INF/classes/com/icbc/cosp/yffk/','D:/tmp/')
        
        # cwdAndMkdir(ftp,'/bak/a/b/')


        # print checkType('D:/tmp/')
        # download(ftp,'/bak/move/','D:/tmp/')
        # download(ftp,'/bak/notes.txt','D:/tmp/')
        # download(ftp,'/bak/move','D:/tmp')

        download(ftp,'/home/gtcg/GTCGProcessor/application/CITEICBC/CTBSH/trades/9998','D:/tmp2')
        # download(ftp,'/home/gtcg/GTCGProcessor/application/CITEICBC/CTBSH/trades/9998/message/BICE_TO_CITE.xml','D:/tmp2')

        # print os.path.split('/home/gtcg/GTCGProcessor/application/CITEICBC/CTBSH/trades/9998/message/BICE_TO_CITE.xml')
        


    finally:
        ftpQuit(ftp)


def test2():
    try:
        # ftp = ftpConnect('107.6.61.103',21,'gtcg','gtcg')
        ftp = ftpConnect('107.6.61.79',21,'maps','maps')
        ftp.getwelcome()

        # upload(ftp,'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\classes\com\icbc\cosp\yffk','/bak/tmp2017')
        # upload(ftp,'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\config\contributions','/bak/tmp2017')
        uploadFile(ftp,r'E:\CTP Developer\ide\workspace\G1S1_YFFK_web\WebContent\WEB-INF\config\contributions\yffk\opg\t81113.opg',r'/bak/tmp2017/tmp')
        
        

    finally:
        ftpQuit(ftp)


def main():
    # test1()
    test2()

    print 'done'
    pass


if __name__ == '__main__':
    main()