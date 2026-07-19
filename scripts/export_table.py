#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_table.py — 批量导出成品表格文件的工具

功能说明：
    - 从 skills_md/ 下的Prompt文件中提取表格内容
    - 支持导出格式：CSV、Markdown、JSON
    - 支持 --format 参数选择输出格式
    - 支持 --output-dir 指定输出目录
    - 包含详细的日志输出

运行环境：Windows PowerShell + Python 3（仅使用标准库，无外部依赖）
"""

import argparse
import csv
import glob
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


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
# 数据模型
# ============================================================

@dataclass
class TableCell:
    """表格单元格。

    Attributes:
        content: 单元格内容。
        alignment: 对齐方式（左/中/右/无）。
    """
    content: str
    alignment: str = "left"


@dataclass
class ExtractedTable:
    """从Markdown中提取的完整表格。

    Attributes:
        source_file: 来源文件路径。
        headers: 表头列表。
        rows: 数据行列表（每行为单元格列表）。
        alignments: 各列对齐方式（left/center/right/None）。
        position: 在原文中的起始行号。
    """
    source_file: str
    headers: List[str]
    rows: List[List[str]]
    alignments: List[Optional[str]] = field(default_factory=list)
    position: int = 0

    @property
    def row_count(self) -> int:
        """数据行数。"""
        return len(self.rows)

    @property
    def col_count(self) -> int:
        """列数。"""
        return len(self.headers)


# ============================================================
# Markdown 表格解析器
# ============================================================

class MarkdownTableParser:
    """Markdown表格解析器，从 .md 文件中提取所有表格。"""

    # Markdown表格的正则表达式
    # 匹配包含表头行、分隔行和数据行的完整表格
    TABLE_PATTERN = re.compile(
        r'^\|(.+)\|\s*$'        # 表头行
        r'\n'                    # 换行
        r'^\|([\s\-:|]+)\|\s*$'  # 分隔行
        r'(\n^\|.+\\|\s*$)*',    # 数据行（0行或多行）
        re.MULTILINE,
    )

    def __init__(self) -> None:
        self._extracted_tables: List[ExtractedTable] = []

    def extract_from_file(self, file_path: str) -> List[ExtractedTable]:
        """从单个 .md 文件中提取所有表格。

        Args:
            file_path: .md 文件的绝对路径。

        Returns:
            提取的表格列表。
        """
        if not os.path.isfile(file_path):
            logging.error("文件不存在: %s", file_path)
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.error("读取文件失败 %s: %s", file_path, e)
            return []

        tables = self._parse_tables(content, file_path)
        self._extracted_tables.extend(tables)

        filename = os.path.basename(file_path)
        if tables:
            logging.info("从 %s 中提取了 %d 个表格", filename, len(tables))
        else:
            logging.debug("文件 %s 中未找到表格", filename)

        return tables

    def _parse_tables(self, content: str, source_file: str) -> List[ExtractedTable]:
        """从文本内容中解析出所有表格。

        Args:
            content: Markdown内容的字符串。
            source_file: 来源文件路径。

        Returns:
            解析出的表格列表。
        """
        tables: List[ExtractedTable] = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检测表头行：以 | 开头且不全是 ---
            if line.startswith("|") and not self._is_separator_line(line):
                # 检查下一行是否为分隔行
                if i + 1 < len(lines) and self._is_separator_line(lines[i + 1].strip()):
                    table = self._parse_table_at(lines, i, source_file)
                    if table:
                        tables.append(table)
                    # 跳过已解析的行
                    i += table.row_count + 2 if table else 2
                    continue

            i += 1

        return tables

    @staticmethod
    def _is_separator_line(line: str) -> bool:
        """判断一行是否为表格分隔行。

        分隔行格式：| --- | :--- | :---: | ---: |

        Args:
            line: 要判断的行字符串。

        Returns:
            如果是分隔行返回 True。
        """
        stripped = line.strip()
        if not stripped.startswith("|"):
            return False
        # 去除首尾 | 后，检查是否只包含 -, :, 空格, |
        inner = stripped.strip("|")
        return bool(re.match(r'^[\s\-:|]+$', inner))

    @staticmethod
    def _parse_alignment(sep_line: str) -> List[Optional[str]]:
        """解析分隔行中各列的对齐方式。

        Args:
            sep_line: 分隔行字符串。

        Returns:
            每列对齐方式列表（"left"/"center"/"right"/None）。
        """
        alignments: List[Optional[str]] = []
        # 按 | 分割
        cells = sep_line.split("|")
        for cell in cells:
            cell = cell.strip()
            if not cell:
                continue
            if cell.startswith(":") and cell.endswith(":"):
                alignments.append("center")
            elif cell.endswith(":"):
                alignments.append("right")
            elif cell.startswith(":"):
                alignments.append("left")
            else:
                alignments.append(None)
        return alignments

    def _parse_table_at(
        self,
        lines: List[str],
        start_idx: int,
        source_file: str,
    ) -> Optional[ExtractedTable]:
        """从指定位置解析一个完整的表格。

        Args:
            lines: 文件的所有行。
            start_idx: 表头行的索引（0-based）。
            source_file: 来源文件路径。

        Returns:
            解析出的表格对象，如果解析失败返回 None。
        """
        try:
            # 解析表头
            header_line = lines[start_idx].strip()
            headers = self._split_row(header_line)
            if not headers:
                return None

            # 解析分隔行获取对齐方式
            sep_line = lines[start_idx + 1].strip()
            alignments = self._parse_alignment(sep_line)

            # 确保对齐方式列表长度与表头匹配
            if len(alignments) < len(headers):
                alignments.extend([None] * (len(headers) - len(alignments)))

            # 解析数据行
            rows: List[List[str]] = []
            row_idx = start_idx + 2
            while row_idx < len(lines):
                line = lines[row_idx].strip()
                if not line.startswith("|"):
                    break
                if self._is_separator_line(line):
                    break
                row = self._split_row(line)
                if row:
                    # 如果某行列数不足，补齐空字符串
                    while len(row) < len(headers):
                        row.append("")
                    rows.append(row)
                row_idx += 1

            return ExtractedTable(
                source_file=source_file,
                headers=headers,
                rows=rows,
                alignments=alignments,
                position=start_idx + 1,  # 转换为1-based行号
            )

        except Exception as e:
            logging.warning("解析表格失败（位置 %d）: %s", start_idx + 1, e)
            return None

    @staticmethod
    def _split_row(row_line: str) -> List[str]:
        """将一行表格按 | 分割为单元格列表，并去除首尾空格。

        Args:
            row_line: 表格行字符串。

        Returns:
            单元格内容列表。
        """
        # 去除首尾空白
        row_line = row_line.strip()
        # 去除首尾 |
        if row_line.startswith("|"):
            row_line = row_line[1:]
        if row_line.endswith("|"):
            row_line = row_line[:-1]

        cells = row_line.split("|")
        return [cell.strip() for cell in cells]


# ============================================================
# 导出器
# ============================================================

class BaseExporter:
    """导出器基类。"""

    def export(self, table: ExtractedTable, output_path: str) -> bool:
        """导出单个表格到文件。

        Args:
            table: 要导出的表格数据。
            output_path: 输出文件路径。

        Returns:
            导出成功返回 True。
        """
        raise NotImplementedError("子类必须实现 export 方法")

    def export_all(self, tables: List[ExtractedTable], output_dir: str) -> int:
        """批量导出表格到指定目录。

        Args:
            tables: 表格列表。
            output_dir: 输出目录。

        Returns:
            成功导出的文件数量。
        """
        success_count = 0
        for i, table in enumerate(tables):
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(table.source_file))[0]
            ext = self._file_extension()
            output_path = os.path.join(output_dir, f"{base_name}_table_{i + 1}{ext}")

            try:
                if self.export(table, output_path):
                    logging.info("已导出: %s", output_path)
                    success_count += 1
            except Exception as e:
                logging.error("导出失败 %s: %s", output_path, e)

        return success_count

    @staticmethod
    def _file_extension() -> str:
        """返回导出文件的扩展名（含点号）。

        Returns:
            文件扩展名。
        """
        return ".txt"


class CsvExporter(BaseExporter):
    """导出为CSV格式。"""

    @staticmethod
    def _file_extension() -> str:
        return ".csv"

    def export(self, table: ExtractedTable, output_path: str) -> bool:
        """将表格导出为CSV文件。

        Args:
            table: 表格数据。
            output_path: 输出路径。

        Returns:
            导出成功返回 True。
        """
        try:
            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                # 写入表头
                writer.writerow(table.headers)

                # 写入数据行
                for row in table.rows:
                    writer.writerow(row)

            return True
        except Exception as e:
            logging.error("CSV写入失败: %s", e)
            return False


class MarkdownExporter(BaseExporter):
    """导出为Markdown表格格式。"""

    @staticmethod
    def _file_extension() -> str:
        return ".md"

    def export(self, table: ExtractedTable, output_path: str) -> bool:
        """将表格导出为Markdown格式。

        Args:
            table: 表格数据。
            output_path: 输出路径。

        Returns:
            导出成功返回 True。
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # 写入文件头说明
                f.write(f"<!-- 来源: {table.source_file} -->\n")
                f.write(f"<!-- 位置: 第 {table.position} 行 -->\n\n")

                # 构建表头
                header_line = "| " + " | ".join(table.headers) + " |"
                f.write(header_line + "\n")

                # 构建分隔行
                sep_cells: List[str] = []
                for i, align in enumerate(table.alignments):
                    if i < len(table.headers):
                        if align == "center":
                            sep_cells.append(":---:")
                        elif align == "right":
                            sep_cells.append("---:")
                        elif align == "left":
                            sep_cells.append(":---")
                        else:
                            sep_cells.append("---")
                sep_line = "| " + " | ".join(sep_cells) + " |"
                f.write(sep_line + "\n")

                # 写入数据行
                for row in table.rows:
                    data_line = "| " + " | ".join(row) + " |"
                    f.write(data_line + "\n")

            return True
        except Exception as e:
            logging.error("Markdown写入失败: %s", e)
            return False


class JsonExporter(BaseExporter):
    """导出为JSON格式。"""

    @staticmethod
    def _file_extension() -> str:
        return ".json"

    def export(self, table: ExtractedTable, output_path: str) -> bool:
        """将表格导出为JSON格式。

        JSON结构：
            {
                "source_file": "...",
                "position": 1,
                "headers": ["col1", "col2"],
                "alignments": ["left", "center"],
                "row_count": 3,
                "col_count": 2,
                "rows": [
                    {"col1": "val1", "col2": "val2"},
                    ...
                ]
            }

        Args:
            table: 表格数据。
            output_path: 输出路径。

        Returns:
            导出成功返回 True。
        """
        try:
            # 构建行字典列表
            rows_dicts: List[Dict[str, str]] = []
            for row in table.rows:
                row_dict: Dict[str, str] = {}
                for i, header in enumerate(table.headers):
                    row_dict[header] = row[i] if i < len(row) else ""
                rows_dicts.append(row_dict)

            output: Dict[str, Any] = {
                "source_file": table.source_file,
                "position": table.position,
                "headers": table.headers,
                "alignments": table.alignments or [],
                "row_count": table.row_count,
                "col_count": table.col_count,
                "rows": rows_dicts,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logging.error("JSON写入失败: %s", e)
            return False


# ============================================================
# 导出器工厂
# ============================================================

class ExporterFactory:
    """导出器工厂，根据格式名称返回对应的导出器实例。"""

    EXPORTER_MAP: Dict[str, type] = {
        "csv": CsvExporter,
        "markdown": MarkdownExporter,
        "md": MarkdownExporter,
        "json": JsonExporter,
    }

    @classmethod
    def get_exporter(cls, format_name: str) -> Optional[BaseExporter]:
        """获取指定格式的导出器实例。

        Args:
            format_name: 格式名称（不区分大小写）。

        Returns:
            导出器实例；如果不支持该格式返回 None。
        """
        exporter_cls = cls.EXPORTER_MAP.get(format_name.lower())
        if exporter_cls is None:
            return None
        return exporter_cls()

    @classmethod
    def supported_formats(cls) -> List[str]:
        """获取支持的格式列表。

        Returns:
            支持的格式名称列表。
        """
        return list(cls.EXPORTER_MAP.keys())


# ============================================================
# 命令行入口
# ============================================================

def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    Returns:
        解析后的命名空间对象。
    """
    parser = argparse.ArgumentParser(
        description="批量导出成品表格文件的工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python export_table.py --format csv
  python export_table.py --format json --output-dir ./tables_json
  python export_table.py --format markdown
  python export_table.py --dir ./docs --format csv --verbose
        """,
    )

    parser.add_argument(
        "--dir",
        type=str,
        default=".",
        help="指定要搜索 .md 文件的目录（默认: 当前目录）",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="csv",
        choices=["csv", "markdown", "json"],
        help="导出格式（默认: csv）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="指定输出目录（默认: <当前目录>/exported_tables）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="输出详细日志（DEBUG级别）",
    )

    return parser.parse_args()


def main() -> None:
    """主函数：解析参数、提取表格、导出文件。"""
    args = parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logging.info("=" * 60)
    logging.info("export_table.py 启动")
    logging.info("=" * 60)

    # 解析搜索目录
    search_dir = os.path.abspath(args.dir)
    if not os.path.isdir(search_dir):
        logging.error("指定目录不存在: %s", search_dir)
        sys.exit(1)

    # 确定输出目录
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        output_dir = os.path.join(search_dir, "exported_tables")

    # 创建输出目录
    try:
        os.makedirs(output_dir, exist_ok=True)
        logging.info("输出目录: %s", output_dir)
    except Exception as e:
        logging.error("创建输出目录失败: %s", e)
        sys.exit(1)

    # 搜索 .md 文件
    pattern = os.path.join(search_dir, "**", "*.md")
    md_files = sorted(glob.glob(pattern, recursive=True))
    logging.info("在 %s 下找到 %d 个 .md 文件", search_dir, len(md_files))

    if not md_files:
        logging.warning("未找到任何 .md 文件，请检查目录路径")
        sys.exit(0)

    # 提取表格
    parser = MarkdownTableParser()
    all_tables: List[ExtractedTable] = []

    for file_path in md_files:
        tables = parser.extract_from_file(file_path)
        all_tables.extend(tables)

    logging.info("共提取 %d 个表格", len(all_tables))

    if not all_tables:
        logging.warning("未从任何 .md 文件中提取到表格，无需导出")
        sys.exit(0)

    # 获取导出器
    exporter = ExporterFactory.get_exporter(args.format)
    if exporter is None:
        logging.error(
            "不支持的导出格式: %s (支持: %s)",
            args.format,
            ", ".join(ExporterFactory.supported_formats()),
        )
        sys.exit(1)

    logging.info("导出格式: %s", args.format.upper())

    # 执行导出
    try:
        success_count = exporter.export_all(all_tables, output_dir)
    except Exception as e:
        logging.error("导出过程中发生异常: %s", e)
        sys.exit(1)

    # 输出汇总
    logging.info("=" * 60)
    logging.info(
        "导出完成: %d 个表格已导出为 %s 格式，共 %d 个文件",
        len(all_tables),
        args.format.upper(),
        success_count,
    )
    logging.info("输出目录: %s", output_dir)
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
