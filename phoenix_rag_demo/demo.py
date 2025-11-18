"""
Phoenix RAG 完整演示脚本
展示如何使用Arize Phoenix追踪和评估RAG系统
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from rag_system import PhoenixRAGSystem
from evaluate import evaluate_from_query_results

# 加载环境变量
load_dotenv()


def print_banner(text: str, char: str = "="):
    """打印标题横幅"""
    print(f"\n{char * 80}")
    print(f"{text.center(80)}")
    print(f"{char * 80}\n")


def run_basic_demo():
    """运行基础RAG演示"""
    print_banner("🚀 Phoenix RAG 基础演示", "=")

    # 1. 创建RAG系统
    print("步骤 1: 初始化RAG系统...")
    rag = PhoenixRAGSystem(
        data_dir="./sample_data",
        chunk_size=512,
        chunk_overlap=50,
        top_k=3,
        enable_phoenix=True,
    )

    # 2. 构建索引
    print("\n步骤 2: 构建向量索引...")
    rag.build_index()

    # 3. 测试查询
    print("\n步骤 3: 执行测试查询...")

    test_questions = [
        "什么是机器学习?",
        "深度学习有哪些主要应用?",
        "什么是卷积神经网络(CNN)?",
        "解释一下Transformer架构",
        "监督学习和无监督学习的区别是什么?",
    ]

    query_results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 查询 {i}/{len(test_questions)} ---")
        result = rag.query(question)
        rag.print_result(result)
        query_results.append(result)

    # 4. Phoenix UI 信息
    if rag.phoenix_session:
        print_banner("🌐 Phoenix 追踪可视化", "=")
        print(f"Phoenix UI 地址: {rag.phoenix_session.url}")
        print("\n在Phoenix UI中你可以看到:")
        print("  ✓ 每个查询的完整追踪链路")
        print("  ✓ LLM调用的详细信息(prompt、response、token使用)")
        print("  ✓ 向量检索的性能指标")
        print("  ✓ 整个RAG pipeline的时间分布")
        print("  ✓ 所有spans的层次结构视图")

    return rag, query_results


def run_evaluation_demo(query_results):
    """运行评估演示"""
    print_banner("📊 Phoenix 评估演示", "=")

    print("步骤 4: 使用Phoenix Evals评估RAG质量...\n")

    try:
        # 评估查询结果
        eval_results = evaluate_from_query_results(
            query_results,
            save_path="evaluation_results.json"
        )

        print("\n✅ 评估完成!")
        print("\n💡 评估说明:")
        print("  • 检索相关性: 评估检索的文档是否与问题相关")
        print("  • 幻觉检测: 评估回答是否基于检索的上下文,还是编造的")
        print("  • 评估结果已保存到: evaluation_results.json")

        return eval_results

    except Exception as e:
        print(f"\n⚠️  评估失败: {e}")
        print("提示: 评估功能需要OpenAI API key或兼容的API")
        print("      请确保在.env中设置了OPENAI_API_KEY或DEEPSEEK_API_KEY")
        return None


def run_interactive_demo(rag):
    """运行交互式演示"""
    print_banner("💬 交互式问答模式", "=")

    print("输入你的问题,或输入 'q' 退出")
    print("所有查询都会被Phoenix追踪\n")

    while True:
        try:
            question = input("❓ 你的问题: ").strip()

            if question.lower() in ['q', 'quit', 'exit', '退出']:
                break

            if not question:
                continue

            result = rag.query(question)
            rag.print_result(result)

        except KeyboardInterrupt:
            print("\n\n退出交互模式...")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


def main():
    """主函数"""
    print_banner("🎯 Arize Phoenix RAG 完整演示", "█")

    print("本演示将展示:")
    print("  1. 使用DeepSeek API构建RAG系统")
    print("  2. 使用Phoenix追踪所有RAG操作")
    print("  3. 使用Phoenix Evals评估RAG质量")
    print("  4. 在Phoenix UI中可视化追踪数据")

    # 检查环境配置
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  警告: 未找到DEEPSEEK_API_KEY")
        print("请创建 .env 文件并设置API密钥")
        print("参考 .env.example 文件")
        response = input("\n是否继续? (y/n): ")
        if response.lower() != 'y':
            return

    try:
        # 运行基础演示
        rag, query_results = run_basic_demo()

        # 运行评估演示
        eval_results = run_evaluation_demo(query_results)

        # 询问是否进入交互模式
        print_banner("", "-")
        response = input("是否进入交互式问答模式? (y/n): ")
        if response.lower() == 'y':
            run_interactive_demo(rag)

        # 最终提示
        print_banner("✅ 演示完成", "=")
        if rag.phoenix_session:
            print(f"🌐 Phoenix UI 仍在运行: {rag.phoenix_session.url}")
            print("\n建议:")
            print("  1. 打开Phoenix UI查看所有追踪数据")
            print("  2. 探索每个span的详细信息")
            print("  3. 分析RAG系统的性能瓶颈")
            print("  4. 查看evaluation_results.json了解质量评估")
            input("\n按Enter键退出并关闭Phoenix...")

        rag.close()
        print("\n👋 感谢使用Phoenix RAG演示!")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
