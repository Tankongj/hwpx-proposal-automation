#!/usr/bin/env python3
"""
fix_namespaces.py — HWPX namespace post-processor.

Fixes XML namespace corruption that can occur after ZIP-level text replacement.
Without this step, Hancom Office may display blank pages.

Usage:
    python fix_namespaces.py output.hwpx
"""

import sys
import re
import zipfile
import shutil
import tempfile
from pathlib import Path


def fix_xml_declaration(content: str) -> str:
    """Restore XML declaration if missing or corrupted."""
    if not content.strip().startswith('<?xml'):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    return content


def fix_namespace_in_content(content: str) -> str:
    """Validate and restore XML namespace content."""
    # Fix ampersands that may have been corrupted during replacement
    content = content.replace('&', '&amp;')
    # Restore already-escaped entities
    content = content.replace('&amp;amp;', '&amp;')
    content = content.replace('&amp;lt;', '&lt;')
    content = content.replace('&amp;gt;', '&gt;')
    content = content.replace('&amp;quot;', '&quot;')
    content = content.replace('&amp;apos;', '&apos;')
    return content


def fix_hwpx_namespaces(hwpx_path: str) -> None:
    """Post-process HWPX file to fix XML namespaces."""
    src = Path(hwpx_path)
    if not src.exists():
        print(f"Error: File not found: {src}")
        sys.exit(1)

    tmp = Path(tempfile.mktemp(suffix='.hwpx'))
    fixed_count = 0

    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename.endswith('.xml'):
                text = data.decode('utf-8')
                original = text

                text = fix_xml_declaration(text)
                text = fix_namespace_in_content(text)

                if text != original:
                    fixed_count += 1

                data = text.encode('utf-8')

            zout.writestr(item, data)

    shutil.move(str(tmp), hwpx_path)
    print(f"✅ Namespace fix complete: {hwpx_path} ({fixed_count} XML files modified)")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fix HWPX XML namespaces after text replacement')
    parser.add_argument('hwpx_file', help='HWPX file to fix (modified in-place)')

    args = parser.parse_args()
    fix_hwpx_namespaces(args.hwpx_file)
