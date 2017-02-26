#encoding=utf-8
import pandas as pd
import matplotlib.pyplot as plt
import ftpFunc as ftpf
from ftpFunc import *

# df= pd.read_csv('E:/pyworkspace/20170307-zzdzmq-gjszsb-rpt2.csv',encoding='gbk')
df= pd.read_csv(u'E:/pyworkspace/中金所-入金-2.csv',encoding='gbk')
df.dropna(how='any')
df.fillna(0)

# df2 = df.drop(1,axis=0)

print df.head()
#rename columnsName
df.rename(columns={r'SUBSTR(WORKDATE,1,6)':'date',r'COUNT(*)':'count',r'SUM(REALAMT)':'amt'},inplace=True)
df.set_index('index')

print df.head()

#print df.describe()
#print df[u'币种']
#print df.iloc[:,]
df.plot()
#set Chinese
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False

# write to csv
# df.to_csv(u'E:/pyworkspace/中金所-入金-3.csv',encoding='gbk')

# plt.show()

try:
    ftp = ftpConnect('107.6.141.134',21,'wasup','pass.123')
    # ftp = ftpConnect('107.6.61.11',21,'wasup','pass.123')
    ftp.getwelcome()
    print ftp.pwd()
    # ftp.dir() 
    # fileUpolad = open('D:/sync2.log','rb')

    # upload(ftp,'D:/ImageTest','/home/wasup/tmp')
    # downloadFile(ftp,'/home/wasup/tmp/aaa.txt','d:/aaa.txt')

    # downloadDir(ftp,'/home/wasup/tmp/','D:/tmp/')
    # downloadDir(ftp,'/home/wasup/src/sh/ups/','D:/tmp/')
    # downloadDir(ftp,'/home/wasup/IBM/WebSphere/AppServer/profiles/AppSrv02/installedApps/TSHFHCOSPAPP01Node01Cell/G1S2_war.ear/G1S2.war/WEB-INF/classes/com/icbc/cosp/yffk/','D:/tmp/')
        
finally:
    ftpQuit(ftp)