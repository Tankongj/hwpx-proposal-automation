#!/usr/bin/env python3
"""
fix_namespaces.py — HWPX namespace post-processor (v2).

Fixes XML namespace corruption that occurs after lxml serialization or
ZIP-level text replacement. Without this step, Hancom Office displays
blank pages.

Features (v2):
  - lxml ns0:/ns1: prefix removal (regex)
  - XML entity double-escaping fix
  - XML declaration restoration
  - Table page-break fix (--fix-tables):  treatAsChar, horzRelTo, vertsize
  - Table Fixer integration (hwpx_editor.table_fixer)

Usage:
    python fix_namespaces.py output.hwpx
    python fix_namespaces.py output.hwpx --fix-tables
"""

import sys
import re
import zipfile
import shutil
import tempfile
import argparse
from pathlib import Path


def fix_xml_declaration(content: str) -> str:
    """Restore XML declaration if missing or corrupted."""
    if not content.strip().startswith('<?xml'):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    return content


def fix_namespace_prefixes(content: str) -> str:
    """Remove lxml-generated ns0:/ns1: namespace prefixes.

    lxml's etree.tostring() adds ns0:, ns1: etc. prefixes that
    Hancom Office cannot parse, causing blank pages.
    See: docs/knowhow/namespace-corruption.md
    """
    # Remove opening tag prefixes: <ns0:p ...> → <p ...>
    content = re.sub(r'<ns\d+:', '<', content)
    # Remove closing tag prefixes: </ns0:p> → </p>
    content = re.sub(r'</ns\d+:', '</', content)
    # Remove attribute prefixes: ns0:paraPrIDRef → paraPrIDRef
    content = re.sub(r'\bns\d+:', '', content)
    # Remove xmlns:ns0="..." declarations
    content = re.sub(r'\s+xmlns:ns\d+="[^"]*"', '', content)
    return content


def fix_entity_corruption(content: str) -> str:
    """Fix double-escaped XML entities."""
    content = content.replace('&amp;amp;', '&amp;')
    content = content.replace('&amp;lt;', '&lt;')
    content = content.replace('&amp;gt;', '&gt;')
    content = content.replace('&amp;quot;', '&quot;')
    content = content.replace('&amp;apos;', '&apos;')
    return content


def fix_table_pagebreak(content: str) -> str:
    """Fix table page-breaking by modifying pos.treatAsChar and related attrs.

    Three conditions must be met for table page-breaking:
    1. tbl textWrap="SQUARE"
    2. tbl pageBreak="TABLE"
    3. pos treatAsChar="0"  ← Most critical!

    See: docs/knowhow/com-api-pitfalls.md, docs/table-pagebreak.md
    """
    # pos.treatAsChar → 0
    content = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', content)
    # horzRelTo="COLUMN" → "PARA" (normal pattern)
    content = re.sub(r'horzRelTo="COLUMN"', 'horzRelTo="PARA"', content)
    # linesegarray large vertsize → 1200 (let Hancom recalculate)
    content = re.sub(r'vertsize="(\d{5,})"', 'vertsize="1200"', content)
    return content


def fix_hwpx_namespaces(hwpx_path: str, fix_tables: bool = False) -> None:
    """Post-process HWPX file to fix XML namespaces and optionally tables."""
    src = Path(hwpx_path)
    if not src.exists():
        print(f"Error: File not found: {src}")
        sys.exit(1)

    tmp = Path(tempfile.mktemp(suffix='.hwpx'))
    fixed_count = 0
    ns_fixed = False
    tables_fixed = False

    # Attempt to import the Table Fixer module
    try:
        from hwpx_editor.table_fixer import fix_all_tables
    except ImportError:
        try:
            from scripts.hwpx_editor.table_fixer import fix_all_tables
        except ImportError:
            fix_all_tables = None

    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename.endswith('.xml'):
                text = data.decode('utf-8')
                original = text

                text = fix_xml_declaration(text)
                text = fix_namespace_prefixes(text)
                text = fix_entity_corruption(text)

                # Check if ns prefixes were present
                if text != original:
                    ns_fixed = True

                # Apply table fixes to section XMLs
                if item.filename.startswith('Contents/section'):
                    if fix_tables:
                        text = fix_table_pagebreak(text)

                    if fix_all_tables:
                        fixed_text = fix_all_tables(text)
                        if fixed_text != text:
                            text = fixed_text
                            tables_fixed = True

                if text != original:
                    fixed_count += 1

                data = text.encode('utf-8')

            zout.writestr(item, data)

    shutil.move(str(tmp), hwpx_path)

    print(f"[OK] Namespace fix complete: {hwpx_path} ({fixed_count} XML files modified)")
    if ns_fixed:
        print(f"[OK] Namespace prefixes (ns0:/ns1:) removed.")
    if fix_tables:
        print(f"[OK] Table page-break fix applied (treatAsChar=0, vertsize reset).")
    if tables_fixed:
        print(f"[OK] Table Fixer (colSpan/pagination) applied.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fix HWPX XML namespaces after text replacement or lxml serialization',
        epilog='See docs/knowhow/namespace-corruption.md for technical details.'
    )
    parser.add_argument('hwpx_file', help='HWPX file to fix (modified in-place)')
    parser.add_argument('--fix-tables', action='store_true',
                        help='Also fix table page-breaking (treatAsChar=0)')

    args = parser.parse_args()
    fix_hwpx_namespaces(args.hwpx_file, fix_tables=args.fix_tables)
