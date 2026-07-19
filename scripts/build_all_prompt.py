#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_all_prompt.py — 一键生成全套标准化Prompt的工具脚本

功能说明：
    - 遍历 skills_md/ 目录下的所有Prompt文件
    - 读取 reference/ 和 assists/prompt_template/ 下的模板文件
    - 根据 global_param_config.yaml 自动填充变量
    - 生成标准化输出到指定目录
    - 支持命令行参数：--output-dir、--template、--dry-run
    - 包含详细的日志输出和错误处理
    - 使用argparse解析命令行参数

运行环境：Windows PowerShell + Python 3（仅使用标准库，无外部依赖）
"""

import argparse
import glob
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================
# 日志配置
# ============================================================

def setup_logging(level: int = logging.INFO) -> None:
    """配置日志输出的格式和级别。

    Args:
        level: 日志级别，默认为 logging.INFO。
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


# ============================================================
# 配置与模型
# ============================================================

class ProjectConfig:
    """项目配置类，加载和管理全局参数配置。

    Attributes:
        root_dir: 项目根目录路径。
        skills_dir: skills_md/ 目录路径。
        reference_dir: reference/ 目录路径。
        template_dir: assists/prompt_template/ 目录路径。
        output_dir: 生成输出目录路径。
        params: 从 global_param_config.yaml 解析的参数字典。
    """

    def __init__(self, root_dir: str) -> None:
        """初始化 ProjectConfig。

        Args:
            root_dir: 项目根目录的绝对路径。
        """
        self.root_dir: str = root_dir
        self.skills_dir: str = os.path.join(root_dir, "skills_md")
        self.reference_dir: str = os.path.join(root_dir, "reference")
        self.template_dir: str = os.path.join(root_dir, "assists", "prompt_template")
        self.output_dir: str = os.path.join(root_dir, "output")
        self.params: Dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """从 global_param_config.yaml 加载全局参数。

        使用简单的行解析方式加载YAML格式的配置（仅限键值对形式）。
        如果文件不存在或解析失败，记录错误但不中断运行。
        """
        config_path = os.path.join(self.root_dir, "global_param_config.yaml")
        if not os.path.isfile(config_path):
            logging.warning("配置文件不存在，使用默认参数: %s", config_path)
            self.params = self._default_params()
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or stripped.startswith("---"):
                        continue
                    match = re.match(r'^([\w_]+)\s*:\s*(.+)$', stripped)
                    if match:
                        key = match.group(1).strip()
                        value = match.group(2).strip().strip('"').strip("'")
                        self.params[key] = value
            logging.info("成功加载配置，共 %d 个参数", len(self.params))
        except Exception as e:
            logging.error("加载配置文件失败: %s", e)
            self.params = self._default_params()

    @staticmethod
    def _default_params() -> Dict[str, str]:
        """返回默认参数配置。

        Returns:
            包含默认参数的字典。
        """
        return {
            "author": "GuoFanDirector",
            "version": "1.0.0",
            "language": "zh-CN",
            "output_encoding": "utf-8",
        }


# ============================================================
# 模板引擎
# ============================================================

class TemplateEngine:
    """模板引擎，负责读取模板文件并用参数填充占位符。

    占位符格式：{{ variable_name }}
    """

    def __init__(self, params: Dict[str, str]) -> None:
        """初始化 TemplateEngine。

        Args:
            params: 用于填充模板的参数字典。
        """
        self.params = params

    def load_template(self, template_path: str) -> str:
        """读取模板文件内容。

        Args:
            template_path: 模板文件的绝对路径。

        Returns:
            模板文件内容的字符串。

        Raises:
            FileNotFoundError: 模板文件不存在时抛出。
        """
        if not os.path.isfile(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        logging.debug("已读取模板文件: %s (长度: %d 字符)", template_path, len(content))
        return content

    def fill_template(self, content: str) -> str:
        """用全局参数填充模板内容中的占位符。

        Args:
            content: 包含占位符的模板内容。

        Returns:
            填充了实际值的模板内容。
        """
        def _replacer(match: re.Match) -> str:
            var_name = match.group(1).strip()
            return self.params.get(var_name, match.group(0))

        result = re.sub(r'\{\{\s*(\w+)\s*\}\}', _replacer, content)
        filled_count = len(re.findall(r'\{\{\s*(\w+)\s*\}\}', content))
        logging.debug("填充了 %d 个占位符", filled_count)
        return result


# ============================================================
# Prompt 文件处理
# ============================================================

class PromptBuilder:
    """Prompt 构建器，负责遍历、读取、填充和输出Prompt文件。

    Attributes:
        config: 项目配置实例。
        engine: 模板引擎实例。
    """

    def __init__(self, config: ProjectConfig, engine: TemplateEngine) -> None:
        """初始化 PromptBuilder。

        Args:
            config: ProjectConfig 实例。
            engine: TemplateEngine 实例。
        """
        self.config = config
        self.engine = engine
        self.template_cache: Dict[str, str] = {}

    def scan_prompt_files(self) -> List[str]:
        """扫描 skills_md/ 目录下的所有 .md Prompt 文件。

        Returns:
            所有匹配的Prompt文件绝对路径列表。
        """
        pattern = os.path.join(self.config.skills_dir, "**", "*.md")
        files = sorted(glob.glob(pattern, recursive=True))
        logging.info("在 skills_md/ 下找到 %d 个Prompt文件", len(files))
        for f in files:
            logging.debug("  发现文件: %s", f)
        return files

    def read_prompt_file(self, file_path: str) -> Tuple[str, str]:
        """读取单个Prompt文件内容。

        Args:
            file_path: Prompt文件的绝对路径。

        Returns:
            元组 (文件名, 文件内容)。
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            filename = os.path.basename(file_path)
            logging.debug("已读取Prompt文件: %s", filename)
            return filename, content
        except Exception as e:
            logging.error("读取文件失败 %s: %s", file_path, e)
            return os.path.basename(file_path), ""

    def load_template_by_name(self, template_name: str) -> Optional[str]:
        """按名称加载模板文件。

        搜索顺序：
            1. assists/prompt_template/<template_name>
            2. reference/<template_name>

        Args:
            template_name: 模板文件名（可包含路径）。

        Returns:
            模板内容字符串；如果未找到则返回 None。
        """
        if template_name in self.template_cache:
            return self.template_cache[template_name]

        search_paths = [
            os.path.join(self.config.template_dir, template_name),
            os.path.join(self.config.reference_dir, template_name),
        ]

        for sp in search_paths:
            if os.path.isfile(sp):
                content = self.engine.load_template(sp)
                self.template_cache[template_name] = content
                return content

        logging.warning("未找到模板文件: %s (搜索路径: %s)", template_name, search_paths)
        return None

    def process_prompt(
        self,
        file_path: str,
        template_name: Optional[str] = None,
    ) -> Optional[str]:
        """处理单个Prompt文件：读取、填充模板、返回最终内容。

        Args:
            file_path: Prompt文件的绝对路径。
            template_name: 可选的模板文件名；如果提供则合并模板。

        Returns:
            最终处理后的内容字符串；失败时返回 None。
        """
        filename, content = self.read_prompt_file(file_path)
        if not content:
            return None

        # 填充全局参数
        content = self.engine.fill_template(content)

        # 如果指定了模板，合并模板
        if template_name:
            template_content = self.load_template_by_name(template_name)
            if template_content:
                template_content = self.engine.fill_template(template_content)
                content = template_content.replace("{{ CONTENT }}", content)
                logging.info("已将模板 '%s' 合并到文件: %s", template_name, filename)

        logging.info("已完成处理: %s", filename)
        return content

    def generate_output(
        self,
        output_dir: str,
        template_name: Optional[str] = None,
        dry_run: bool = False,
    ) -> int:
        """生成所有Prompt文件的标准化输出。

        Args:
            output_dir: 输出目录的绝对路径。
            template_name: 可选的模板文件名。
            dry_run: 如果为 True，仅模拟运行，不写文件。

        Returns:
            成功处理的文件数量。
        """
        files = self.scan_prompt_files()
        success_count = 0

        for file_path in files:
            result = self.process_prompt(file_path, template_name)
            if result is None:
                continue

            # 计算输出路径（保持相对目录结构）
            rel_path = os.path.relpath(file_path, self.config.skills_dir)
            output_path = os.path.join(output_dir, rel_path)

            if dry_run:
                logging.info("[DRY-RUN] 将输出到: %s (长度: %d 字符)", output_path, len(result))
                success_count += 1
                continue

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                logging.info("已生成文件: %s", output_path)
                success_count += 1
            except Exception as e:
                logging.error("写入文件失败 %s: %s", output_path, e)

        return success_count


# ============================================================
# 命令行入口
# ============================================================

def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    Returns:
        解析后的命名空间对象。
    """
    parser = argparse.ArgumentParser(
        description="一键生成全套标准化Prompt的工具脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python build_all_prompt.py  --output-dir ./output
  python build_all_prompt.py  --output-dir ./output --template default_template.md
  python build_all_prompt.py  --dry-run
  python build_all_prompt.py  --output-dir ./output --verbose
        """,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="指定输出目录（默认: <root>/output）",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="指定要合并的模板文件名称（位于 reference/ 或 assists/prompt_template/ 下）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="仅模拟运行，不实际写入文件",
    )
    parser.add_argument(
        "--root-dir",
        type=str,
        default=".",
        help="指定项目根目录（默认: 当前目录）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="输出详细日志（DEBUG级别）",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="将日志输出到指定文件",
    )

    return parser.parse_args()


def setup_file_logging(log_file: str, level: int = logging.INFO) -> None:
    """配置日志同时输出到文件。

    Args:
        log_file: 日志文件路径。
        level: 日志级别。
    """
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logging.getLogger().addHandler(file_handler)


def main() -> None:
    """主函数：解析参数、加载配置、执行生成流程。"""
    args = parse_args()

    # 配置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # 可选的文件日志
    if args.log_file:
        setup_file_logging(args.log_file, log_level)

    logging.info("=" * 60)
    logging.info("build_all_prompt.py 启动")
    logging.info("=" * 60)

    # 解析项目根目录
    root_dir = os.path.abspath(args.root_dir)
    if not os.path.isdir(root_dir):
        logging.error("项目根目录不存在: %s", root_dir)
        sys.exit(1)

    # 加载配置
    try:
        config = ProjectConfig(root_dir)
    except Exception as e:
        logging.error("初始化配置失败: %s", e)
        sys.exit(1)

    # 如果提供了输出目录，覆盖默认
    if args.output_dir:
        config.output_dir = os.path.abspath(args.output_dir)

    logging.info("项目根目录: %s", config.root_dir)
    logging.info("skills_md目录: %s", config.skills_dir)
    logging.info("输出目录: %s", config.output_dir)
    logging.info("dry-run模式: %s", args.dry_run)
    logging.info("模板文件: %s", args.template or "无")

    # 检查 skills_md 目录是否存在
    if not os.path.isdir(config.skills_dir):
        logging.error("skills_md/ 目录不存在: %s", config.skills_dir)
        logging.info("提示: 请在项目根目录下创建 skills_md/ 文件夹并放入Prompt文件")
        sys.exit(1)

    # 初始化模板引擎和构建器
    engine = TemplateEngine(config.params)
    builder = PromptBuilder(config, engine)

    # 执行生成
    try:
        success_count = builder.generate_output(
            output_dir=config.output_dir,
            template_name=args.template,
            dry_run=args.dry_run,
        )
    except Exception as e:
        logging.error("生成过程中发生异常: %s", e)
        sys.exit(1)

    # 输出汇总
    logging.info("=" * 60)
    if args.dry_run:
        logging.info("DRY-RUN 完成，共模拟处理 %d 个文件", success_count)
    else:
        logging.info("生成完成，共成功处理 %d 个文件，输出到: %s", success_count, config.output_dir)
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
