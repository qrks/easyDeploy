# easyDeploy
一个简单好用的部署工具，让工作部署变得简单！
通过ftp，telnet来传输文件，通过sqlplus来获取数据库信息
运行环境：python2.7  ，计划下个版本，通过pyinstaller，封装成exe来作为日常使用工具

## 使用方法：
python -u deploy.py ${any_path}/deploy.ini

## ini配置文件说明：
	[action:自定义名字]
	put:从本机上传文件到服务器
	get:从服务器拿文件到本机
	move: 2个服务器间传送文件（暂未实现，后续版本实现）
	ddl: 获取数据库 数据结构的DDL语句（包括表，视图，序列，索引等。。）

	几个特殊的action：
	[varset]: 定义配置文件中的变量（暂时仅支持在 put/get/move action中使用）
    变量定义规则：${var_name}=var_value
    
    [server:XXXXXX]: 定义服务器相关信息
    hostip：服务器地址
    user：登录用户名
    pswd：登录密码
    
    [ddl:XXXXXX]: 定义数据库信息和需要获取的数据结构
    hostip=ip地址
    user=服务器用户名
    pswd=服务器用户名的密码
    db_user=数据库实例用户名
    db_pswd=数据库实例密码
    db_service_name=数据库serviceName
    [sys]: todo:在这里定义的action才会执行

### tips:
    目录路径以'/'or'\'结尾
