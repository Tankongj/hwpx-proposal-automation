#!/usr/bin/env python3
"""
enhance_hwpx.py — Insert images and tables into HWPX via Hancom COM API.

This is an OPTIONAL post-processing step for Windows + Hancom Office environments.
It opens the generated HWPX in Hancom Office, finds text anchors, and inserts
images/tables at those positions.

Requirements:
    - Windows 10/11
    - Hancom Office Hangul (licensed)
    - pip install pywin32

Usage:
    python enhance_hwpx.py --input result.hwpx --output enhanced.hwpx --inserts inserts.json

inserts.json format:
{
  "images": [
    {"anchor": "사업추진 조직 체계", "path": "slides/slide_06.png", "width_mm": 155}
  ],
  "tables": [
    {
      "anchor": "RFP 주요 KPI",
      "headers": ["성과지표", "목표치", "산출방법"],
      "rows": [["교육 수료 인원", "14,000명 이상", "교육 수료 인원"]]
    }
  ]
}

See docs/knowhow/com-api-pitfalls.md for known issues.
"""

import sys
import io
import os
import json
import time
import argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def insert_image_after_text(hwp, search_text: str, image_path: str, width_mm: int = 150):
    """Find text anchor and insert image on the next line.

    Args:
        hwp: Hancom COM object
        search_text: Text to search for (anchor)
        image_path: Path to image file (PNG/JPG)
        width_mm: Image width in millimeters (1mm = 283.46 HWP units)
    """
    if not os.path.exists(image_path):
        print(f'  ⚠️  Image not found: {image_path}')
        return False

    # Move to document start
    hwp.HAction.Run('MoveDocBegin')

    # Search for text
    # NOTE: FindWordByWord is NOT a valid attribute (raises AttributeError)
    # See docs/knowhow/com-api-pitfalls.md
    hwp.HAction.GetDefault('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)
    hwp.HParameterSet.HFindReplace.FindString = search_text
    hwp.HParameterSet.HFindReplace.FindRegExp = 0
    hwp.HParameterSet.HFindReplace.Direction = 0  # Forward

    found = hwp.HAction.Execute('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)

    if not found:
        print(f'  ⚠️  Text not found: "{search_text[:30]}..."')
        return False

    # Move to end of line and insert new paragraph
    hwp.HAction.Run('MoveLineEnd')
    hwp.HAction.Run('BreakPara')  # Enter

    # Insert image
    abs_path = os.path.abspath(image_path)

    hwp.HAction.GetDefault('InsertPicture', hwp.HParameterSet.HInsertPicture.HSet)
    hwp.HParameterSet.HInsertPicture.FileName = abs_path
    hwp.HParameterSet.HInsertPicture.Treatment = 0  # 자리차지
    hwp.HParameterSet.HInsertPicture.Width = int(width_mm * 283.46)
    hwp.HParameterSet.HInsertPicture.Height = 0  # auto (maintain aspect ratio)
    hwp.HParameterSet.HInsertPicture.SizeConstraint = 1  # width-based
    hwp.HAction.Execute('InsertPicture', hwp.HParameterSet.HInsertPicture.HSet)

    return True


def insert_table_after_text(hwp, search_text: str, headers: list, rows: list):
    """Find text anchor and insert a table with data on the next line.

    Args:
        hwp: Hancom COM object
        search_text: Text to search for (anchor)
        headers: Column header strings
        rows: List of row data (list of lists)
    """
    hwp.HAction.Run('MoveDocBegin')

    hwp.HAction.GetDefault('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)
    hwp.HParameterSet.HFindReplace.FindString = search_text
    hwp.HParameterSet.HFindReplace.FindRegExp = 0
    hwp.HParameterSet.HFindReplace.Direction = 0

    found = hwp.HAction.Execute('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)

    if not found:
        print(f'  ⚠️  Text not found: "{search_text[:30]}..."')
        return False

    hwp.HAction.Run('MoveLineEnd')
    hwp.HAction.Run('BreakPara')

    num_rows = len(rows) + 1  # +1 for header row
    num_cols = len(headers)

    hwp.HAction.GetDefault('InsertTable', hwp.HParameterSet.HTableCreation.HSet)
    hwp.HParameterSet.HTableCreation.Rows = num_rows
    hwp.HParameterSet.HTableCreation.Cols = num_cols
    hwp.HParameterSet.HTableCreation.WidthType = 2  # page-width
    hwp.HParameterSet.HTableCreation.HeightType = 0  # auto
    hwp.HAction.Execute('InsertTable', hwp.HParameterSet.HTableCreation.HSet)

    # Fill header row
    for i, header in enumerate(headers):
        hwp.HAction.GetDefault('InsertText', hwp.HParameterSet.HInsertText.HSet)
        hwp.HParameterSet.HInsertText.Text = header
        hwp.HAction.Execute('InsertText', hwp.HParameterSet.HInsertText.HSet)
        hwp.HAction.Run('CharShapeBold')
        if i < num_cols - 1:
            hwp.HAction.Run('TableRightCell')

    # Fill data rows
    for row in rows:
        hwp.HAction.Run('TableRightCell')
        for j, cell in enumerate(row):
            hwp.HAction.GetDefault('InsertText', hwp.HParameterSet.HInsertText.HSet)
            hwp.HParameterSet.HInsertText.Text = str(cell)
            hwp.HAction.Execute('InsertText', hwp.HParameterSet.HInsertText.HSet)
            if j < num_cols - 1:
                hwp.HAction.Run('TableRightCell')

    hwp.HAction.Run('CloseEx')
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Insert images and tables into HWPX via Hancom COM API (Windows only)',
        epilog='Requires: Windows + Hancom Office + pywin32. See docs/knowhow/com-api-pitfalls.md'
    )
    parser.add_argument('--input', required=True, help='Input HWPX file')
    parser.add_argument('--output', required=True, help='Output HWPX file')
    parser.add_argument('--inserts', required=True,
                        help='JSON file defining images/tables to insert')
    parser.add_argument('--visible', action='store_true', default=True,
                        help='Show Hancom window during processing (default: True)')
    parser.add_argument('--close', action='store_true',
                        help='Close Hancom after processing')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f'❌ Input file not found: {args.input}')
        sys.exit(1)

    if not os.path.exists(args.inserts):
        print(f'❌ Inserts file not found: {args.inserts}')
        sys.exit(1)

    with open(args.inserts, 'r', encoding='utf-8') as f:
        inserts = json.load(f)

    print(f'Input:   {args.input}')
    print(f'Output:  {args.output}')
    print(f'Inserts: {args.inserts}')

    # --- Open Hancom ---
    try:
        import win32com.client
    except ImportError:
        print('❌ pywin32 not installed. Run: pip install pywin32')
        sys.exit(1)

    print(f'\n[1/4] Opening Hangul...')
    hwp = win32com.client.gencache.EnsureDispatch('HWPFrame.HwpObject')
    hwp.XHwpWindows.Item(0).Visible = args.visible

    try:
        hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
    except Exception:
        pass

    print(f'[2/4] Opening HWPX: {os.path.basename(args.input)}')
    hwp.Open(os.path.abspath(args.input))
    time.sleep(1)

    # --- Insert visuals ---
    print(f'\n[3/4] Inserting visual elements...')

    images = inserts.get('images', [])
    tables = inserts.get('tables', [])

    base_dir = os.path.dirname(os.path.abspath(args.inserts))

    for item in images:
        anchor = item['anchor']
        img_path = item['path']
        if not os.path.isabs(img_path):
            img_path = os.path.join(base_dir, img_path)
        width = item.get('width_mm', 150)
        result = insert_image_after_text(hwp, anchor, img_path, width)
        status = '✅' if result else '⚠️ '
        print(f'  {status} Image: "{anchor[:30]}" → {os.path.basename(img_path)}')

    for item in tables:
        anchor = item['anchor']
        headers = item['headers']
        rows = item['rows']
        result = insert_table_after_text(hwp, anchor, headers, rows)
        status = '✅' if result else '⚠️ '
        print(f'  {status} Table: "{anchor[:30]}" ({len(rows)} rows)')

    # --- Save ---
    print(f'\n[4/4] Saving as: {os.path.basename(args.output)}')
    hwp.SaveAs(os.path.abspath(args.output))
    time.sleep(1)

    if args.close:
        hwp.Quit()
        print(f'\n✅ Done! Hancom closed.')
    else:
        print(f'\n✅ Done! Hancom window remains open for review.')

    print(f'   Output: {args.output}')


if __name__ == '__main__':
    main()
