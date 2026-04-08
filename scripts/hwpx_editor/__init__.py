"""
HWPX Document Editor & Byte-Preserving Automation Module.

Provides raw XML byte-substitution APIs for Hancom Office HWPX files
without breaking their structural integrity or pagination capabilities.
"""

from .table_fixer import fix_all_tables, validate_all_tables
from .modify_hwpx import replace_text, insert_paragraph_after, update_section
from .read_hwpx import open_hwpx

__all__ = [
    "fix_all_tables",
    "validate_all_tables",
    "replace_text",
    "insert_paragraph_after",
    "update_section",
    "open_hwpx"
]
