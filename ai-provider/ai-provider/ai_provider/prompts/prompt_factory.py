"""Prompt factory for managing prompt templates."""

import os
import json
from typing import Any
from pathlib import Path

from .language_factory import language_factory


class PromptFactory:
    """Prompt factory for loading and managing prompt templates."""

    def __init__(self):
        # 使用相对路径查找prompts目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        self.prompts_dir = project_root / "prompts"
        self._load()

    def _load(self):
        """加载所有prompt模板和配置文件"""
        try:

            # 加载提取配置
            self.all_categories = self._load_json_file("all-categories.json")
            self.all_categories_clean = json.dumps(
                self.all_categories, separators=(",", ":")
            )

            # 加载提取配置 - 去掉了搞笑分类
            self.all_categories_exclude_funny = self.all_categories.copy()
            self.all_categories_exclude_funny.get("Entertainment", {}).pop(
                "Funny", None
            )
            self.all_categories_exclude_funny_clean = json.dumps(
                self.all_categories_exclude_funny, separators=(",", ":")
            )

            # 加载 web3 分类配置
            self.web3_categories = self._load_json_file("web3-categories.json")
            self.web3_categories_clean = json.dumps(
                self.web3_categories, separators=(",", ":")
            )

            # 统一的内容提取prompt
            self.prompt_for_unified_content_classification = self._load_md_file(
                "prompt-unified-content-classification.md"
            )
            
            # Pellet summaries生成prompt (阶段1)
            self.prompt_for_pellet_summaries = self._load_md_file(
                "prompt-pellet-summaries.md"
            )

            # Pellet page生成prompt (阶段2)
            self.prompt_for_pellet_page = self._load_md_file(
                "prompt-pellet-page.md"
            )

            # 替换变量
            self._replace_variables()
        except Exception as e:
            print(f"Warning: Failed to load prompts: {e}")
            raise e

    def _load_json_file(self, filename: str) -> dict[str, Any]:
        """加载JSON文件"""
        file_path = self.prompts_dir / filename
        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {filename}: {e}")
            return {}

    def _load_md_file(self, filename: str) -> str:
        """加载Markdown文件"""
        file_path = self.prompts_dir / filename
        if not file_path.exists():
            return ""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to load {filename}: {e}")
            return ""

    def _replace_variables(self):
        """替换prompt中的变量"""
        replacements = {
            "{{ all-language-codes }}": language_factory.all_language_codes_clean,
        }

        # 替换所有prompt模板中的 all-language-codes 变量
        for attr_name in dir(self):
            if attr_name.startswith("prompt_"):
                prompt_content = getattr(self, attr_name)
                if isinstance(prompt_content, str):
                    for key, value in replacements.items():
                        prompt_content = prompt_content.replace(key, value)
                    setattr(self, attr_name, prompt_content)

    def get_prompt_for_unified_content_classification(self) -> str:
        return self.prompt_for_unified_content_classification

    def get_prompt_for_pellet_summaries(self) -> str:
        return self.prompt_for_pellet_summaries

    def get_prompt_for_pellet_page(self) -> str:
        return self.prompt_for_pellet_page


# 全局实例
prompt_factory = PromptFactory()
