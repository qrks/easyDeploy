# encoding=utf-8
import sys
import os
import json
import re
import requests

import smtplib
# import email.mime.text as et
# import email.mime.multipart as em
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import win32com
import bs4
from PIL import ImageGrab
import PIL.ImageGrab

# import tesseract

mailto_list = ['qianxiaokai@sh.icbc.com.cn']
mail_host = "inshfhoem000/服务器/ICBC";
mail_user = "钱晓恺/科技/上海/ICBC"
mail_pass = " pass.234 "
mail_postfix= ""

def test1():
    str = '{dir1:dir2,dir3:[dir4,dir5,dir6],dir7:dir8}'
    index = 0;
    ss = list(str)
    str = str[1:len(str)-1]
    flag = 0 #0未遇到[  #1遇到了[,等待] 
    nowSumStr = ''
    retList = []
    for char in str:
        if char == ',' and flag == 0:
            print 'insert [%s]' % nowSumStr
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
        print 'nowSumStr=%s,flag=%s' % (nowSumStr,flag)
        index += 1

        if index == len(str): #最后一位了，插入
            print 'insert [%s]' % nowSumStr
            retList.append(nowSumStr)

def test2():
    # match = re.match('{[a-zA-z0-9_]+:([a-zA-z0-9_]+)|(\[[a-zA-z0-9_]+:[a-zA-z0-9_]+\])}','{dir1:dir2,dir3:[dir4,dir5,dir6],dir7:dir8,}')
    match = re.match('[a-zA-z0-9_]*:([a-zA-z0-9_]*)|(\[[a-zA-z0-9_]*,[a-zA-z0-9_]*\])','dir1:dir2,dir3:[dir4,dir5,dir6],dir7:dir8,')
    match = re.match('^[1-9][0-9]{0,17}','2')

    print match
    print '---------------------------'
    if match:
        print match.string
        print match.group()
        print match.re
        print match.pos
        print match.endpos
        print match.groups()


def test3():
    fillVarInPath('${gtcg_ctbsh_dir}/9998,${gtcg_ctbsh_dir}/9994,${gtcg_home}/UPS')


def test4():
    s = '/home/wasup/IBM/WebSphere/AppServer/profiles/AppSrv02/installedApps/TSHFHCOSPAPP01Node01Cell/G1S2_war'
    s = 'd:/tmp'
    #获取路径中的最后的 文件名or文件夹名
    print os.path.split(s)
    print os.path.abspath(s)
    print os.path.basename(s)

def test5():
    urlstr = "http://107.22.189.175/wiki/index.php?title=%E7%89%B9%E6%AE%8A:%E7%94%A8%E6%88%B7%E7%99%BB%E5%BD%95&returnto=%E9%A6%96%E9%A1%B5"
    login_params = {"wpName":"Qianxk","wpPassword":"Password","wpLoginattempt":"%E7%99%BB%E5%BD%95"}
          
    s = requests.session()
    r = s.post(url=urlstr,data=login_params)

    content = r.content
    # print content

    # headers = r.headers
    # print r.content
    # r.encoding = 'utf-8'

    # print r.content
    # print r.text
    # print r.content.decode('utf-8')

    # con = json.loads(r.content)
    print '--------------------------'
    soup = bs4.BeautifulSoup(content,'html.parser')
    print soup.a['id']
    # print soup.findAll('a')[0].get('id')
    # 

    index = 0
    for rs in soup.findAll('a',attrs={'href':True}):
        print rs,type(rs)

        print rs['href']
        index += 1


def test6():
    urlstr_login = "http://83.28.33.230:9080/icbc/apip/without_session?action=signin.flowc&flowActionName=signin"
    urlstr = "http://83.28.33.230:9080/icbc/apip/api_info.flowc"
    #http://83.28.33.230:9080/icbc/apip/imageServlet
    login_params = {"netType":"0","dse_sessionId":"","userId":"jb064070","pw":"pass.123","ssicFlag":"0","netTerminal":"107.22.191.10"}

    s = requests.session()
    r = s.get(urlstr)
    # r = s.post(url=urlstr,data=login_params)

    print r.content

    # headers = r.headers
    # print r.content
    # r.encoding = 'utf-8'

    # print r.text
    # print r.content.decode('utf-8')

    # con = json.loads(r.content)
    print '--------------------------'
    # print json.loads(headers)
    # print r.json()


def test7():
    pass


def getScreenPig():
    im = ImageGrab.grab()
    im.save('d:/test.jpg','jpeg')


def main():
    test7()
    # getScreenPig()
    print 'done'
    pass

if __name__ == '__main__':
    main()
    