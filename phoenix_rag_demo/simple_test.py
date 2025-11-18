"""
简单测试脚本 - 快速验证基础功能
不依赖Phoenix,用于快速测试RAG核心功能
"""

from dotenv import load_dotenv
from rag_system import PhoenixRAGSystem

load_dotenv()


def main():
    print("🧪 简单RAG测试 (无Phoenix追踪)\n")

    # 创建RAG系统 (禁用Phoenix)
    rag = PhoenixRAGSystem(
        data_dir="./sample_data",
        chunk_size=512,
        chunk_overlap=50,
        top_k=3,
        enable_phoenix=False,  # 禁用Phoenix以快速测试
    )

    # 构建索引
    rag.build_index()

    # 单个测试查询
    question = "什么是深度学习?"
    result = rag.query(question)
    rag.print_result(result)

    print("✅ 测试完成!")


if __name__ == "__main__":
    main()
