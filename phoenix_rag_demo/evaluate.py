"""
Phoenix RAG 评估脚本
使用Phoenix Evals对RAG系统进行质量评估
包括: QA正确性、幻觉检测、检索相关性等评估指标
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

import phoenix as px
from phoenix.evals import (
    OpenAIModel,
    llm_classify,
    RAG_RELEVANCY_PROMPT_TEMPLATE,
    HALLUCINATION_PROMPT_TEMPLATE,
)

# 加载环境变量
load_dotenv()


@dataclass
class EvaluationResult:
    """评估结果数据类"""
    question: str
    answer: str
    context: str
    relevance_score: Optional[str] = None
    relevance_explanation: Optional[str] = None
    hallucination_score: Optional[str] = None
    hallucination_explanation: Optional[str] = None


class RAGEvaluator:
    """
    RAG系统评估器

    使用Phoenix Evals评估RAG系统的质量:
    1. 检索相关性 (Retrieval Relevancy): 检索的文档是否与问题相关
    2. 幻觉检测 (Hallucination): 回答是否基于检索的上下文
    3. QA正确性 (可选): 回答是否正确回答了问题
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        初始化评估器

        Args:
            model_name: 用于评估的模型名称
        """
        # 配置评估模型
        # 注意: Phoenix Evals目前主要支持OpenAI模型
        # 如果使用DeepSeek,需要通过OpenAI兼容接口
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")

        if not api_key:
            raise ValueError(
                "需要设置OPENAI_API_KEY或DEEPSEEK_API_KEY用于评估"
            )

        self.eval_model = OpenAIModel(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )

        print(f"✅ 评估模型已配置: {model_name}")

    def evaluate_relevance(
        self,
        questions: List[str],
        contexts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        评估检索相关性

        Args:
            questions: 问题列表
            contexts: 对应的检索上下文列表

        Returns:
            评估结果列表
        """
        print("\n🔍 评估检索相关性...")

        # 准备评估数据
        eval_data = [
            {"input": q, "reference": c}
            for q, c in zip(questions, contexts)
        ]

        # 执行评估
        results = llm_classify(
            dataframe=eval_data,
            model=self.eval_model,
            template=RAG_RELEVANCY_PROMPT_TEMPLATE,
            rails=["relevant", "irrelevant"],
        )

        print(f"✅ 相关性评估完成: {len(results)} 条")
        return results

    def evaluate_hallucination(
        self,
        answers: List[str],
        contexts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        评估幻觉 (Hallucination)

        Args:
            answers: 回答列表
            contexts: 对应的上下文列表

        Returns:
            评估结果列表
        """
        print("\n🎭 评估幻觉检测...")

        # 准备评估数据
        eval_data = [
            {"input": c, "output": a}
            for a, c in zip(answers, contexts)
        ]

        # 执行评估
        results = llm_classify(
            dataframe=eval_data,
            model=self.eval_model,
            template=HALLUCINATION_PROMPT_TEMPLATE,
            rails=["factual", "hallucinated"],
        )

        print(f"✅ 幻觉检测完成: {len(results)} 条")
        return results

    def evaluate_qa_dataset(
        self,
        qa_pairs: List[Dict[str, str]],
        save_path: Optional[str] = None,
    ) -> List[EvaluationResult]:
        """
        评估完整的QA数据集

        Args:
            qa_pairs: QA对列表,每个元素包含 question, answer, context
            save_path: 保存结果的路径 (可选)

        Returns:
            评估结果列表
        """
        print(f"\n📊 开始评估 {len(qa_pairs)} 个QA对...")

        # 提取数据
        questions = [pair["question"] for pair in qa_pairs]
        answers = [pair["answer"] for pair in qa_pairs]
        contexts = [pair["context"] for pair in qa_pairs]

        # 评估相关性
        relevance_results = self.evaluate_relevance(questions, contexts)

        # 评估幻觉
        hallucination_results = self.evaluate_hallucination(answers, contexts)

        # 合并结果
        evaluation_results = []
        for i, pair in enumerate(qa_pairs):
            result = EvaluationResult(
                question=pair["question"],
                answer=pair["answer"],
                context=pair["context"],
                relevance_score=relevance_results[i].get("label"),
                relevance_explanation=relevance_results[i].get("explanation"),
                hallucination_score=hallucination_results[i].get("label"),
                hallucination_explanation=hallucination_results[i].get("explanation"),
            )
            evaluation_results.append(result)

        # 打印统计
        self._print_statistics(evaluation_results)

        # 保存结果
        if save_path:
            self._save_results(evaluation_results, save_path)

        return evaluation_results

    def _print_statistics(self, results: List[EvaluationResult]):
        """打印评估统计信息"""
        total = len(results)

        # 相关性统计
        relevant_count = sum(
            1 for r in results if r.relevance_score == "relevant"
        )
        relevance_rate = relevant_count / total * 100 if total > 0 else 0

        # 幻觉统计
        factual_count = sum(
            1 for r in results if r.hallucination_score == "factual"
        )
        factual_rate = factual_count / total * 100 if total > 0 else 0

        print("\n" + "="*80)
        print("📈 评估统计")
        print("="*80)
        print(f"总样本数: {total}")
        print(f"\n检索相关性:")
        print(f"  - 相关: {relevant_count}/{total} ({relevance_rate:.1f}%)")
        print(f"  - 不相关: {total - relevant_count}/{total} ({100-relevance_rate:.1f}%)")
        print(f"\n幻觉检测:")
        print(f"  - 基于事实: {factual_count}/{total} ({factual_rate:.1f}%)")
        print(f"  - 有幻觉: {total - factual_count}/{total} ({100-factual_rate:.1f}%)")
        print("="*80 + "\n")

    def _save_results(self, results: List[EvaluationResult], save_path: str):
        """保存评估结果到JSON文件"""
        results_dict = [asdict(r) for r in results]

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        print(f"💾 评估结果已保存到: {save_path}")


def evaluate_from_query_results(
    query_results: List[Dict[str, Any]],
    save_path: str = "evaluation_results.json",
) -> List[EvaluationResult]:
    """
    从RAG查询结果进行评估

    Args:
        query_results: RAG系统的查询结果列表
        save_path: 保存路径

    Returns:
        评估结果
    """
    # 转换为评估格式
    qa_pairs = []
    for result in query_results:
        # 合并所有source文本作为context
        context = "\n\n".join([
            source["text"] for source in result.get("sources", [])
        ])

        qa_pairs.append({
            "question": result["question"],
            "answer": result["answer"],
            "context": context,
        })

    # 执行评估
    evaluator = RAGEvaluator()
    return evaluator.evaluate_qa_dataset(qa_pairs, save_path)


if __name__ == "__main__":
    """
    测试评估功能
    """
    # 示例QA数据
    test_qa_pairs = [
        {
            "question": "什么是机器学习?",
            "answer": "机器学习是人工智能的一个分支,它使计算机能够在没有明确编程的情况下学习和改进。",
            "context": "机器学习是人工智能(AI)的一个子领域,专注于开发能够从数据中学习的算法。通过学习,计算机程序能够在特定任务上自动改进其性能。",
        },
        {
            "question": "深度学习用于什么?",
            "answer": "深度学习主要用于图像识别和自然语言处理。",
            "context": "深度学习是机器学习的一个子集,使用多层神经网络。它在计算机视觉、自然语言处理、语音识别等领域都有广泛应用。",
        },
    ]

    # 创建评估器
    evaluator = RAGEvaluator(model_name="gpt-4o-mini")

    # 评估
    results = evaluator.evaluate_qa_dataset(
        test_qa_pairs,
        save_path="test_evaluation_results.json"
    )

    # 打印详细结果
    print("\n📋 详细评估结果:")
    for i, result in enumerate(results, 1):
        print(f"\n--- 问题 {i} ---")
        print(f"问题: {result.question}")
        print(f"相关性: {result.relevance_score} - {result.relevance_explanation}")
        print(f"幻觉: {result.hallucination_score} - {result.hallucination_explanation}")
