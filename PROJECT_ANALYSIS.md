# HUAFENG_SQL 项目完整分析文档

## 📋 目录

1. [项目概述](#项目概述)
2. [项目架构图](#项目架构图)
3. [目录结构](#目录结构)
4. [核心组件详解](#核心组件详解)
5. [完整执行流程](#完整执行流程)
6. [数据流向图](#数据流向图)
7. [每个文件的详细说明](#每个文件的详细说明)

---

## 项目概述

**项目名称**: Huafeng QA (华丰工业数据问答系统)

**核心功能**:
- 基于 LangChain 1.0 的多数据源智能问答系统
- 支持 SQL 数据库查询（历史数据、报警数据）
- 支持 CSV 文件查询（点位主数据）
- 智能路由：自动选择最合适的数据源
- 跨源回补：SQL 需要 CSV 信息时自动调用
- 澄清机制：候选过多时提示用户选择

**技术栈**:
- LangChain 1.0.7 (LLM 框架)
- PostgreSQL (时序数据库)
- Pandas (CSV 数据处理)
- DeepSeek Chat (默认 LLM)
- Phoenix (可观测性)

---

## 项目架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                                │
│                    scripts/service.py                            │
│              (CLI 交互 / 一次性查询 / 报告生成)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      路由编排层                                    │
│                app/router/orchestrator.py                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RoutingOrchestrator (核心控制器)                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ 1. plan_sources()    - 智能路由规划                       │  │
│  │ 2. probe_sources()   - 数据源探测                         │  │
│  │ 3. execute()         - 执行查询 (串行/并发)               │  │
│  │ 4. _summarize()      - 多源结果汇总                       │  │
│  │ 5. _rewrite()        - 查询改写                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                │                           │
                ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    SQL 数据源层           │  │    CSV 数据源层           │
│  app/sources/sql.py      │  │  app/sources/csv.py      │
├──────────────────────────┤  ├──────────────────────────┤
│ SqlDataSource            │  │ CsvDataSource            │
│ - SQL Agent              │  │ - SimpleCsvToolsAgent    │
│ - create_sql_agent()     │  │ - StructuredTool         │
│ - SQLDatabase            │  │ - Pandas DataFrame       │
└──────────────────────────┘  └──────────────────────────┘
                │                           │
                ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   PostgreSQL 数据库       │  │    CSV 文件               │
│   - alarm_event (报警)    │  │  data/point_data.csv     │
│   - 历史表 (时序数据)      │  │  (点位主数据)             │
└──────────────────────────┘  └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      支撑服务层                                    │
├─────────────────────────────────────────────────────────────────┤
│ LLM 服务            │ app/llm/factory.py (ChatOpenAI)           │
│ 提示模板            │ app/prompts/*.py (规划/汇总/CSV工具)        │
│ 回调处理            │ app/callbacks/*.py (中文输出/Token统计)     │
│ 配置管理            │ app/config/settings.py (.env加载)         │
│ 可观测性            │ app/observability/phoenix.py              │
│ 评估               │ app/monitor/evals.py                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
HUAFENG_SQL/
├── app/                          # 核心应用代码
│   ├── callbacks/                # LangChain 回调处理器
│   │   ├── console.py            # 中文终端输出格式化
│   │   └── usage.py              # Token 使用统计
│   ├── config/                   # 配置管理
│   │   └── settings.py           # 环境变量加载与配置
│   ├── llm/                      # LLM 工厂
│   │   └── factory.py            # ChatOpenAI 构建函数
│   ├── monitor/                  # 监控与评估
│   │   └── evals.py              # 质量评估逻辑
│   ├── observability/            # 可观测性
│   │   └── phoenix.py            # Phoenix/OpenTelemetry 集成
│   ├── prompts/                  # 提示模板
│   │   ├── planner.py            # 路由规划提示
│   │   ├── summarizer.py         # 证据汇总提示
│   │   └── csv_tools.py          # CSV 工具提示
│   ├── router/                   # 路由编排
│   │   └── orchestrator.py       # ★ 核心路由控制器 ★
│   └── sources/                  # 数据源抽象
│       ├── base.py               # 数据源基类
│       ├── sql.py                # SQL Agent 数据源
│       └── csv.py                # CSV 工具代理数据源
├── scripts/                      # 可执行脚本
│   ├── service.py                # ★ 主入口 ★ (交互式/一次性查询)
│   ├── router_smoke_test.py     # 路由烟雾测试
│   ├── evals_demo_generate.py   # 评估数据生成
│   ├── evals_report.py           # 评估报告生成
│   ├── sql_schema_qa.py          # SQL Schema QA 测试
│   └── test_deepseek_langchain.py # LangChain 测试
├── data/                         # 数据文件
│   └── point_data.csv            # 点位主数据 CSV
├── requirements.txt              # Python 依赖
├── constraints.txt               # 依赖版本约束
└── .env                          # 环境变量配置 (不提交)
```

---

## 核心组件详解

### 1. **入口层** - `scripts/service.py`

**职责**:
- 应用程序主入口
- 处理命令行参数
- 管理交互式会话
- 生成查询报告

**关键函数**:
```python
main()                    # 主函数
  ├─ parse_args()         # 解析命令行参数
  ├─ build_sql_source()   # 构建 SQL 数据源
  ├─ build_csv_source()   # 构建 CSV 数据源
  ├─ register_data_sources()  # 注册数据源
  ├─ router.execute()     # 执行查询
  └─ _write_per_query_report()  # 写报告
```

**执行模式**:
1. **一次性模式**: `--question "问题"`
2. **交互模式**: 终端循环输入
3. **澄清模式**: `--clarify "0,2"` 选择候选

---

### 2. **路由编排层** - `app/router/orchestrator.py`

**核心类**: `RoutingOrchestrator`

**职责**:
- 智能路由规划 (静态规则 + LLM 规划)
- 多数据源并发/串行执行
- 跨源回补 (CSV → SQL)
- 结果汇总与引用
- 澄清机制

**核心方法详解**:

```python
class RoutingOrchestrator:

    # 1. 路由规划
    def plan_sources(question, lang, callbacks):
        """
        步骤:
        1. 静态启发式规则 (_apply_static_rules)
           - 检测意图 (点位/历史/报警)
           - 预过滤数据源
        2. LLM 规划 (可选)
           - 使用 planner_llm 生成执行计划
           - 返回: {ordered_sources: [...], strategy: "..."}
        3. 缓存 (PLAN_CACHE_SECONDS)
        """

    # 2. 数据源探测
    def probe_sources(source_names):
        """
        目的: 快速检查数据源状态
        - SQL: 返回表预览 (前5个表)
        - CSV: 返回前3行样本
        - 异步并发执行
        - 缓存 (PROBE_CACHE_SECONDS)
        """

    # 3. 执行查询 (核心)
    def execute(question, lang, callbacks, clarify_choice):
        """
        主执行流程:

        1. 规划阶段
           plan_data = plan_sources()

        2. 探测阶段
           probe_info = probe_sources()

        3. 查询改写
           rewritten = _rewrite_queries_for_sources()
           - CSV: 提示返回结构化候选
           - SQL: 添加上下文 (CSV 候选、年份过滤)

        4. 并发/串行执行
           if 无 CSV→SQL 依赖:
               并发执行 (asyncio)
           else:
               串行执行

        5. 动态跨源回补
           if SQL 调用了 invalid_tool:
               执行 CSV → 提取候选 → 重写 SQL → 重试

        6. 澄清处理
           if 候选数 > CLARIFY_CANDIDATE_THRESHOLD:
               返回澄清选项
               等待用户选择

        7. 结果汇总
           final_text = _summarize_outputs()
           - 单源: 直接返回
           - 多源: LLM 汇总 + 引用
        """

    # 4. 查询改写
    def _rewrite_for_csv(question, lang, intent):
        """
        改写为 CSV 查询:
        - 提示返回结构化候选
        - 包含桥接列 (point_name, code, table_name...)
        """

    def _rewrite_for_sql(question, lang, intent, context):
        """
        改写为 SQL 查询:
        - 添加 CSV 候选上下文
        - 添加年份过滤
        - 添加严格表限制 (澄清后)
        """

    # 5. 结果汇总
    def _summarize_outputs(outputs, plan_data, lang, callbacks):
        """
        汇总策略:
        1. 单源 → 直接返回 + 引用
        2. 多源 → LLM 汇总 + 引用
        3. Fallback → 简单拼接
        """
```

**重要机制**:

**A. 静态启发式规则**:
```python
def _detect_intent(question, lang):
    """
    意图检测:
    - is_point_master: 点位/描述/单位 → CSV
    - is_history: 历史/曲线/趋势 → SQL
    - is_alarm: 报警/告警/事件 → SQL
    - has_point_id: 检测点位ID
    """
```

**B. 动态跨源回补**:
```python
# 检测 SQL 调用了 invalid_tool
if "invalid_tool" in sql_tool_calls:
    # 1. 执行 CSV 获取候选
    csv_result = csv_source.run(...)

    # 2. 提取结构化候选 (JSON)
    candidates = _extract_csv_candidates(csv_result)

    # 3. 重写 SQL 查询 (添加候选上下文)
    new_sql_query = _rewrite_for_sql(..., context={"csv_candidates_json": candidates})

    # 4. 重试 SQL
    sql_result = sql_source.run(new_sql_query)
```

**C. 澄清机制**:
```python
if len(candidates) > CLARIFY_CANDIDATE_THRESHOLD:
    # 生成澄清选项
    options = [
        {
            "index": 0,
            "label": "点位A(CODE_A) | table_1 | 描述",
            "data": {point_name: "A", code: "CODE_A", ...}
        },
        ...
    ]

    return {
        "needs_clarification": True,
        "clarification": {
            "message": "检测到多个候选，请选择...",
            "options": options
        }
    }
```

---

### 3. **数据源层**

#### A. **SQL 数据源** - `app/sources/sql.py`

**核心类**: `SqlDataSource`

**组件**:
```python
SqlDataSource:
    _agent: AgentExecutor       # LangChain SQL Agent
    _db: SQLDatabase            # SQLAlchemy 包装的数据库连接
```

**构建流程**:
```python
def build_sql_source(base_url, max_iterations):
    # 1. 创建 SQLDatabase 连接
    db = SQLDatabase.from_uri(
        DB_URI,
        ignore_tables=["point_data"],  # 忽略 CSV 维护的表
        sample_rows_in_table_info=0,   # 不采样
        engine_args={
            "pool_pre_ping": True,      # 连接池预检
            "pool_recycle": 1800,        # 30分钟回收
            "pool_size": 5,
            "max_overflow": 10,
            "connect_args": {
                "connect_timeout": 5,
                "options": "-c statement_timeout=5000"  # 5秒超时
            }
        }
    )

    # 2. 缓存 table_info (减少重复自省)
    db.get_table_info = _cached_get_table_info

    # 3. SQL 查询守护 (年份过滤)
    db.run = _guarded_run  # 自动注入年份过滤

    # 4. 表访问控制 (澄清后限制)
    db.get_usable_table_names = _filtered_usable

    # 5. 创建 SQL Agent
    llm = build_llm(base_url)
    agent = create_sql_agent(
        llm,
        db=db,
        agent_type="tool-calling",  # LangChain 1.0 推荐
        verbose=False,
        max_iterations=max_iterations
    )

    return SqlDataSource(agent, db)
```

**关键优化**:

1. **表信息缓存** (避免重复自省):
```python
_ti_cache: Dict[str, tuple] = {}  # 缓存 1200 秒

def _cached_get_table_info(table_names):
    key = tuple(sorted(table_names))
    if cached and not_expired:
        return cached_value
    return _orig_get_table_info(table_names)
```

2. **年份守护** (自动注入当年过滤):
```python
def _sanitize_sql_query(sql, user_text):
    if SQL_ENFORCE_CURRENT_YEAR_IF_UNSPECIFIED:
        if not user_specified_year:
            # 注入: WHERE EXTRACT(YEAR FROM ts) = 2025 AND ...
            sql = inject_year_filter(sql, now_year)
    return sql
```

3. **表访问控制** (澄清后限制):
```python
_ALLOWED_TABLES = ContextVar("_ALLOWED_TABLES", default=[])

def _filtered_usable():
    all_tables = _orig_get_usable()
    if _ALLOWED_TABLES:
        return [t for t in all_tables if t in _ALLOWED_TABLES]
    return all_tables
```

#### B. **CSV 数据源** - `app/sources/csv.py`

**核心类**:
- `CsvDataSource` (数据源包装)
- `SimpleCsvToolsAgent` (自定义工具代理)

**CSV 工具集**:
```python
class SimpleCsvToolsAgent:
    tools = [
        csv_columns,     # 列出所有列名
        csv_head,        # 返回前 N 行
        csv_find_rows,   # 按条件过滤行
        csv_group_count  # 分组统计
    ]
```

**工具定义示例**:
```python
# 1. csv_find_rows (核心工具)
class _FindRowsInput(BaseModel):
    where: List[_FilterCond]    # 过滤条件
    select: Optional[List[str]] # 返回列
    limit: int = 20             # 最大行数

class _FilterCond(BaseModel):
    column: str                 # 列名
    op: Literal["equals", "contains", "startswith", "endswith"]
    value: str                  # 匹配值

def _csv_find_rows(where, select, limit):
    df = apply_filters(dataframe, where)
    if select:
        df = df[select]
    return {"rows": df.head(limit).to_dict("records")}

# 2. csv_group_count
def _csv_group_count(by, where, limit):
    df = apply_filters(dataframe, where)
    return df.groupby(by).size().to_dict()
```

**执行流程**:
```python
def invoke(payload, config):
    # 1. 构建提示
    messages = prompt.format_messages(q=user_query, now=datetime.now())

    # 2. LLM 工具调用
    bound_llm = llm.bind_tools(self.tools)
    resp = bound_llm.invoke(messages)

    # 3. 解析工具调用
    tool_calls = resp.tool_calls

    # 4. 执行工具
    for call in tool_calls:
        tool = find_tool_by_name(call.name)
        result = tool.invoke(call.args)

    # 5. 可选的第二次 LLM 调用 (CSV_AGENT_SECOND_PASS)
    if CSV_AGENT_SECOND_PASS:
        follow_messages = messages + [AIMessage(...), ToolMessage(result)]
        final = llm.invoke(follow_messages)
        return {"output": final.content, "data": result}
    else:
        return {"output": summary, "data": result}
```

---

### 4. **LLM 工厂** - `app/llm/factory.py`

**职责**: 创建配置好的 ChatOpenAI 实例

```python
def build_llm(base_url):
    return ChatOpenAI(
        model=MODEL,                    # deepseek-chat
        api_key=API_KEY,
        base_url=base_url,
        temperature=0.0,                # 确定性输出
        timeout=LLM_REQUEST_TIMEOUT,    # 25秒
        max_tokens=LLM_MAX_TOKENS,      # 512
        model_kwargs={
            "enable_auto_tool_choice": True,  # 自动工具选择
            "tool_call_parser": ...           # 自定义解析器
        },
        default_headers=custom_headers,  # 自定义请求头
        stream_usage=True,              # ✨ LangChain 1.0 最佳实践
    )
```

---

### 5. **回调处理器** - `app/callbacks/`

#### A. **中文终端输出** - `console.py`

```python
class ChineseConsoleCallback(BaseCallbackHandler):
    def on_tool_start(tool, input_str, **kwargs):
        """格式化工具调用输出"""
        if tool.name == "sql_db_query":
            print(f"【调用工具】sql_db_query")
            print(f"【SQL目标】表：{extract_table(input)}；时间窗：{extract_time(input)}")

    def on_tool_end(output, **kwargs):
        """格式化工具返回"""
        print(f"【工具返回】{output[:400]}")

    def on_routing_plan(plan_data, **kwargs):
        """路由计划"""
        print(f"【路由计划】顺序：{' -> '.join(plan_data['ordered_sources'])}")
        print(f"【路由计划】策略：{plan_data['strategy']}")

    def on_routing_step(source_name, output_text, **kwargs):
        """路由步骤"""
        print(f"【路由结果】{source_name} => {output_text[:400]}")
```

#### B. **Token 统计** - `usage.py`

```python
class TokenUsageHandler(BaseCallbackHandler):
    def on_llm_start(serialized, prompts, **kwargs):
        """记录开始时间"""
        self.llm_calls += 1
        self._llm_timer_stack.append(time.perf_counter())

    def on_llm_end(response, **kwargs):
        """统计 Token 使用"""
        # ✨ LangChain 1.0 最佳实践: 优先使用 usage_metadata

        # 方法 1: usage_metadata (推荐)
        for gen in response.generations:
            msg = gen.message
            if msg.usage_metadata:
                self.prompt_tokens += msg.usage_metadata["input_tokens"]
                self.completion_tokens += msg.usage_metadata["output_tokens"]
                return

        # 方法 2: llm_output (fallback)
        usage = response.llm_output.get("token_usage")
        if usage:
            self.prompt_tokens += usage["prompt_tokens"]
            ...

        # 方法 3: tiktoken 近似 (最终 fallback)
        ...
```

---

### 6. **提示模板** - `app/prompts/`

#### A. **路由规划提示** - `planner.py`

```python
def build_routing_planner_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """
        你是路由规划器，请为工业问答选择最合适的数据源并给出执行顺序。
        仅用提供的来源名称，且至少包含一个来源。
        以严格 JSON 返回：ordered_sources（按执行顺序的来源名称列表）和 strategy（简要策略）。
        如问题涉及时间但未指定年份，规划时默认按今年处理。
        """),
        ("human", """
        语言：{lang}
        当前时间：{now}
        问题：{question}
        可用数据源：
        {available}
        返回 JSON：{{"ordered_sources": ["name"...], "strategy": "..."}}
        示例：{example_json}
        """)
    ])
```

#### B. **证据汇总提示** - `summarizer.py`

```python
def build_evidence_summarizer_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """
        你是汇总器，请将多个来源的信息合并为简洁一致的答案。
        结尾追加来源引用（使用来源名称）。用简体中文回答。
        """),
        ("human", """
        语言：{lang}
        当前时间：{now}
        路由策略：{strategy}
        执行顺序：{ordered}
        收集的证据：
        {evidence}
        先输出合并后的答案，再输出引用列表。
        """)
    ])
```

#### C. **CSV 工具提示** - `csv_tools.py`

```python
def build_csv_tools_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """
        你是内存 DataFrame 'csv_lookup' 的工具调用助手。
        当前时间：{now}。
        使用提供的工具检索结构化候选（桥接列如 point_id/tag/name/desc）。
        如问题涉及时间但未指定年份，默认按今年处理。
        禁止访问本地文件或执行任意代码。请用简体中文简洁回答。
        """),
        ("human", "{q}")
    ])
```

---

### 7. **配置管理** - `app/config/settings.py`

**职责**:
- 从 `.env` 文件加载环境变量
- 提供默认值
- 支持新旧配置键名兼容

**关键配置**:
```python
# LLM 配置
BASE_URL = "https://api.deepseek.com"
API_KEY = os.getenv("LLM_API_KEY")
MODEL = "deepseek-chat"
LLM_REQUEST_TIMEOUT = 25
LLM_MAX_TOKENS = 512

# 数据库配置
PG_HOST = "127.0.0.1"
PG_PORT = "5433"
PG_DB = "app_db"
DB_URI = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# CSV 配置
OPCAE_CSV_PATH = "data/point_data.csv"

# 路由优化
USE_LLM_PLANNER = True
USE_LLM_SUMMARIZER = True
ROUTER_PARALLEL_EXECUTE = True
PROBE_CACHE_SECONDS = 120
PLAN_CACHE_SECONDS = 300
RESULT_CACHE_SECONDS = 600

# Agent 配置
SQL_AGENT_MAX_ITERATIONS = 12
CSV_AGENT_SECOND_PASS = True

# 澄清配置
CLARIFY_ENABLED = True
CLARIFY_CANDIDATE_THRESHOLD = 4
CLARIFY_MAX_OPTIONS = 8

# 年份守护
SQL_ENFORCE_CURRENT_YEAR_IF_UNSPECIFIED = True
SQL_YEAR_COLUMN_NAME = "ts"

# Phoenix 可观测性
PHOENIX_ENABLED = False
PHOENIX_ENDPOINT = "http://127.0.0.1:6006/v1/traces"
```

---

## 完整执行流程

### 场景 1: 简单查询 (单数据源)

**用户**: "查询 L3210C 点位的单位"

```
1. service.py main()
   ↓
2. router.execute(question="查询 L3210C 点位的单位", lang="zh")
   ↓
3. RoutingOrchestrator
   ├─ plan_sources()
   │  ├─ _detect_intent() → is_point_master=True
   │  ├─ _apply_static_rules() → ["csv_lookup"]
   │  └─ 返回: {ordered_sources: ["csv_lookup"], strategy: "point master → CSV"}
   │
   ├─ probe_sources(["csv_lookup"])
   │  └─ csv_source.probe() → "sample rows: ..."
   │
   ├─ _rewrite_queries_for_sources()
   │  └─ CSV: "请使用点位主数据 CSV 检索 L3210C..."
   │
   ├─ execute sources
   │  └─ csv_source.run(rewritten_query)
   │     ├─ SimpleCsvToolsAgent.invoke()
   │     ├─ LLM: 调用 csv_find_rows(where=[{column:"code", op:"contains", value:"L3210C"}])
   │     ├─ 执行工具: df[df['code'].str.contains("L3210C")]
   │     └─ 返回: {"rows": [{point_name: "...", unit: "kg/h", ...}]}
   │
   └─ _summarize_outputs()
      └─ 单源: 直接返回 "L3210C 的单位是 kg/h\n\nSources: csv_lookup"
```

---

### 场景 2: 跨源查询 (CSV → SQL)

**用户**: "查询粘度点位最近3天的历史趋势"

```
1. service.py main()
   ↓
2. router.execute(question="查询粘度点位最近3天的历史趋势")
   ↓
3. RoutingOrchestrator
   ├─ plan_sources()
   │  ├─ _detect_intent() → is_point_master=True, is_history=True
   │  ├─ LLM 规划 → {ordered_sources: ["csv_lookup", "sql_database"], strategy: "先查CSV获取点位，再查SQL历史"}
   │  └─ 返回规划
   │
   ├─ probe_sources(["csv_lookup", "sql_database"])
   │
   ├─ execute sources (串行 - 有依赖)
   │
   │  【第1步: CSV 查询】
   │  ├─ csv_source.run("查询粘度相关点位，返回 point_name, code, table_name...")
   │  │  ├─ LLM 调用 csv_find_rows(where=[{column:"desc", op:"contains", value:"粘度"}])
   │  │  └─ 返回候选: [{point_name:"VICRA2", code:"L3210C", table_name:"vicra2_history", ...}]
   │  │
   │  ├─ _extract_csv_candidates()
   │  │  └─ 提取 JSON: [{"point_name":"VICRA2","code":"L3210C","table_name":"vicra2_history"}]
   │  │
   │  【第2步: SQL 查询 (使用 CSV 上下文)】
   │  └─ sql_source.run(rewritten_sql)
   │     ├─ 重写查询: "使用 sql_database 查询，参考 CSV 候选: {...}"
   │     │             "当前年份: 2025，使用 EXTRACT(YEAR FROM ts) = 2025"
   │     │             "优先使用 point_name='VICRA2' 或 code='L3210C' 过滤"
   │     │             "目标表: vicra2_history"
   │     │
   │     ├─ SQL Agent 执行
   │     │  ├─ 工具调用: sql_db_query
   │     │  ├─ SQL: SELECT ts, value FROM "vicra2_history"
   │     │  │      WHERE point_name='VICRA2'
   │     │  │      AND EXTRACT(YEAR FROM ts)=2025
   │     │  │      AND ts >= NOW() - INTERVAL '3 days'
   │     │  │      ORDER BY ts DESC LIMIT 100
   │     │  └─ 返回: [(ts1, val1), (ts2, val2), ...]
   │
   └─ _summarize_outputs(outputs=[csv_result, sql_result])
      ├─ 多源汇总 (LLM)
      ├─ 提示: "语言: zh, 策略: 先查CSV获取点位再查SQL历史"
      │        "证据:"
      │        "Source[csv_lookup]: 找到粘度点位 VICRA2(L3210C)，表名 vicra2_history"
      │        "Source[sql_database]: 最近3天数据: ..."
      │
      └─ 返回: "粘度点位 VICRA2(L3210C) 最近3天的历史趋势:\n
                2025-11-17 10:00:00 | 45.2 kg/h\n
                2025-11-17 11:00:00 | 46.1 kg/h\n
                ...\n\n
                Sources: csv_lookup, sql_database"
```

---

### 场景 3: 动态跨源回补

**用户**: "查询报警次数最多的点位"

```
1. router.execute(question)
   ↓
2. plan_sources()
   ├─ 规划: {ordered_sources: ["sql_database"]}
   └─ 策略: "报警数据 → SQL 主导"
   ↓
3. execute sources
   ├─ sql_source.run("查询报警次数最多的点位")
   │  ├─ SQL Agent 尝试查询
   │  ├─ 发现需要点位信息 (表名映射)
   │  └─ 调用 invalid_tool(requested_tool_name="point_data_lookup")
   │
   ├─ 检测到 invalid_tool 调用
   │  ├─ 判断: 需要 CSV 回补
   │  └─ csv_backfill_done = False
   │
   ├─ 【动态回补: 执行 CSV】
   │  ├─ csv_source.run("查询所有点位的 point_name, table_name 映射")
   │  ├─ 返回候选
   │  └─ 提取 JSON candidates
   │
   └─ 【重试 SQL (带上下文)】
      ├─ 重写查询: "使用 sql_database, CSV 候选: {...}"
      ├─ SQL Agent 重新执行
      │  ├─ SELECT point_name, COUNT(*) as alarm_count
      │  │  FROM alarm_event
      │  │  WHERE EXTRACT(YEAR FROM ts) = 2025
      │  │  GROUP BY point_name
      │  │  ORDER BY alarm_count DESC
      │  │  LIMIT 10
      │  └─ 返回结果
      │
      └─ 成功返回
```

---

### 场景 4: 澄清机制

**用户**: "查询粘度的历史数据"

```
1. router.execute(question)
   ↓
2. plan_sources() → ["csv_lookup", "sql_database"]
   ↓
3. csv_source.run("查询粘度相关点位")
   ├─ 返回: {
   │    "rows": [
   │      {point_name: "VICRA1", code: "L3210A", table_name: "vicra1_history"},
   │      {point_name: "VICRA2", code: "L3210C", table_name: "vicra2_history"},
   │      {point_name: "VISC1", code: "L3211A", table_name: "visc1_history"},
   │      {point_name: "VISC2", code: "L3211B", table_name: "visc2_history"},
   │      {point_name: "VIS_CALC", code: "L3212", table_name: "vis_calc_history"}
   │    ]
   │  }
   │
   ├─ 候选数 = 5 > CLARIFY_CANDIDATE_THRESHOLD (4)
   │
   └─ 【触发澄清机制】
      ├─ _build_clarification_payload()
      │  └─ 生成选项:
      │     [
      │       {index: 0, label: "VICRA1(L3210A) | vicra1_history"},
      │       {index: 1, label: "VICRA2(L3210C) | vicra2_history"},
      │       {index: 2, label: "VISC1(L3211A) | visc1_history"},
      │       {index: 3, label: "VISC2(L3211B) | visc2_history"},
      │       {index: 4, label: "VIS_CALC(L3212) | vis_calc_history"}
      │     ]
      │
      └─ 返回: {
           "needs_clarification": True,
           "clarification": {
             "message": "检测到多个可能的点位。为避免盲目枚举查询，请先从下列候选中选择...",
             "options": [...]
           }
         }

【用户选择】
4. 用户输入: "1,2" (选择 VICRA2 和 VISC1)
   ↓
5. router.execute(question, clarify_choice={"indices": [1, 2]})
   ├─ 提取选中候选:
   │  selected = [
   │    {point_name: "VICRA2", code: "L3210C", table_name: "vicra2_history"},
   │    {point_name: "VISC1", code: "L3211A", table_name: "visc1_history"}
   │  ]
   │
   ├─ 设置严格表限制:
   │  set_allowed_tables(["vicra2_history", "visc1_history"])
   │
   ├─ 重写 SQL 查询:
   │  "仅限查询以下目标表: \"vicra2_history\", \"visc1_history\""
   │  "过滤: point_name IN ('VICRA2', 'VISC1')"
   │
   └─ sql_source.run(rewritten_query)
      ├─ SQL Agent 执行
      ├─ 表过滤生效: 只能访问选中的表
      └─ 返回结果
```

---

## 数据流向图

```
┌─────────────┐
│  用户输入    │
│  "问题文本"  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. 路由规划 (plan_sources)                      │
│  ┌────────────────────────────────────────────┐ │
│  │ 静态规则:                                   │ │
│  │ - 检测意图 (点位/历史/报警)                  │ │
│  │ - 初步过滤数据源                            │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │ LLM 规划 (可选):                            │ │
│  │ Input: 问题 + 可用数据源                    │ │
│  │ Output: {ordered_sources, strategy}         │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  2. 数据源探测 (probe_sources)                   │
│  ┌───────────────┐  ┌───────────────┐          │
│  │ CSV: 前3行     │  │ SQL: 前5表    │          │
│  └───────────────┘  └───────────────┘          │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  3. 查询改写 (_rewrite_queries_for_sources)      │
│  ┌────────────────────────────────────────────┐ │
│  │ CSV 重写:                                   │ │
│  │ "请使用 CSV 检索，返回结构化候选..."         │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │ SQL 重写:                                   │ │
│  │ "使用 SQL，参考 CSV 候选: {...}"            │ │
│  │ "年份过滤: EXTRACT(YEAR FROM ts) = 2025"    │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  4. 执行数据源                                   │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │  并发执行         │  │  串行执行         │    │
│  │  (无依赖)         │  │  (CSV→SQL依赖)   │    │
│  │  ┌──────────┐    │  │  ┌──────────┐    │    │
│  │  │ CSV      │    │  │  │ CSV      │    │    │
│  │  └──────────┘    │  │  └────┬─────┘    │    │
│  │  ┌──────────┐    │  │       │          │    │
│  │  │ SQL      │    │  │       ▼          │    │
│  │  └──────────┘    │  │  ┌──────────┐    │    │
│  │  asyncio.gather  │  │  │ SQL      │    │    │
│  └──────────────────┘  │  └──────────┘    │    │
│                        │  (使用CSV上下文)   │    │
│                        └──────────────────┘    │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  5. 动态回补 (可选)                              │
│  ┌────────────────────────────────────────────┐ │
│  │ if SQL 调用 invalid_tool:                   │ │
│  │   1. 执行 CSV 获取候选                       │ │
│  │   2. 提取 JSON candidates                   │ │
│  │   3. 重写 SQL 查询 (添加上下文)              │ │
│  │   4. 重试 SQL                               │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  6. 澄清处理 (可选)                              │
│  ┌────────────────────────────────────────────┐ │
│  │ if 候选数 > CLARIFY_CANDIDATE_THRESHOLD:    │ │
│  │   1. 生成澄清选项                           │ │
│  │   2. 返回给用户                             │ │
│  │   3. 等待用户选择                           │ │
│  │   4. 设置表访问限制                         │ │
│  │   5. 重新执行 SQL                           │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  7. 结果汇总 (_summarize_outputs)                │
│  ┌────────────────────────────────────────────┐ │
│  │ 单源: 直接返回 + 引用                        │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │ 多源: LLM 汇总 + 引用                        │ │
│  │ Input: 策略 + 执行顺序 + 各源证据            │ │
│  │ Output: 合并答案 + Sources引用              │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  最终答案    │
│  + 引用      │
└─────────────┘
```

---

## 每个文件的详细说明

### 📁 app/callbacks/

#### `console.py` - 中文终端输出格式化

**类**: `ChineseConsoleCallback(BaseCallbackHandler)`

**职责**:
- 将 LangChain 的英文输出格式化为中文
- 美化工具调用、结果输出
- 支持自定义回调 (路由计划、探测、步骤)

**关键方法**:
```python
on_chain_start()      # 链开始
on_agent_action()     # Agent 动作
on_tool_start()       # 工具开始 (美化 SQL 查询)
on_tool_end()         # 工具结束
on_chain_end()        # 链结束
on_routing_plan()     # 自定义: 路由计划
on_routing_probe()    # 自定义: 数据源探测
on_routing_step()     # 自定义: 单步结果
on_selected_candidates()  # 自定义: 用户选择
```

**输出示例**:
```
【调用工具】sql_db_query 入参：SELECT ...
【SQL目标】表：vicra2_history；时间窗：2025-11-15 ~ 2025-11-17
【工具返回】[(2025-11-17 10:00:00, 45.2), ...]
【路由计划】顺序：csv_lookup -> sql_database
【路由计划】策略：先查CSV获取点位，再查SQL历史
【路由结果】csv_lookup => 找到粘度点位 VICRA2
【路由结果】sql_database => 查询到100条历史记录
```

---

#### `usage.py` - Token 使用统计

**类**: `TokenUsageHandler(BaseCallbackHandler)`

**职责**:
- 统计每次查询的 Token 使用
- 统计 LLM 调用次数和耗时
- 支持三层 fallback 获取 Token

**属性**:
```python
prompt_tokens: int          # 输入 Token 数
completion_tokens: int      # 输出 Token 数
total_tokens: int           # 总 Token 数
llm_calls: int              # LLM 调用次数
llm_runtime_sec: float      # LLM 总耗时
```

**Token 获取策略** (LangChain 1.0 最佳实践):
```python
# 方法 1: usage_metadata (推荐)
msg.usage_metadata["input_tokens"]
msg.usage_metadata["output_tokens"]

# 方法 2: llm_output (fallback)
response.llm_output["token_usage"]

# 方法 3: tiktoken 近似 (最终 fallback)
tiktoken.encode(text)
```

---

### 📁 app/config/

#### `settings.py` - 配置管理

**职责**:
- 加载 `.env` 文件
- 提供配置默认值
- 支持新旧配置键名兼容

**配置分类**:

1. **LLM 配置**:
   - `BASE_URL`: API 端点
   - `API_KEY`: API 密钥
   - `MODEL`: 模型名称
   - `LLM_REQUEST_TIMEOUT`: 请求超时
   - `LLM_MAX_TOKENS`: 最大 Token 数

2. **数据库配置**:
   - `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASSWORD`
   - `DB_URI`: 完整连接字符串

3. **路由优化**:
   - `USE_LLM_PLANNER`: 启用 LLM 规划
   - `ROUTER_PARALLEL_EXECUTE`: 并发执行
   - `PROBE_CACHE_SECONDS`: 探测缓存时长
   - `PLAN_CACHE_SECONDS`: 规划缓存时长
   - `RESULT_CACHE_SECONDS`: 结果缓存时长

4. **Agent 配置**:
   - `SQL_AGENT_MAX_ITERATIONS`: SQL Agent 最大迭代
   - `CSV_AGENT_SECOND_PASS`: CSV 二次 LLM 调用

5. **澄清配置**:
   - `CLARIFY_ENABLED`: 启用澄清
   - `CLARIFY_CANDIDATE_THRESHOLD`: 候选阈值
   - `CLARIFY_MAX_OPTIONS`: 最大选项数

6. **年份守护**:
   - `SQL_ENFORCE_CURRENT_YEAR_IF_UNSPECIFIED`: 强制当年过滤
   - `SQL_YEAR_COLUMN_NAME`: 时间列名

---

### 📁 app/llm/

#### `factory.py` - LLM 工厂

**函数**: `build_llm(base_url) -> ChatOpenAI`

**职责**:
- 创建配置好的 ChatOpenAI 实例
- 支持自定义请求头
- 支持模型特定参数

**配置**:
```python
ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url=base_url,
    temperature=0.0,         # 确定性输出
    timeout=25,              # 请求超时
    max_tokens=512,          # 最大输出
    model_kwargs={
        "enable_auto_tool_choice": True,  # 自动工具选择
    },
    default_headers={...},   # 自定义请求头
    stream_usage=True,       # ✨ LangChain 1.0 最佳实践
)
```

---

### 📁 app/monitor/

#### `evals.py` - 质量评估

**职责**:
- 评估回答质量
- 生成评估报告
- 支持批量评估

**评估维度**:
- Relevance (相关性): 1-5
- Completeness (完整性): 1-5
- Clarity (清晰度): 1-5
- Rationale (理由): 文本

---

### 📁 app/observability/

#### `phoenix.py` - Phoenix 集成

**职责**:
- 集成 Phoenix 可观测性平台
- 记录 LangChain 调用链路
- 上报评估结果

**函数**:
```python
init(endpoint):
    """初始化 Phoenix Tracer"""
    # 设置 TracerProvider
    # 添加 BatchSpanProcessor
    # 启用 LangChainInstrumentor

evaluate(base_url, question, final_text, lang):
    """使用 LLM 评估回答质量"""
    # 返回: {relevance, completeness, clarity, rationale}

record_eval(evals, rep):
    """记录评估结果到 Phoenix"""
    # 创建 span
    # 添加评估属性
```

---

### 📁 app/prompts/

#### `planner.py` - 路由规划提示

**职责**: 生成路由规划的提示模板

**输入**:
- `lang`: 语言
- `question`: 问题
- `available`: 可用数据源列表
- `example_json`: JSON 示例
- `now`: 当前时间

**输出**: JSON 格式的规划
```json
{
  "ordered_sources": ["csv_lookup", "sql_database"],
  "strategy": "先查CSV获取点位信息，再查SQL历史数据"
}
```

---

#### `summarizer.py` - 证据汇总提示

**职责**: 生成多源结果汇总的提示模板

**输入**:
- `lang`: 语言
- `strategy`: 路由策略
- `ordered`: 执行顺序
- `evidence`: 各源证据
- `now`: 当前时间

**输出**: 合并的答案 + 引用

---

#### `csv_tools.py` - CSV 工具提示

**职责**: 生成 CSV 工具代理的提示模板

**输入**:
- `q`: 用户问题
- `now`: 当前时间

**输出**: CSV 工具调用结果

---

### 📁 app/router/

#### `orchestrator.py` - 核心路由控制器

**核心类**: `RoutingOrchestrator`

**(详见上文"核心组件详解 - 路由编排层")**

---

### 📁 app/sources/

#### `base.py` - 数据源基类

**类**: `DataSource` (抽象基类)

**接口**:
```python
class DataSource:
    name: str               # 数据源名称
    description: str        # 数据源描述

    def run(query, callbacks):
        """执行查询"""
        raise NotImplementedError

    def probe():
        """探测数据源状态"""
        return "probe not implemented"

    def short_info():
        """返回简短信息"""
        return f"{name}: {description}"
```

---

#### `sql.py` - SQL 数据源

**类**: `SqlDataSource(DataSource)`

**(详见上文"核心组件详解 - 数据源层 - SQL 数据源")**

---

#### `csv.py` - CSV 数据源

**类**:
- `CsvDataSource(DataSource)`
- `SimpleCsvToolsAgent`

**(详见上文"核心组件详解 - 数据源层 - CSV 数据源")**

---

### 📁 scripts/

#### `service.py` - 主入口

**(详见上文"核心组件详解 - 入口层")**

---

#### 其他脚本

- `router_smoke_test.py`: 路由功能烟雾测试
- `evals_demo_generate.py`: 生成评估数据集
- `evals_report.py`: 生成评估报告
- `sql_schema_qa.py`: SQL Schema 问答测试
- `test_deepseek_langchain.py`: LangChain 功能测试

---

## 总结

这是一个**生产级的工业数据问答系统**，核心特点:

1. **智能路由**: 自动选择最合适的数据源
2. **跨源协同**: SQL 和 CSV 无缝配合
3. **动态回补**: 自动处理数据源间依赖
4. **澄清机制**: 避免盲目枚举查询
5. **性能优化**: 多级缓存、并发执行
6. **可观测性**: Phoenix 集成、完整链路追踪
7. **最佳实践**: 符合 LangChain 1.0 标准

**关键技术点**:
- ✅ LangChain 1.0 Agent 框架
- ✅ 多数据源编排
- ✅ 智能查询改写
- ✅ 结构化工具调用
- ✅ 三层 Token 统计 fallback
- ✅ 年份守护与安全过滤

---

*文档生成时间: 2025-11-17*
