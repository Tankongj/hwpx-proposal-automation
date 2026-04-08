#!/usr/bin/env python3
"""
write_hwpx.py — Inject data into HWPX templates via ZIP-level replacement.

Two replacement modes:
  - Batch: Replace all occurrences of a string with another
  - Sequential: Replace the same placeholder with different values in order

Usage:
    python write_hwpx.py --template input.hwpx --output output.hwpx --data-json data.json

Python API:
    from write_hwpx import zip_replace, zip_replace_sequential
"""

import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path


def zip_replace(src_path: str, dst_path: str, replacements: dict) -> None:
    """
    ZIP-level batch replacement.
    Replaces all occurrences of each key with its value across all XML files.

    Args:
        src_path: Source HWPX file path
        dst_path: Output HWPX file path (can be same as src)
        replacements: {"old text": "new text", ...}
    """
    src = Path(src_path)
    tmp = Path(tempfile.mktemp(suffix='.hwpx'))

    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename.endswith('.xml') or item.filename.endswith('.rels'):
                text = data.decode('utf-8')
                for old, new in replacements.items():
                    text = text.replace(old, new)
                data = text.encode('utf-8')

            zout.writestr(item, data)

    shutil.move(str(tmp), dst_path)


def zip_replace_sequential(src_path: str, dst_path: str, placeholder: str, values: list) -> None:
    """
    ZIP-level sequential replacement.
    Replaces the same placeholder with different values in order of appearance.

    Args:
        src_path: Source HWPX file path
        dst_path: Output HWPX file path
        placeholder: The repeated placeholder text
        values: List of replacement values in order
    """
    src = Path(src_path)
    tmp = Path(tempfile.mktemp(suffix='.hwpx'))
    value_iter = iter(values)

    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename.endswith('.xml') or item.filename.endswith('.rels'):
                text = data.decode('utf-8')

                result_parts = []
                remaining = text
                while placeholder in remaining:
                    idx = remaining.index(placeholder)
                    result_parts.append(remaining[:idx])
                    try:
                        replacement = next(value_iter)
                    except StopIteration:
                        replacement = placeholder  # Keep original if values exhausted
                    result_parts.append(replacement)
                    remaining = remaining[idx + len(placeholder):]
                result_parts.append(remaining)
                text = ''.join(result_parts)
                data = text.encode('utf-8')

            zout.writestr(item, data)

    shutil.move(str(tmp), dst_path)


def write_hwpx_from_json(template_path: str, output_path: str, data_path: str) -> None:
    """
    Fill an HWPX template using a JSON data file.

    JSON structure:
    {
        "replace": {"old text": "new text", ...},
        "replace_sequential": [
            {"placeholder": "repeated text", "values": ["val1", "val2", ...]}
        ]
    }
    """
    data = json.loads(Path(data_path).read_text(encoding='utf-8'))
    output = Path(output_path)

    # Step 1: Copy template
    shutil.copy(template_path, output_path)
    print(f"📋 Template copied: {template_path} → {output_path}")

    # Step 2: Batch replacement
    if 'replace' in data and data['replace']:
        zip_replace(str(output), str(output), data['replace'])
        print(f"✅ Batch replacement done: {len(data['replace'])} items")

    # Step 3: Sequential replacement
    if 'replace_sequential' in data:
        for item in data['replace_sequential']:
            placeholder = item['placeholder']
            values = item['values']
            zip_replace_sequential(str(output), str(output), placeholder, values)
            print(f"✅ Sequential replacement done: '{placeholder[:20]}...' → {len(values)} items")

    print(f"\n🎉 HWPX generated: {output}")
    print(f"⚠️  Run fix_namespaces.py next!")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Inject data into HWPX template')
    parser.add_argument('--template', required=True, help='HWPX template file path')
    parser.add_argument('--output', required=True, help='Output HWPX file path')
    parser.add_argument('--data-json', required=True, help='Data JSON file path')

    args = parser.parse_args()
    write_hwpx_from_json(args.template, args.output, args.data_json)
