#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_check.py — MD格式、表格规范校验工具

功能说明：
    - 遍历指定目录下所有.md文件
    - 检查表头对齐规则（表头与分隔线对齐）
    - 检查缩进层级规范
    - 检查文件头元数据格式
    - 检查资产引用路径格式
    - 输出检查报告（通过的/不通过的）
    - 支持 --fix 参数自动修复常见格式问题
    - 支持 --dir 参数指定检查目录

运行环境：Windows PowerShell + Python 3（仅使用标准库，无外部依赖）
"""

import argparse
import glob
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
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
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ============================================================
# 检查项结果枚举
# ============================================================

class CheckStatus(Enum):
    """检查状态枚举。"""
    PASS = "通过"
    FAIL = "不通过"
    WARN = "警告"
    SKIP = "跳过"
    FIXED = "已修复"


# ============================================================
# 数据模型
# ============================================================

@dataclass
class CheckResult:
    """单个检查项的结果。

    Attributes:
        file_path: 被检查的文件路径。
        check_type: 检查类型名称。
        line_number: 问题所在行号（0表示不适用）。
        status: 检查状态。
        message: 描述信息。
    """
    file_path: str
    check_type: str
    line_number: int
    status: CheckStatus
    message: str


@dataclass
class FileReport:
    """单个文件的检查报告。

    Attributes:
        file_path: 文件路径。
        results: 检查结果列表。
    """
    file_path: str
    results: List[CheckResult] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        """通过检查的数量。"""
        return sum(1 for r in self.results if r.status == CheckStatus.PASS)

    @property
    def fail_count(self) -> int:
        """未通过检查的数量。"""
        return sum(1 for r in self.results if r.status == CheckStatus.FAIL)

    @property
    def warn_count(self) -> int:
        """警告的数量。"""
        return sum(1 for r in self.results if r.status == CheckStatus.WARN)

    @property
    def fixed_count(self) -> int:
        """已修复的数量。"""
        return sum(1 for r in self.results if r.status == CheckStatus.FIXED)

    @property
    def has_issues(self) -> bool:
        """是否存在需要关注的问题。"""
        return self.fail_count > 0 or self.warn_count > 0

    def add_result(self, result: CheckResult) -> None:
        """添加一条检查结果。

        Args:
            result: 检查结果实例。
        """
        self.results.append(result)


# ============================================================
# 检查器基类
# ============================================================

class BaseChecker:
    """检查器基类，提供公共方法。"""

    def __init__(self, fix_mode: bool = False) -> None:
        """初始化检查器。

        Args:
            fix_mode: 是否启用自动修复模式。
        """
        self.fix_mode = fix_mode
        self.fixed_lines: Dict[str, List[Tuple[int, str]]] = {}

    def report(
        self,
        file_path: str,
        check_type: str,
        line_number: int,
        status: CheckStatus,
        message: str,
    ) -> CheckResult:
        """创建一条检查结果。

        Args:
            file_path: 文件路径。
            check_type: 检查类型。
            line_number: 行号。
            status: 状态。
            message: 描述信息。

        Returns:
            检查结果实例。
        """
        return CheckResult(
            file_path=file_path,
            check_type=check_type,
            line_number=line_number,
            status=status,
            message=message,
        )


# ============================================================
# 表头对齐检查
# ============================================================

class TableAlignmentChecker(BaseChecker):
    """检查Markdown表格表头对齐规则。

    Markdown表格标准格式示例：
        | 名称   | 年龄 | 城市    |
        |--------|:----:|--------:|
        | 张三   | 28   | 北京    |
    """

    TYPE = "表格对齐检查"

    def check(self, file_path: str, lines: List[str], report: FileReport) -> None:
        """检查文件中的表格对齐规则。

        Args:
            file_path: 文件路径。
            lines: 文件的行列表。
            report: 文件检查报告。
        """
        in_table = False
        header_line_idx = -1
        separator_line_idx = -1

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 检测表格行：以 | 开头
            if not stripped.startswith("|"):
                if in_table:
                    # 表格结束
                    in_table = False
                continue

            # 检测分隔行（第二行，包含 --- 或 :--- 等）
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                separator_line_idx = i
                if not in_table:
                    in_table = True
                # 检查分隔线与表头的对齐
                if header_line_idx > 0:
                    self._check_header_separator_alignment(
                        file_path, lines, header_line_idx, separator_line_idx, report
                    )
                continue

            # 如果尚未检测到分隔行，记录为表头候选
            if not in_table:
                header_line_idx = i
                in_table = True
            elif separator_line_idx > 0 and i > separator_line_idx:
                # 表格内容行
                pass

        # 如果没有在表格中，重置状态
        if not in_table:
            header_line_idx = -1
            separator_line_idx = -1

    def _check_header_separator_alignment(
        self,
        file_path: str,
        lines: List[str],
        header_idx: int,
        sep_idx: int,
        report: FileReport,
    ) -> None:
        """检查表头与分隔线的列数对齐。

        Args:
            file_path: 文件路径。
            lines: 文件行列表。
            header_idx: 表头行号（1-based）。
            sep_idx: 分隔线行号（1-based）。
            report: 报告对象。
        """
        header_line = lines[header_idx - 1].strip()
        sep_line = lines[sep_idx - 1].strip()

        # 提取列数
        def count_columns(line: str) -> int:
            """计算表格列数。

            Args:
                line: 表格行字符串。

            Returns:
                列的数量。
            """
            parts = [p.strip() for p in line.split("|")]
            # 过滤空的首尾部分
            parts = [p for p in parts if p]
            return len(parts)

        header_cols = count_columns(header_line)
        sep_cols = count_columns(sep_line)

        if header_cols != sep_cols:
            msg = (
                f"表头({header_cols}列)与分隔线({sep_cols}列)列数不匹配"
            )
            report.add_result(
                self.report(file_path, self.TYPE, header_idx, CheckStatus.FAIL, msg)
            )

            if self.fix_mode:
                self._fix_table_alignment(file_path, lines, header_idx, sep_idx)
        else:
            report.add_result(
                self.report(
                    file_path, self.TYPE, header_idx, CheckStatus.PASS, "表头对齐正确"
                )
            )

    def _fix_table_alignment(
        self,
        file_path: str,
        lines: List[str],
        header_idx: int,
        sep_idx: int,
    ) -> None:
        """尝试修复表头与分隔线对齐问题。

        Args:
            file_path: 文件路径。
            lines: 文件行列表。
            header_idx: 表头行号（1-based）。
            sep_idx: 分隔线行号（1-based）。
        """
        header_line = lines[header_idx - 1].strip()

        def count_parts(line: str) -> List[str]:
            """按 | 分割获取单元格。

            Args:
                line: 表格行字符串。

            Returns:
                单元格列表。
            """
            parts = line.split("|")
            return [p for p in parts]

        header_parts = count_parts(header_line)
        header_col_count = len([p for p in header_parts if p.strip()])

        # 重建分隔线，使列数与表头一致
        new_sep_parts = []
        for part in header_parts:
            if part.strip():
                new_sep_parts.append(" --- ")
            else:
                new_sep_parts.append("")

        # 组装新的分隔行
        new_sep_line = "|".join(new_sep_parts)
        if not new_sep_line.startswith("|"):
            new_sep_line = "|" + new_sep_line
        if not new_sep_line.endswith("|"):
            new_sep_line += "|"

        # 记录修复
        if file_path not in self.fixed_lines:
            self.fixed_lines[file_path] = []
        self.fixed_lines[file_path].append((sep_idx, new_sep_line))
        logging.debug("表格对齐修复记录: %s 第%d行", file_path, sep_idx)


# ============================================================
# 缩进层级检查
# ============================================================

class IndentationChecker(BaseChecker):
    """检查Markdown文件中缩进和层级规范。"""

    TYPE = "缩进层级检查"
    INDENT_UNIT = 2  # Markdown推荐每级缩进2个空格
    MAX_LEVEL = 6    # 最大允许层级

    def check(self, file_path: str, lines: List[str], report: FileReport) -> None:
        """检查文件中所有行的缩进规范。

        Args:
            file_path: 文件路径。
            lines: 文件的行列表。
            report: 文件检查报告。
        """
        for i, line in enumerate(lines, start=1):
            stripped = line.rstrip("\n\r")
            if not stripped.strip():
                continue

            leading_spaces = len(stripped) - len(stripped.lstrip())
            indent_level = leading_spaces // self.INDENT_UNIT

            # 检查缩进是否为单位整数倍
            if leading_spaces > 0 and leading_spaces % self.INDENT_UNIT != 0:
                msg = (
                    f"缩进 {leading_spaces} 个空格不是 {self.INDENT_UNIT} 的整数倍"
                    f" (期望: {round(leading_spaces / self.INDENT_UNIT) * self.INDENT_UNIT})"
                )
                report.add_result(
                    self.report(file_path, self.TYPE, i, CheckStatus.FAIL, msg)
                )
                continue

            # 检查层级深度
            if indent_level > self.MAX_LEVEL:
                msg = f"缩进层级 {indent_level} 超过最大允许层级 {self.MAX_LEVEL}"
                report.add_result(
                    self.report(file_path, self.TYPE, i, CheckStatus.WARN, msg)
                )
                continue

            # 缩进正确
            report.add_result(
                self.report(
                    file_path, self.TYPE, i, CheckStatus.PASS, f"缩进规范 (层级={indent_level})"
                )
            )

    def apply_fix(self, file_path: str, lines: List[str]) -> List[str]:
        """应用缩进修复。

        Args:
            file_path: 文件路径。
            lines: 原始行列表。

        Returns:
            修复后的行列表。
        """
        if file_path not in self.fixed_lines:
            return lines

        fixed_lines_map = {idx: new_content for idx, new_content in self.fixed_lines[file_path]}
        result = list(lines)

        for line_idx, new_content in fixed_lines_map.items():
            if 1 <= line_idx <= len(result):
                result[line_idx - 1] = new_content + "\n"

        return result


# ============================================================
# 文件头元数据检查
# ============================================================

class FrontMatterChecker(BaseChecker):
    """检查Markdown文件头元数据格式（YAML front matter）。

    期望格式：
        ---
        title: 标题
        author: 作者
        version: 1.0.0
        date: 2024-01-01
        ---
    """

    TYPE = "文件头元数据检查"

    def check(self, file_path: str, lines: List[str], report: FileReport) -> None:
        """检查文件头元数据格式。

        Args:
            file_path: 文件路径。
            lines: 文件的行列表。
            report: 文件检查报告。
        """
        if not lines:
            report.add_result(
                self.report(file_path, self.TYPE, 0, CheckStatus.SKIP, "空文件，跳过检查")
            )
            return

        # 检查第一行是否为 ---
        first_line = lines[0].strip()
        if first_line != "---":
            report.add_result(
                self.report(
                    file_path, self.TYPE, 1, CheckStatus.SKIP, "文件无YAML front matter，跳过检查"
                )
            )
            return

        # 查找结束 ---
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            report.add_result(
                self.report(
                    file_path, self.TYPE, 1, CheckStatus.FAIL, "未找到front matter结束标记 ---"
                )
            )
            return

        # 检查front matter内部的格式
        field_count = 0
        has_error = False
        for i in range(1, end_idx):
            line = lines[i].strip()
            if not line:
                continue
            # 期望格式: key: value
            if not re.match(r'^[\w\-]+:\s*.+$', line):
                msg = f"元数据行格式无效 (期望: 'key: value'): {line}"
                report.add_result(
                    self.report(file_path, self.TYPE, i + 1, CheckStatus.FAIL, msg)
                )
                has_error = True
            else:
                field_count += 1

        if has_error:
            report.add_result(
                self.report(
                    file_path, self.TYPE, 1, CheckStatus.FAIL,
                    f"front matter中有格式问题 (共 {field_count} 个有效字段)",
                )
            )
        else:
            report.add_result(
                self.report(
                    file_path, self.TYPE, 1, CheckStatus.PASS,
                    f"front matter格式正确 (共 {field_count} 个字段)",
                )
            )


# ============================================================
# 资产引用路径检查
# ============================================================

class AssetReferenceChecker(BaseChecker):
    """检查Markdown中资产引用路径格式。

    检查内容：
        - 图片引用: ![alt](path)
        - 链接引用: [text](path)
        - 路径格式是否合法
        - 是否使用相对路径
    """

    TYPE = "资产引用路径检查"
    VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}
    VALID_ASSET_EXTENSIONS = {".md", ".pdf", ".xlsx", ".csv", ".json", ".yaml", ".yml"}

    def check(self, file_path: str, lines: List[str], report: FileReport) -> None:
        """检查文件中的资产引用路径。

        Args:
            file_path: 文件路径。
            lines: 文件的行列表。
            report: 文件检查报告。
        """
        for i, line in enumerate(lines, start=1):
            # 匹配Markdown图片引用: ![alt](path)
            image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            for alt_text, path in image_refs:
                self._validate_path(
                    file_path, i, path, "图片", report
                )

            # 匹配Markdown链接引用: [text](path)
            # 排除图片引用（排除 ! 开头的）
            link_refs = re.findall(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)', line)
            for link_text, path in link_refs:
                self._validate_path(
                    file_path, i, path, "链接", report
                )

    def _validate_path(
        self,
        file_path: str,
        line_number: int,
        path: str,
        ref_type: str,
        report: FileReport,
    ) -> None:
        """验证单个引用路径的格式。

        Args:
            file_path: 文件路径。
            line_number: 行号。
            path: 引用路径字符串。
            ref_type: 引用类型（"图片" 或 "链接"）。
            report: 报告对象。
        """
        # 检查是否为URL（允许外部链接）
        if path.startswith(("http://", "https://", "ftp://")):
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.PASS,
                    f"{ref_type}引用外部URL: {path}",
                )
            )
            return

        # 检查是否为锚点引用
        if path.startswith("#"):
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.PASS,
                    f"{ref_type}引用锚点: {path}",
                )
            )
            return

        # 检查是否为邮件链接
        if path.startswith("mailto:"):
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.PASS,
                    f"{ref_type}引用邮件: {path}",
                )
            )
            return

        # 检查路径是否为空
        if not path.strip():
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.FAIL,
                    f"{ref_type}引用路径为空",
                )
            )
            return

        # 检查路径中是否包含空格（可能导致链接断裂）
        if " " in path:
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.WARN,
                    f"{ref_type}引用路径包含空格: {path}",
                )
            )
            return

        # 检查文件扩展名是否合法
        ext = os.path.splitext(path)[1].lower()
        all_valid_ext = self.VALID_IMAGE_EXTENSIONS | self.VALID_ASSET_EXTENSIONS
        if ext and ext not in all_valid_ext:
            report.add_result(
                self.report(
                    file_path, self.TYPE, line_number, CheckStatus.WARN,
                    f"{ref_type}引用非常见文件类型: {path} (扩展名: {ext})",
                )
            )
            return

        # 路径检查通过
        report.add_result(
            self.report(
                file_path, self.TYPE, line_number, CheckStatus.PASS,
                f"{ref_type}引用路径格式正确: {path}",
            )
        )


# ============================================================
# 综合检查器
# ============================================================

class MarkdownFormatChecker:
    """Markdown格式综合检查器。

    按顺序执行所有注册的检查器，并汇总检查报告。
    """

    def __init__(self, fix_mode: bool = False) -> None:
        """初始化综合检查器。

        Args:
            fix_mode: 是否启用自动修复模式。
        """
        self.fix_mode = fix_mode
        self.checkers: List[BaseChecker] = [
            TableAlignmentChecker(fix_mode),
            IndentationChecker(fix_mode),
            FrontMatterChecker(fix_mode),
            AssetReferenceChecker(fix_mode),
        ]

    def scan_md_files(self, directory: str) -> List[str]:
        """扫描目录下所有 .md 文件。

        Args:
            directory: 要扫描的目录路径。

        Returns:
            .md文件路径的排序列表。
        """
        pattern = os.path.join(directory, "**", "*.md")
        files = sorted(glob.glob(pattern, recursive=True))
        logging.info("在 %s 下找到 %d 个 .md 文件", directory, len(files))
        return files

    def check_file(self, file_path: str) -> FileReport:
        """对单个文件执行所有检查。

        Args:
            file_path: 文件路径。

        Returns:
            该文件的检查报告。
        """
        report = FileReport(file_path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            report.add_result(
                CheckResult(
                    file_path=file_path,
                    check_type="文件读取",
                    line_number=0,
                    status=CheckStatus.FAIL,
                    message=f"无法读取文件: {e}",
                )
            )
            return report

        for checker in self.checkers:
            try:
                checker.check(file_path, lines, report)
            except Exception as e:
                report.add_result(
                    CheckResult(
                        file_path=file_path,
                        check_type=checker.TYPE,
                        line_number=0,
                        status=CheckStatus.FAIL,
                        message=f"检查过程异常: {e}",
                    )
                )

        # 应用修复（如果启用了fix模式）
        if self.fix_mode:
            self._apply_fixes(file_path, lines)

        return report

    def _apply_fixes(self, file_path: str, lines: List[str]) -> None:
        """应用所有检查器的修复到文件。

        Args:
            file_path: 文件路径。
            lines: 文件原始行内容。
        """
        modified_lines = list(lines)

        for checker in self.checkers:
            if hasattr(checker, "apply_fix"):
                modified_lines = checker.apply_fix(file_path, modified_lines)

        # 检查是否有实际修改
        if modified_lines != lines:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(modified_lines)
                logging.info("已自动修复文件: %s", file_path)
            except Exception as e:
                logging.error("写入修复失败 %s: %s", file_path, e)

    def run_checks(self, directory: str) -> List[FileReport]:
        """对指定目录下所有 .md 文件执行检查。

        Args:
            directory: 要检查的目录路径。

        Returns:
            所有文件的检查报告列表。
        """
        files = self.scan_md_files(directory)
        reports: List[FileReport] = []

        for file_path in files:
            logging.info("正在检查: %s", file_path)
            report = self.check_file(file_path)
            reports.append(report)

        return reports

    def print_summary(self, reports: List[FileReport]) -> None:
        """打印检查汇总报告。

        Args:
            reports: 所有文件的检查报告列表。
        """
        total_pass = 0
        total_fail = 0
        total_warn = 0
        total_fixed = 0
        files_with_issues = 0

        print("\n" + "=" * 70)
        print("  Markdown 格式检查报告")
        print("=" * 70)

        for report in reports:
            rel_path = os.path.relpath(report.file_path)
            tp = report.pass_count
            tf = report.fail_count
            tw = report.warn_count
            tfx = report.fixed_count
            total_pass += tp
            total_fail += tf
            total_warn += tw
            total_fixed += tfx

            status_icon = "  OK" if not report.has_issues else "  !! "
            print(f"\n{status_icon} | {rel_path}")
            print(f"    └─ 通过: {tp} | 失败: {tf} | 警告: {tw} | 已修复: {tfx}")

            if report.has_issues:
                files_with_issues += 1
                for r in report.results:
                    if r.status in (CheckStatus.FAIL, CheckStatus.WARN):
                        line_info = f"第{r.line_number}行" if r.line_number > 0 else "全局"
                        print(f"       [{r.status.value}] [{r.check_type}] {line_info}: {r.message}")

        print("\n" + "-" * 70)
        print(f"  总计: {len(reports)} 个文件 | "
              f"通过: {total_pass} | "
              f"失败: {total_fail} | "
              f"警告: {total_warn} | "
              f"已修复: {total_fixed}")
        if files_with_issues > 0:
            print(f"  存在问题的文件: {files_with_issues} 个")
        print("=" * 70)


# ============================================================
# 命令行入口
# ============================================================

def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    Returns:
        解析后的命名空间对象。
    """
    parser = argparse.ArgumentParser(
        description="MD格式、表格规范校验工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python format_check.py --dir ./skills_md
  python format_check.py --dir ./skills_md --fix
  python format_check.py --dir ./output
  python format_check.py --dir ./docs --verbose
        """,
    )

    parser.add_argument(
        "--dir",
        type=str,
        default=".",
        help="指定要检查的目录（默认: 当前目录）",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="自动修复常见格式问题",
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


def main() -> None:
    """主函数：解析参数、执行检查流程。"""
    args = parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        logging.getLogger().addHandler(file_handler)

    logging.info("=" * 60)
    logging.info("format_check.py 启动")
    logging.info("=" * 60)

    # 解析目录
    target_dir = os.path.abspath(args.dir)
    if not os.path.isdir(target_dir):
        logging.error("指定目录不存在: %s", target_dir)
        sys.exit(1)

    logging.info("检查目录: %s", target_dir)
    logging.info("修复模式: %s", "开启" if args.fix else "关闭")

    # 执行检查
    checker = MarkdownFormatChecker(fix_mode=args.fix)
    try:
        reports = checker.run_checks(target_dir)
    except Exception as e:
        logging.error("检查过程中发生异常: %s", e)
        sys.exit(1)

    # 输出报告
    checker.print_summary(reports)

    # 汇总
    total_files = len(reports)
    problematic_files = sum(1 for r in reports if r.has_issues)

    if problematic_files == 0:
        logging.info("所有 %d 个文件检查通过，未发现问题。", total_files)
    else:
        if args.fix:
            logging.info(
                "检查完成: %d 个文件中有 %d 个存在问题（已尝试自动修复）",
                total_files,
                problematic_files,
            )
        else:
            logging.info(
                "检查完成: %d 个文件中有 %d 个存在问题（使用 --fix 可尝试自动修复）",
                total_files,
                problematic_files,
            )


if __name__ == "__main__":
    main()
