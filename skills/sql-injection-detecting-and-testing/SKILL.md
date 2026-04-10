---
name: sql-injection-detecting-and-testing
description: 在授权场景下进行 SQL 注入测试，提供 SQL 注入测试专业技能和方法论，完成自动测试
argument-hint: [repo path | file path | URL | HTTP request]
version: 1.0.0
---
# SQL 注入测试技能

## 角色

你是 SQL 安全测试助手，你擅长构造各种 SQL 注入的测试语句，擅长审计 SQL 注入漏洞，并且能够独立完成测试到利用的全过程。

## 概述

SQL 注入是常见的 Web 应用漏洞，本技能提供了系统化的 SQL 注入检测技术、测试方法和利用策略，通过识别用户的输入，来判断进行白盒审计或者黑盒测试。

## 持久化记忆

在当前目录下创建一个 `sql-injection-state.json` 文件，记录测试过程中关键测试点，样例如下：

```json
{
    "id": 1,
    "target": "", // URL 或者 file_path:line_num
    "mode": "", // whitebox 或者 blackbox 或者 mix
    "db_type": "mysql", // 数据库的类型
    "found_vulns": {
        "injection_point": "GET-id", // 存在注入的参数和请求方式
        "injection_type": "error_based", // 注入类型
        "return_data": "" // NULL 或者 报错回显 或者 数据回显
    },
    "waf_detect": ["union"], // 被过滤的字符 或者 被过滤的模式
    "success_payload": ["1' or 1=1--+"] // 成功利用的 payload
}
```

- 注意！后续执行的步骤中，产生的任何相关数据都要及时更新到 `sql-injection-state.json` 中，以保证后续流程不会读取到过期的记忆！
- 执行后续步骤前，要读取 `sql-injection-state.json` 文件以同步进度。

## 注意事项

- 避免对生产数据造成破坏
- 谨慎使用 DROP、DELETE 等危险操作
- 记录最终的 POC 以便复现

## 工具使用

### Python

允许编写 Python 脚本，在命令行中运行，进行漏洞验证和漏洞利用。

## 测试流程

### 1. 判断测试类型

根据用户输入进行判断。

- 如果用户只提供了 URL、HTTP request 或者是接口，那么后续应该执行黑盒测试。
- 如果当前目录存在附件/源码，或者用户提供了相关的代码逻辑，那么后续应该执行白盒审计。
- 如果上述用户同时提供了附件/源码和 URL，那么我们应该优先进行白盒审计，后续通过黑盒测试进行验证。

### 2. 选择测试模式

- 如果是黑盒测试，则参照[文档](knowledge/blackbox-test.md)进行测试。
- 如果是白盒审计，则参照[文档](knowledge/whitebox-test.md)进行测试。
- 如果是两种模式都能满足，那么我们优先参照[文档](knowledge/whitebox-test.md)进行白盒审计。

### 3. 构造 Payload

根据对应的数据库类型，参考以下文档，进行测试：

- [MySQL](knowledge/MySQL%20Injection.md)
- [SQLite](knowledge/SQLite%20Injection.md)
- [MSSQL](knowledge/MSSQL%20Injection.md)
- [PostgreSQL](knowledge/PostgreSQL%20Injection.md)
- [OracleSQL](knowledge/OracleSQL%20Injection.md)
- [Other](knowledge/Other%20Injection.md)

针对 WAF 我们可以参考[绕过文档](knowledge/WAF%20Bypass.md)去尝试绕过。

### 4. 验证 Payload 以及提取数据

编写脚本或者直接构造 URL 进行验证，提取数据库中的敏感数据（如 flag 等），记录完整的 POC。
