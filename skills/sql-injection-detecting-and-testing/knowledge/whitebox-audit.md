# 白盒审计流程

作为代码白盒审计专家，必须秉持严谨客观的态度，杜绝主观臆断。任何 SQL 注入漏洞的确认，都必须经过严格的代码逻辑推导与数据流验证，确凿证明用户输入能够直接或间接控制目标参数，并最终改变 SQL 语句的原有语义。

## 1. 环境与技术栈识别 (Context & Tech Stack)
- 编程语言：通过项目文件后缀及目录结构，精准识别后端语言（如 PHP、Python、Java、Node.js、Go、C#、Ruby 等）。
- 数据库系统：审计数据库连接配置及驱动，确认底层数据库类型（如 MySQL、PostgreSQL、SQLite、MSSQL、Oracle 等），以确定特定数据库的 SQL 语法特性。
- 基建辅助分析：综合分析依赖文件（如 `pom.xml`、`package.json`、`requirements.txt`）、配置文件或 `docker-compose.yml`，快速掌握项目框架与组件版本。

## 2. 锚定 SQL 注入风险点 (Sink Location)
全局检索数据库交互的关键函数与 SQL 关键字，寻找潜在的动态拼接点：
- 通用 SQL 动词：`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `WHERE`, `ORDER BY`, `GROUP BY`
- PHP：`mysql_query`, `mysqli_query`, `PDO::query`, `->where(`
- Python：`cursor.execute`, `.raw(`, `.extra(`, `text(`
- Java：`Statement.execute`, `createQuery`, `createNativeQuery`
- Node.js：`.query(`, `.raw(`, `knex.raw(`, `sequelize.query(`, `[Op.raw]`, `$queryRawUnsafe(`, `$executeRawUnsafe(`
- Go：`db.Query(`, `db.Exec(`, 配合 `fmt.Sprintf` 的拼接查询
- C# / .NET：`SqlCommand`, `ExecuteReader`, `ExecuteScalar`, `ExecuteNonQuery`, `FromSqlRaw`, `ExecuteSqlRaw`
- Ruby on Rails：`find_by_sql`, `connection.execute`, `.where("...")` (非参数化操作), `.order(`
- 以及其他存在注入的地方
- 状态同步：将所有发现的动态 SQL 构造位置及对应的风险变量进行标记，并详细更新至 `sql-injection-state.json` 文件中。

## 3. 数据流追踪与污点分析 (Source to Sink Analysis)
对已定位的风险点进行逆向溯源或正向追踪，严谨验证变量是否真正可控：
- 识别污染源 (Source)：排查所有可能的用户输入入口，包含但不限于：
  - HTTP 基础交互：GET / POST 参数、Cookie 字段、自定义 Header
  - 路由解析：URL Path 参数
  - 请求体：JSON / XML Body 字段
  - 文件交互：文件名解析、上传的文件内容读取
- 可利用性验证：追踪污染数据在代码流转中的完整路径，确认其最终能无损或有效携带 Payload 到达 SQL 执行处 (Sink)。
- 状态同步：剔除无法被外部控制、已被安全截断或处于死代码 (Dead Code) 中的误报点，将最终确认的有效注入点更新至 `sql-injection-state.json`。

## 4. 过滤与防御机制审查 (Bypass & Sanitization Check)
- 防御机制定性：排查数据流转链路中是否经过 WAF 拦截规则、全局过滤器、拦截器 (Interceptor) 或自定义的数据清洗函数。
- 状态同步：将目标参数受到的具体清洗规则、过滤字符集及最终的绕过评估结果，按照要求结构化地更新至 `sql-injection-state.json` 文件中。
