# encoding=utf-8
import sys
import os
import json
import pymongo

def test1():
    conn = pymongo.MongoClient('107.6.141.134',27017)
    #授权用户登陆
    loginFlag = conn.admin.authenticate('qianxk','qianxk')
    print loginFlag
    db = conn.dbt #dbt表
    print conn
    print db.collection_names() #所有的表名

    #insert
    oneRecord134 = {'hostip':'107.6.141.134','ftp':{'user':'wasup','pass':'pass.123','port':'21'},'telnet':{'user':'wasup','pass':'pass.123','port':'23'}}
    record103 = {'hostip':'107.6.61.103','ftp':[{'user':'gtcg','pass':'gtcg','port':'21'}],'telnet':{'user':'gtcg','pass':'gtcg','port':'23'}}
    oneRecord79 = {'hostip':'107.6.61.79','user':'maps','pass':'maps','telnet_port':'23','ftp_port':'21'}
    print type(record103)
    # db['Test'].insert(oneRecord79)
    #insert some
    twoRecords = [oneRecord134,oneRecord79]
    # db['Test'].insert(twoRecords)

    '''
    #find,query
    rs = db['Test'].find_one()
    print rs
    hostip = rs['hostip']
    print hostip
    #有条件查询
    rs = db['Test'].find_one({'hostip':'107.6.61.79'})
    print rs['hostip']
    '''

    #显示所有记录
    for item in db['Test'].find():
        print 'item=%s' % item

    #update  第一个dict是条件，后面一个是改变的值
    # db['Test'].update({'hostip':'107.6.61.79','user':'maps'},{"$set":{"ftp_port":'21'}})

    #删除一个collection中的数据
    # db['Test'].remove({'hostip':'107.6.61.79'})

# 
    pass



'''
插入数据
db：数据库名
collName：表名 collectionName
data:需要插入的数据dict，可以是dict数组
'''
def insData(db,collName,data):
    db[collName].insert(data)


'''
删除一条数据
db：数据库名
collName：表名 collectionName
whereDict：where条件dict
'''
def delData(db,collName,whereDict):
    db[collName].remove(whereDict)


'''
# db['Test'].update({'hostip':'107.6.61.79','user':'maps'},{"$set":{"ftp_port":'21'}})
db：数据库名
collName：表名 collectionName
whereDict：where条件dict
setDict: set的dict
'''
def updData(db,collName,whereDict,setDict):
    db[collName].update(whereDict,setDict)


def main():
    test1()
    print 'done'
    pass


if __name__ == '__main__':
    main()
    