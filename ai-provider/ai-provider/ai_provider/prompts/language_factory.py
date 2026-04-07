"""Prompt factory for managing prompt templates."""

import os
import json
from typing import Any
from pathlib import Path


class LanguageFactory:
    def __init__(self):
        # 使用相对路径查找prompts目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        self.files_dir = project_root / "prompts"
        self._load()

    def _load(self):
        """加载所有prompt模板和配置文件"""
        try:
            # 加载语言代码配置
            self.all_language_codes = self._load_json_file("all-language-codes.json")
            self.all_language_names = {v: k for k, v in self.all_language_codes.items()}
            self.all_language_codes_clean = json.dumps(
                self.all_language_codes, separators=(",", ":")
            )
        except Exception as e:
            print(f"Warning: Failed to load: {e}")
            raise e

    def _load_json_file(self, filename: str) -> dict[str, Any]:
        """加载JSON文件"""
        file_path = self.files_dir / filename
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
        file_path = self.files_dir / filename
        if not file_path.exists():
            return ""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to load {filename}: {e}")
            return ""

    def get_all_language_codes_json(self) -> dict[str, Any]:
        return self.all_language_codes


# 全局实例
language_factory = LanguageFactory()
