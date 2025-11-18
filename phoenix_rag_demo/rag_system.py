"""
Arize Phoenix RAG 演示系统
使用 DeepSeek API + LlamaIndex + Arize Phoenix 构建的基础RAG问答系统
包含完整的追踪和可观测性功能
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# LlamaIndex 核心组件
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
    Document,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

# LLM 和 Embedding 模型
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Phoenix 集成
import phoenix as px
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# 加载环境变量
load_dotenv()


class PhoenixRAGSystem:
    """
    基于Phoenix的RAG系统

    功能:
    1. 文档索引和向量化存储
    2. 语义检索
    3. LLM生成回答
    4. Phoenix追踪所有操作
    """

    def __init__(
        self,
        data_dir: str = "./sample_data",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        top_k: int = 3,
        enable_phoenix: bool = True,
    ):
        """
        初始化RAG系统

        Args:
            data_dir: 文档目录路径
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
            top_k: 检索返回的文档数量
            enable_phoenix: 是否启用Phoenix追踪
        """
        self.data_dir = Path(data_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.enable_phoenix = enable_phoenix

        # Phoenix 会话
        self.phoenix_session = None

        # RAG 组件
        self.index = None
        self.query_engine = None

        # 初始化系统
        self._setup_phoenix()
        self._setup_llm()

    def _setup_phoenix(self):
        """配置Phoenix追踪"""
        if not self.enable_phoenix:
            print("⚠️  Phoenix追踪已禁用")
            return

        try:
            # 启动Phoenix应用
            self.phoenix_session = px.launch_app()
            print(f"🚀 Phoenix UI 已启动: {self.phoenix_session.url}")

            # 配置OpenTelemetry追踪
            endpoint = f"http://127.0.0.1:{os.getenv('PHOENIX_PORT', '6006')}/v1/traces"
            tracer_provider = trace_sdk.TracerProvider()
            tracer_provider.add_span_processor(
                SimpleSpanProcessor(OTLPSpanExporter(endpoint))
            )
            trace_api.set_tracer_provider(tracer_provider)

            # 自动instrument LlamaIndex
            LlamaIndexInstrumentor().instrument()

            print("✅ Phoenix追踪已配置")

        except Exception as e:
            print(f"⚠️  Phoenix启动失败: {e}")
            print("继续运行但不追踪...")
            self.enable_phoenix = False

    def _setup_llm(self):
        """配置LLM和Embedding模型 (DeepSeek API)"""

        # DeepSeek API配置
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        chat_model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")

        if not api_key:
            raise ValueError(
                "未找到DEEPSEEK_API_KEY! 请在.env文件中配置或设置环境变量"
            )

        # 初始化LLM (用于生成回答)
        self.llm = OpenAI(
            model=chat_model,
            api_key=api_key,
            api_base=base_url,
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            max_tokens=2048,
        )

        # 初始化Embedding模型
        # 注意: DeepSeek暂无专用embedding API,这里使用text-embedding-3-small
        # 如果你有OpenAI key,可以用于embedding; 或使用本地embedding模型
        embedding_model_name = os.getenv(
            "EMBEDDING_MODEL",
            "text-embedding-3-small"
        )

        # 如果设置了OpenAI key用于embedding
        openai_key = os.getenv("OPENAI_API_KEY", api_key)

        self.embed_model = OpenAIEmbedding(
            model=embedding_model_name,
            api_key=openai_key,
        )

        # 设置全局默认值
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap

        print(f"✅ LLM配置完成: {chat_model}")
        print(f"✅ Embedding配置完成: {embedding_model_name}")

    def load_documents(self, file_paths: Optional[List[str]] = None) -> List[Document]:
        """
        加载文档

        Args:
            file_paths: 指定文件路径列表,如果为None则加载data_dir下所有文档

        Returns:
            Document对象列表
        """
        if file_paths:
            # 加载指定文件
            documents = []
            for file_path in file_paths:
                reader = SimpleDirectoryReader(input_files=[file_path])
                documents.extend(reader.load_data())
        else:
            # 加载目录下所有文档
            if not self.data_dir.exists():
                raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")

            reader = SimpleDirectoryReader(
                input_dir=str(self.data_dir),
                recursive=True,
            )
            documents = reader.load_data()

        print(f"📄 已加载 {len(documents)} 个文档")
        return documents

    def build_index(self, documents: Optional[List[Document]] = None):
        """
        构建向量索引

        Args:
            documents: 文档列表,如果为None则从data_dir加载
        """
        if documents is None:
            documents = self.load_documents()

        if not documents:
            raise ValueError("没有文档可以索引!")

        print("🔨 正在构建向量索引...")

        # 创建索引
        self.index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True,
        )

        # 创建查询引擎
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.top_k,
        )

        self.query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=self.llm,
        )

        print("✅ 索引构建完成!")

    def query(self, question: str) -> Dict[str, Any]:
        """
        执行RAG查询

        Args:
            question: 用户问题

        Returns:
            包含答案和元数据的字典
        """
        if self.query_engine is None:
            raise RuntimeError("请先调用build_index()构建索引!")

        print(f"\n💭 问题: {question}")
        print("🔍 检索相关文档中...")

        # 执行查询 (自动被Phoenix追踪)
        response = self.query_engine.query(question)

        # 提取检索到的文档
        source_nodes = response.source_nodes if hasattr(response, 'source_nodes') else []

        result = {
            "question": question,
            "answer": str(response),
            "sources": [
                {
                    "text": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata,
                }
                for node in source_nodes
            ],
            "num_sources": len(source_nodes),
        }

        print(f"✅ 回答生成完成 (使用了 {len(source_nodes)} 个相关文档)")

        return result

    def print_result(self, result: Dict[str, Any]):
        """美化打印查询结果"""
        print("\n" + "="*80)
        print("📌 问题:")
        print(f"   {result['question']}")
        print("\n💡 回答:")
        print(f"   {result['answer']}")
        print(f"\n📚 参考文档 ({result['num_sources']}个):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n   [{i}] 相似度: {source['score']:.4f}")
            print(f"       内容片段: {source['text']}")
            if source['metadata']:
                print(f"       元数据: {source['metadata']}")
        print("="*80 + "\n")

    def close(self):
        """关闭Phoenix会话"""
        if self.phoenix_session:
            print("\n🛑 关闭Phoenix会话...")
            # Phoenix会话会在程序结束时自动关闭


# 便捷函数
def create_rag_system(**kwargs) -> PhoenixRAGSystem:
    """创建RAG系统实例"""
    return PhoenixRAGSystem(**kwargs)


if __name__ == "__main__":
    """
    测试脚本
    """
    # 创建RAG系统
    rag = create_rag_system(
        data_dir="./sample_data",
        chunk_size=512,
        chunk_overlap=50,
        top_k=3,
        enable_phoenix=True,
    )

    # 构建索引
    rag.build_index()

    # 测试查询
    test_questions = [
        "什么是机器学习?",
        "深度学习有哪些应用?",
    ]

    for question in test_questions:
        result = rag.query(question)
        rag.print_result(result)

    print(f"\n🌐 访问 Phoenix UI 查看追踪: {rag.phoenix_session.url if rag.phoenix_session else 'Phoenix未启用'}")

    # 保持程序运行以查看Phoenix UI
    input("\n按Enter键退出...")
    rag.close()
