#!/usr/bin/env python3
"""
精度测试框架主程序

使用方法：
python eva.py --ground-truth input.csv --model "bedrock.classify_video_is_funny"
"""

import argparse
import csv
import sys
import os
import logging
from typing import Dict, Any, List
from pathlib import Path

import dotenv

dotenv.load_dotenv()

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from metrics import EvaluationMetrics
from models import get_model_function, list_available_models


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_test_data(csv_file: str) -> List[Dict[str, Any]]:
    """
    加载测试数据

    Args:
        csv_file: CSV文件路径

    Returns:
        测试数据列表
    """
    test_data = []

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames

            if not header:
                raise ValueError("CSV文件为空或格式错误")

            logger.info(f"CSV文件header: {header}")

            # 读取数据
            for row_num, row in enumerate(
                reader, start=2
            ):  # 从第2行开始计数（第1行是header）
                try:
                    params = {}
                    for col_name, value in row.items():
                        # 去掉无用空格
                        value = value.strip()
                        if col_name == "expect_result":
                            try:
                                expect_result = int(value)
                                if expect_result not in [0, 1]:
                                    logger.warning(
                                        f"第{row_num}行: 期望结果必须是0或1，当前值: {expect_result}"
                                    )
                                    continue
                                params["expect_result"] = expect_result
                            except ValueError:
                                logger.warning(
                                    f"第{row_num}行: expect_result必须是整数，当前值: {value}"
                                )
                                continue
                        else:
                            params[col_name] = value
                    # 只校验expect_result
                    if "expect_result" not in params:
                        logger.warning(f"第{row_num}行: 缺少expect_result字段")
                        continue
                    test_data.append(params)
                except Exception as e:
                    logger.warning(f"第{row_num}行数据处理失败: {e}")
                    continue
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到CSV文件: {csv_file}")
    except Exception as e:
        raise Exception(f"读取CSV文件失败: {e}")
    logger.info(f"成功加载 {len(test_data)} 条测试数据")
    return test_data


def run_evaluation(
    test_data: List[Dict[str, Any]], model_name: str
) -> EvaluationMetrics:
    """
    运行评估
    """
    # 获取模型函数
    model_function = get_model_function(model_name)

    # 创建评估指标计算器
    metrics = EvaluationMetrics()

    logger.info(f"开始评估模型: {model_name}")
    logger.info(f"测试数据数量: {len(test_data)}")

    for i, data in enumerate(test_data, 1):
        expect_result = data["expect_result"]
        content_id = data.get("content_id", "-")
        logger.info(f"处理第 {i}/{len(test_data)} 条数据: content_id={content_id}")
        try:
            predicted_result = model_function(**data)
            if predicted_result not in [0, 1]:
                logger.warning(
                    f"模型返回无效结果: {predicted_result}，content_id={content_id}"
                )
                predicted_result = 0
            metrics.add_result(expect_result, predicted_result)
            status = "✅" if expect_result == predicted_result else "🚫"
            logger.info(
                f"{status} content_id={content_id}, 期望={expect_result}, 预测={predicted_result}"
            )
        except Exception as e:
            logger.error(f"处理数据失败: content_id={content_id}, 错误={e}")
            metrics.add_result(expect_result, 0)
    return metrics


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="精度测试框架")
    parser.add_argument("--ground-truth", help="包含真实标签的CSV文件路径")
    parser.add_argument("--model", help="模型函数名称，格式: package.function_name")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用的模型")
    parser.add_argument("--verbose", action="store_true", help="显示详细日志")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 列出可用模型
    if args.list_models:
        print("可用的模型:")
        for model in list_available_models():
            print(f"  - {model}")
        return

    # 检查必需参数
    if not args.ground_truth or not args.model:
        parser.error("--ground-truth 和 --model 参数是必需的（除非使用 --list-models）")

    # 验证CSV文件
    if not os.path.exists(args.ground_truth):
        logger.error(f"CSV文件不存在: {args.ground_truth}")
        sys.exit(1)

    try:
        # 加载测试数据
        test_data = load_test_data(args.ground_truth)

        if not test_data:
            logger.error("没有有效的测试数据")
            sys.exit(1)

        # 运行评估
        metrics = run_evaluation(test_data, args.model)

        # 打印结果
        metrics.print_detailed_metrics()

    except Exception as e:
        logger.error(f"评估失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
