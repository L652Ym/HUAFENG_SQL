# Arize Phoenix RAG 演示项目

## 📋 项目概述

本项目是一个完整的RAG (Retrieval-Augmented Generation) 演示系统,展示如何使用 **Arize Phoenix** 对RAG系统进行追踪、监控和评估。项目使用 **DeepSeek API** 作为LLM,结合 **LlamaIndex** 框架构建RAG pipeline,并通过 **Phoenix** 实现全链路的可观测性。

### 🎯 项目目标

- ✅ 搭建一个基础的RAG问答系统
- ✅ 集成Arize Phoenix进行追踪和监控
- ✅ 使用Phoenix Evals评估RAG质量
- ✅ 演示如何使用Phoenix UI分析RAG性能
- ✅ 提供完整的中文文档和示例

### 🏗️ 技术栈

- **LLM**: DeepSeek API (兼容OpenAI接口)
- **RAG框架**: LlamaIndex
- **可观测性**: Arize Phoenix
- **向量存储**: ChromaDB (内存模式)
- **编程语言**: Python 3.8+

---

## 📚 什么是Arize Phoenix?

### Phoenix 简介

**Arize Phoenix** 是一个开源的AI可观测性和评估平台,专门为LLM应用设计。它提供:

1. **追踪 (Tracing)**:
   - 自动记录LLM应用的每一步操作
   - 捕获prompt、response、token使用、延迟等信息
   - 支持分布式追踪,可视化整个调用链

2. **评估 (Evaluation)**:
   - 提供多种预置评估模板
   - 支持自定义评估指标
   - 自动评估RAG质量(相关性、幻觉检测等)

3. **可视化 (Visualization)**:
   - Web UI查看所有追踪数据
   - 时间线视图、树状视图
   - 性能分析、成本分析

4. **数据集管理**:
   - 管理测试数据集
   - 运行批量实验
   - 对比不同版本的性能

### Phoenix 的核心概念

#### 1. Spans (跨度)
- Span是追踪的基本单位,代表一个操作
- 每个span包含: 名称、开始时间、持续时间、输入/输出、元数据
- Spans可以嵌套,形成调用树

#### 2. Traces (追踪)
- Trace是一组相关的spans集合
- 代表一个完整的请求处理流程
- 例如: 一个RAG查询的trace包含 embedding → retrieval → generation 等spans

#### 3. Projects (项目)
- 用于组织和分离不同的应用或实验
- 每个project有独立的traces和evaluations

#### 4. Evaluations (评估)
- 对traces的质量评估
- 可以是自动评估(使用LLM)或人工评估
- 评估结果与traces关联,便于分析

### Phoenix 在RAG中的应用

在RAG系统中,Phoenix可以追踪:

```
用户问题
    ├─ 向量化查询 (Embedding)
    │   ├─ API调用
    │   ├─ Token使用
    │   └─ 耗时
    ├─ 向量检索 (Retrieval)
    │   ├─ 检索到的文档数量
    │   ├─ 相似度分数
    │   └─ 检索耗时
    └─ 生成回答 (Generation)
        ├─ Prompt构建
        ├─ LLM API调用
        ├─ Token使用
        ├─ 生成耗时
        └─ 最终回答
```

每一步都被记录,可以在Phoenix UI中查看和分析。

---

## 🚀 快速开始

### 1. 环境准备

#### 系统要求
- Python 3.8 或更高版本
- 2GB+ 内存
- 稳定的网络连接 (访问DeepSeek API)

#### 安装依赖

```bash
# 进入项目目录
cd phoenix_rag_demo

# 安装依赖包
pip install -r requirements_phoenix_demo.txt
```

### 2. 配置环境变量

创建 `.env` 文件:

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件,填入你的API密钥
```

必需的配置:

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx  # 从 https://platform.deepseek.com/ 获取
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-chat

# 如果有OpenAI API key,用于embedding (可选)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# Phoenix 配置 (使用默认值即可)
PHOENIX_PORT=6006
PHOENIX_PROJECT_NAME=rag-demo
```

### 3. 运行演示

#### 方式一: 完整演示 (推荐)

```bash
python demo.py
```

这将运行完整的演示流程:
1. 初始化Phoenix并启动UI
2. 构建RAG索引
3. 执行5个测试查询
4. 运行Phoenix Evals评估
5. 可选:进入交互式问答模式

#### 方式二: 简单测试

```bash
python simple_test.py
```

快速测试RAG核心功能,不启用Phoenix追踪。

#### 方式三: 自定义使用

```python
from rag_system import PhoenixRAGSystem

# 创建RAG系统
rag = PhoenixRAGSystem(
    data_dir="./sample_data",
    chunk_size=512,
    chunk_overlap=50,
    top_k=3,
    enable_phoenix=True,
)

# 构建索引
rag.build_index()

# 查询
result = rag.query("什么是机器学习?")
rag.print_result(result)
```

### 4. 查看Phoenix UI

运行演示后,访问 Phoenix UI:

```
http://localhost:6006
```

在UI中你可以:
- 查看所有查询的追踪记录
- 分析每一步的耗时
- 查看LLM的prompt和response
- 检查token使用情况
- 查看评估结果

---

## 📁 项目结构

```
phoenix_rag_demo/
├── README_PHOENIX_RAG.md          # 本文档
├── requirements_phoenix_demo.txt  # Python依赖
├── .env.example                   # 环境变量示例
├── .env                          # 环境变量配置 (需自己创建)
│
├── rag_system.py                 # RAG系统核心实现
├── evaluate.py                   # Phoenix评估功能
├── demo.py                       # 完整演示脚本
├── simple_test.py                # 简单测试脚本
│
└── sample_data/                  # 示例文档
    ├── ai_basics.txt             # AI基础知识
    ├── machine_learning.txt      # 机器学习
    └── deep_learning.txt         # 深度学习
```

---

## 🔧 核心模块详解

### 1. rag_system.py - RAG系统

这是RAG系统的核心实现,包含以下功能:

#### PhoenixRAGSystem 类

```python
class PhoenixRAGSystem:
    """基于Phoenix的RAG系统"""

    def __init__(self, data_dir, chunk_size, chunk_overlap, top_k, enable_phoenix):
        """初始化RAG系统"""

    def _setup_phoenix(self):
        """配置Phoenix追踪"""
        # 1. 启动Phoenix应用: px.launch_app()
        # 2. 配置OpenTelemetry追踪
        # 3. 自动instrument LlamaIndex

    def _setup_llm(self):
        """配置LLM和Embedding模型"""
        # 1. 配置DeepSeek API作为LLM
        # 2. 配置Embedding模型
        # 3. 设置全局Settings

    def load_documents(self, file_paths=None):
        """加载文档"""
        # 使用SimpleDirectoryReader加载文档

    def build_index(self, documents=None):
        """构建向量索引"""
        # 1. 文档分块
        # 2. 向量化
        # 3. 构建索引
        # 4. 创建查询引擎

    def query(self, question):
        """执行RAG查询"""
        # 1. 向量检索
        # 2. LLM生成回答
        # 3. 返回结果 (自动被Phoenix追踪)
```

#### 关键技术点

**1. Phoenix集成**

```python
# 启动Phoenix应用
self.phoenix_session = px.launch_app()

# 配置OpenTelemetry
tracer_provider = trace_sdk.TracerProvider()
tracer_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint))
)

# 自动instrument LlamaIndex
LlamaIndexInstrumentor().instrument()
```

这样所有LlamaIndex的操作都会自动被追踪!

**2. DeepSeek API配置**

```python
# DeepSeek API兼容OpenAI接口
self.llm = OpenAI(
    model="deepseek-chat",
    api_key=api_key,
    api_base="https://api.deepseek.com",  # 自定义base_url
    temperature=0.1,
)
```

**3. RAG Pipeline**

```python
# 构建索引
index = VectorStoreIndex.from_documents(documents)

# 创建检索器
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=3,
)

# 创建查询引擎
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    llm=self.llm,
)

# 查询 (自动追踪)
response = query_engine.query(question)
```

### 2. evaluate.py - 评估模块

使用Phoenix Evals评估RAG质量:

#### RAGEvaluator 类

```python
class RAGEvaluator:
    """RAG系统评估器"""

    def __init__(self, model_name="gpt-4o-mini"):
        """初始化评估模型"""

    def evaluate_relevance(self, questions, contexts):
        """评估检索相关性"""
        # 使用RAG_RELEVANCY_PROMPT_TEMPLATE
        # 评估检索的文档是否与问题相关

    def evaluate_hallucination(self, answers, contexts):
        """评估幻觉检测"""
        # 使用HALLUCINATION_PROMPT_TEMPLATE
        # 评估回答是否基于检索的上下文

    def evaluate_qa_dataset(self, qa_pairs, save_path):
        """评估完整的QA数据集"""
        # 批量评估并保存结果
```

#### 评估指标

**1. 检索相关性 (Retrieval Relevancy)**
- 评估检索的文档是否与用户问题相关
- 标签: `relevant` / `irrelevant`
- 帮助发现检索质量问题

**2. 幻觉检测 (Hallucination Detection)**
- 评估回答是否基于检索的上下文
- 标签: `factual` / `hallucinated`
- 检测模型是否编造信息

#### 使用示例

```python
from evaluate import evaluate_from_query_results

# 评估RAG查询结果
eval_results = evaluate_from_query_results(
    query_results,  # 从rag.query()得到的结果
    save_path="evaluation_results.json"
)

# 查看统计
# 会自动输出:
# - 相关性比例
# - 幻觉检测比例
# - 详细的评估说明
```

### 3. demo.py - 演示脚本

完整的演示流程:

```python
def main():
    # 1. 运行基础演示
    rag, query_results = run_basic_demo()

    # 2. 运行评估演示
    eval_results = run_evaluation_demo(query_results)

    # 3. 交互式问答 (可选)
    run_interactive_demo(rag)
```

---

## 🎓 Phoenix 使用指南

### Phoenix UI 功能介绍

访问 `http://localhost:6006` 后,你会看到以下功能:

#### 1. Traces 页面

- **列表视图**: 显示所有查询的追踪记录
- **时间线**: 可视化每个操作的耗时
- **过滤**: 按项目、时间、状态过滤
- **搜索**: 搜索特定的traces

#### 2. Trace 详情页

点击任意trace,查看详细信息:

- **Spans树**: 树状结构显示所有操作
- **时间线**: 水平时间线显示并发和顺序关系
- **Span详情**:
  - 输入/输出
  - 元数据 (model, temperature, tokens等)
  - 错误信息 (如果有)
  - 自定义属性

#### 3. 性能分析

- **延迟分布**: P50, P95, P99延迟
- **Token使用**: 统计token消耗
- **成本分析**: 估算API成本
- **瓶颈识别**: 找出最慢的操作

#### 4. Evaluations 页面

查看评估结果:

- **评估列表**: 所有评估任务
- **评估结果**: 每个trace的评估分数
- **统计图表**: 可视化评估指标分布

### Phoenix 最佳实践

#### 1. 合理命名项目

```python
# 为不同实验使用不同的项目名
PHOENIX_PROJECT_NAME=rag-demo-v1
PHOENIX_PROJECT_NAME=rag-demo-v2-improved
```

#### 2. 添加自定义属性

```python
# 在span中添加自定义属性
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("user_id", "12345")
    span.set_attribute("query_type", "factual")
    # ... 你的代码
```

#### 3. 定期导出数据

Phoenix支持导出traces数据用于离线分析:

```python
import phoenix as px

# 导出数据
px.Client().export_traces("traces_export.parquet")
```

#### 4. 使用Phoenix Cloud (可选)

本地Phoenix适合开发,生产环境可以使用Phoenix Cloud:

```bash
# 在.env中配置
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com
PHOENIX_CLIENT_HEADERS=api_key=your_api_key
```

---

## 🔍 常见问题 (FAQ)

### 1. Phoenix UI无法访问?

**可能原因**:
- Phoenix未启动成功
- 端口被占用

**解决方案**:
```bash
# 检查端口
netstat -an | grep 6006

# 更换端口
export PHOENIX_PORT=6007
```

### 2. DeepSeek API调用失败?

**检查清单**:
- [ ] API key是否正确?
- [ ] 网络是否连接?
- [ ] API额度是否充足?

**测试API**:
```python
from openai import OpenAI

client = OpenAI(
    api_key="your_key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### 3. Embedding模型问题?

**注意**: DeepSeek目前没有专用的embedding API。

**解决方案**:

**选项1**: 使用OpenAI的embedding模型 (推荐)
```bash
# 在.env中设置
OPENAI_API_KEY=sk-xxxxx
EMBEDDING_MODEL=text-embedding-3-small
```

**选项2**: 使用开源embedding模型
```bash
pip install sentence-transformers

# 修改代码使用本地模型
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-zh-v1.5"  # 中文模型
)
```

### 4. 评估功能报错?

**常见问题**: Phoenix Evals需要OpenAI兼容的API

**解决方案**:
- 使用OpenAI API key
- 或配置DeepSeek API为评估模型 (需要兼容性测试)

```python
# 在evaluate.py中修改
eval_model = OpenAIModel(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
)
```

### 5. 内存不足?

**RAG系统需要内存**:
- 文档向量化
- 向量索引存储
- LLM上下文

**解决方案**:

```python
# 减小chunk_size
rag = PhoenixRAGSystem(chunk_size=256)  # 默认512

# 减少top_k
rag = PhoenixRAGSystem(top_k=2)  # 默认3

# 减少文档数量
# 只加载部分文档
```

### 6. 追踪数据太多?

**Phoenix会存储所有traces,长时间运行会占用空间**

**解决方案**:

```bash
# 定期清理数据
# Phoenix数据存储在临时目录,重启会清空

# 或使用采样
# 只追踪部分请求 (需要修改代码)
```

---

## 📊 性能优化建议

### 1. 文档分块优化

```python
# 根据文档类型调整chunk_size
# 技术文档: 较大chunk (512-1024)
# 对话数据: 较小chunk (128-256)

chunk_size = 512
chunk_overlap = 50  # 10%左右的重叠
```

### 2. 检索优化

```python
# 调整top_k
# 太小: 可能遗漏相关信息
# 太大: 增加噪声和成本

top_k = 3  # 一般3-5个即可
```

### 3. LLM参数调优

```python
# Temperature: 控制随机性
# 0.0: 完全确定性
# 0.1-0.3: 较少随机性 (推荐RAG)
# 0.7-1.0: 较多创造性

temperature = 0.1  # RAG场景推荐低temperature
```

### 4. 缓存策略

```python
# LlamaIndex支持缓存
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core import load_index_from_storage

# 保存索引
index.storage_context.persist(persist_dir="./storage")

# 加载索引 (避免重复构建)
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

---

## 🌟 扩展建议

### 1. 添加更多数据源

```python
# 支持PDF
pip install pypdf

# 支持Word
pip install python-docx

# 支持网页
pip install beautifulsoup4
```

### 2. 使用更好的向量数据库

```python
# Qdrant (推荐)
pip install qdrant-client

# Milvus
pip install pymilvus

# Pinecone
pip install pinecone-client
```

### 3. 实现混合检索

```python
# BM25 + 向量检索
from llama_index.core.retrievers import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever

# 组合多个检索器
retriever = QueryFusionRetriever([
    vector_retriever,
    bm25_retriever,
])
```

### 4. 添加重排序

```python
# 使用reranker提高检索质量
pip install sentence-transformers

from llama_index.postprocessor import SentenceTransformerRerank

reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-large",
    top_n=3,
)
```

### 5. 多语言支持

```python
# 使用多语言embedding模型
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

---

## 📖 学习资源

### Arize Phoenix 官方资源

- **官方文档**: https://docs.arize.com/phoenix
- **GitHub**: https://github.com/Arize-ai/phoenix
- **Quickstart**: https://docs.arize.com/phoenix/quickstart
- **YouTube频道**: Arize AI (有教学视频)

### LlamaIndex 学习资源

- **官方文档**: https://docs.llamaindex.ai/
- **示例**: https://github.com/run-llama/llama_index/tree/main/docs/examples
- **Discord社区**: LlamaIndex Discord

### RAG 相关资源

- **论文**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- **博客**: LangChain Blog, LlamaIndex Blog
- **课程**: DeepLearning.AI - Building RAG Applications

---

## 🤝 贡献和反馈

### 改进建议

如果你有改进建议:

1. 优化代码性能
2. 添加新功能
3. 改进文档
4. 修复bug

欢迎提交Issue或Pull Request!

### 联系方式

- **Email**: [你的邮箱]
- **GitHub**: [你的GitHub]

---

## 📄 许可证

本项目使用 MIT 许可证,可自由使用和修改。

---

## 🎉 总结

通过本项目,你学会了:

✅ 如何使用DeepSeek API构建LLM应用
✅ 如何使用LlamaIndex构建RAG系统
✅ 如何集成Arize Phoenix进行追踪
✅ 如何使用Phoenix Evals评估RAG质量
✅ 如何使用Phoenix UI分析和优化RAG系统

**下一步**:

1. 🚀 运行演示,探索Phoenix UI
2. 📚 添加你自己的文档数据
3. 🔧 调整参数,优化性能
4. 🌟 扩展功能,构建生产级RAG系统

祝你使用愉快! 🎊
