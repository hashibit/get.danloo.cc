"""
精度测试指标计算模块

计算准确率、召回率、精确率等指标
"""

from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """评估指标计算器"""

    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0

    def add_result(self, expected: int, predicted: int):
        """
        添加一个预测结果

        Args:
            expected: 期望结果 (0 或 1)
            predicted: 预测结果 (0 或 1)
        """
        if expected == 1 and predicted == 1:
            self.true_positives += 1
        elif expected == 1 and predicted == 0:
            self.false_negatives += 1
        elif expected == 0 and predicted == 1:
            self.false_positives += 1
        elif expected == 0 and predicted == 0:
            self.true_negatives += 1
        else:
            logger.warning(
                f"无效的期望值或预测值: expected={expected}, predicted={predicted}"
            )

    def calculate_metrics(self) -> Dict[str, float]:
        """
        计算各项指标

        Returns:
            包含各项指标的字典
        """
        total = (
            self.true_positives
            + self.false_positives
            + self.true_negatives
            + self.false_negatives
        )

        if total == 0:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "total_samples": 0,
            }

        # 准确率 = (TP + TN) / (TP + TN + FP + FN)
        accuracy = (self.true_positives + self.true_negatives) / total

        # 精确率 = TP / (TP + FP)
        precision = (
            self.true_positives / (self.true_positives + self.false_positives)
            if (self.true_positives + self.false_positives) > 0
            else 0.0
        )

        # 召回率 = TP / (TP + FN)
        recall = (
            self.true_positives / (self.true_positives + self.false_negatives)
            if (self.true_positives + self.false_negatives) > 0
            else 0.0
        )

        # F1分数 = 2 * (精确率 * 召回率) / (精确率 + 召回率)
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "total_samples": total,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
        }

    def print_confusion_matrix(self):
        """打印混淆矩阵"""
        print("\n混淆矩阵:")
        print("=" * 40)
        print(f"{'实际\\预测':>12} {'预测为0':>8} {'预测为1':>8}")
        print("-" * 40)
        print(f"{'实际为0':>12} {self.true_negatives:>8} {self.false_positives:>8}")
        print(f"{'实际为1':>12} {self.false_negatives:>8} {self.true_positives:>8}")
        print("=" * 40)

        # 添加解释
        print("\n说明:")
        print(f"  TN (真阴性): {self.true_negatives} - 实际为0，预测为0")
        print(f"  FP (假阳性): {self.false_positives} - 实际为0，预测为1")
        print(f"  FN (假阴性): {self.false_negatives} - 实际为1，预测为0")
        print(f"  TP (真阳性): {self.true_positives} - 实际为1，预测为1")

    def print_detailed_metrics(self):
        """打印详细指标"""
        metrics = self.calculate_metrics()

        print("\n=== 评估结果 ===")
        print(f"总样本数: {metrics['total_samples']}")
        print(
            f"准确率 (Accuracy):     {metrics['accuracy']:.4f} ({metrics['accuracy']*100:6.2f}%)  = (TP + TN) / (TP + TN + FP + FN)"
        )
        print(
            f"精确率 (Precision):    {metrics['precision']:.4f} ({metrics['precision']*100:6.2f}%)  = TP / (TP + FP)"
        )
        print(
            f"召回率 (Recall):       {metrics['recall']:.4f} ({metrics['recall']*100:6.2f}%)  = TP / (TP + FN)"
        )
        print(
            f"F1分数 (F1-Score):     {metrics['f1_score']:.4f} ({metrics['f1_score']*100:6.2f}%)  = 2 * (Precision * Recall) / (Precision + Recall)"
        )

        print(f"\n详细统计:")
        print(f"真阳性 (TP): {metrics['true_positives']}")
        print(f"假阳性 (FP): {metrics['false_positives']}")
        print(f"真阴性 (TN): {metrics['true_negatives']}")
        print(f"假阴性 (FN): {metrics['false_negatives']}")

        self.print_confusion_matrix()
