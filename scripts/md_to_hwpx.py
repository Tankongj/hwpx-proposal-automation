#!/usr/bin/env python3
"""
md_to_hwpx.py — Convert structured Markdown into HWPX format.

Reads a markdown file with Korean government proposal conventions (□○―※ symbols)
and injects it into an HWPX template, preserving the template's cover page and styles.

The style mapping (charPrIDRef, paraPrIDRef) must match your template's header.xml.
Customize STYLE_MAP and INDENT constants for your specific template.

Usage:
    python md_to_hwpx.py --template form.hwpx --md content.md --output result.hwpx

After running, execute fix_namespaces.py on the output:
    python fix_namespaces.py result.hwpx
"""

import argparse
import zipfile
import os
import re
from copy import deepcopy
from lxml import etree

NS_HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'

# ============================================================
# Style configuration — CUSTOMIZE THESE FOR YOUR TEMPLATE
# ============================================================
# Each style maps to paraPrIDRef and charPrIDRef values from your template's header.xml.
# Use analyze_template.py to inspect your template and find the correct values.

STYLE_MAP = {
    'chapter_title': {'para': '8', 'char': '63'},   # Chapter title (e.g., Ⅰ, Ⅱ)
    'section_title': {'para': '8', 'char': '64'},   # Section title (e.g., 1., 2.)
    'subsection':    {'para': '8', 'char': '64'},   # Subsection
    'square':        {'para': '8', 'char': '52'},   # □ Level 0 (major topic, bold)
    'circle':        {'para': '8', 'char': '65'},   # ○ Level 1 (sub topic)
    'dash':          {'para': '8', 'char': '65'},   # ― Level 2 (detail)
    'note':          {'para': '8', 'char': '66'},   # ※ Level 3 (reference/footnote)
    'body':          {'para': '8', 'char': '65'},   # General body text
    'table_header':  {'para': '8', 'char': '52'},   # Table header row
    'table_cell':    {'para': '8', 'char': '65'},   # Table data cell
    'empty':         {'para': '8', 'char': '65'},   # Empty line
}

# Indentation per style (spaces prepended to text)
INDENT = {
    'chapter_title': '',
    'section_title': '',
    'subsection':    '',
    'square':        '',           # □ L0: no indent
    'circle':        '  ',         # ○ L1: 2 spaces
    'dash':          '    ',       # ― L2: 4 spaces
    'note':          '    ',       # ※ L3: 4 spaces
    'body':          '  ',         # Body: 2 spaces
    'table_header':  '  ',
    'table_cell':    '    ',
}

# Cover page keywords — paragraphs containing these are preserved from template.
# Customize for your specific template's cover page text.
COVER_KEYWORDS = []  # e.g., ['사업수행 제안서', '2026년', '용역']


def create_paragraph(text, para_ref, char_ref, style_ref="0"):
    """Create an HWPX paragraph element (<hp:p>) with text."""
    p = etree.Element('{%s}p' % NS_HP)
    p.set('paraPrIDRef', str(para_ref))
    p.set('styleIDRef', str(style_ref))
    p.set('pageBreak', '0')
    p.set('columnBreak', '0')
    p.set('merged', '0')

    run = etree.SubElement(p, '{%s}run' % NS_HP)
    run.set('charPrIDRef', str(char_ref))
    t = etree.SubElement(run, '{%s}t' % NS_HP)
    t.text = text

    lsa = etree.SubElement(p, '{%s}linesegarray' % NS_HP)
    ls = etree.SubElement(lsa, '{%s}lineseg' % NS_HP)
    for k, v in [('textStartPos', '0'), ('lineHeight', '1000'),
                 ('textHeight', '1000'), ('baseLineGap', '850'),
                 ('spacing', '600'), ('horzpos', '0'),
                 ('horzsize', '42520'), ('vertpos', '0'), ('vertsize', '1000')]:
        ls.set(k, v)
    return p


def make_para(text, style_key):
    """Create a paragraph with style-based indentation and formatting."""
    s = STYLE_MAP.get(style_key, STYLE_MAP['body'])
    indent = INDENT.get(style_key, '')
    return create_paragraph(indent + text, s['para'], s['char'])


def make_empty():
    """Create an empty paragraph (blank line)."""
    s = STYLE_MAP['empty']
    return create_paragraph(' ', s['para'], s['char'])


def table_to_list(headers, rows):
    """Convert a markdown table into list format (○/― style) for HWPX compatibility.
    
    Native HWPX tables require complex hp:subList structures.
    Converting to list format is safer and more reliable.
    """
    paragraphs = []
    for row in rows:
        first_cell = row[0] if len(row) > 0 else ''
        if first_cell:
            details = []
            for ci in range(1, len(headers)):
                if ci < len(row) and row[ci]:
                    details.append(f'{headers[ci]}: {row[ci]}')
            if details:
                line = f'○ {first_cell} — {", ".join(details)}'
            else:
                line = f'○ {first_cell}'
            paragraphs.append(make_para(line, 'circle'))
    return paragraphs


def classify_and_convert(line):
    """Classify a markdown line into a style category and extract text."""
    stripped = line.strip()
    if not stripped:
        return None, None
    if stripped.startswith('---') or stripped.startswith('> ') or stripped.startswith('```'):
        return None, None
    if stripped.startswith('# ') and not stripped.startswith('## '):
        return 'chapter_title', stripped[2:].strip()
    if stripped.startswith('## ') and not stripped.startswith('### '):
        return 'section_title', stripped[3:].strip()
    if stripped.startswith('### '):
        return 'subsection', stripped[4:].strip()
    if stripped.startswith('|') and stripped.endswith('|'):
        return 'table_line', stripped

    # Remove markdown bold markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)

    # Classify by Korean proposal symbol hierarchy
    if text.startswith('□'):
        return 'square', text
    if text.startswith('○'):
        return 'circle', text
    if text.startswith('―') or text.startswith('  ―'):
        return 'dash', text.lstrip()
    if text.startswith('※'):
        return 'note', text
    return 'body', text


def parse_markdown(md_content):
    """Parse markdown content into HWPX paragraph elements."""
    paragraphs = []
    stats = {}
    lines = md_content.split('\n')
    i = 0
    prev_style = None

    while i < len(lines):
        style_key, text = classify_and_convert(lines[i])

        if style_key is None:
            i += 1
            continue

        # Insert blank lines before chapter titles
        if style_key == 'chapter_title' and prev_style is not None:
            paragraphs.append(make_empty())
            paragraphs.append(make_empty())

        # Insert blank line before section titles
        if style_key == 'section_title' and prev_style is not None:
            paragraphs.append(make_empty())

        # Handle table blocks
        if style_key == 'table_line':
            table_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('|') and s.endswith('|'):
                    table_lines.append(s)
                    i += 1
                else:
                    break

            if len(table_lines) >= 2:
                headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                rows = []
                for tl in table_lines[1:]:
                    if re.match(r'^\|[\s\-|:]+\|$', tl):
                        continue
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    rows.append(cells)

                if headers and rows:
                    tbl_paras = table_to_list(headers, rows)
                    paragraphs.extend(tbl_paras)
                    stats['table'] = stats.get('table', 0) + 1
            prev_style = 'table'
            continue

        # Regular paragraph
        p = make_para(text, style_key)
        paragraphs.append(p)
        stats[style_key] = stats.get(style_key, 0) + 1
        prev_style = style_key
        i += 1

    return paragraphs, stats


def main():
    parser = argparse.ArgumentParser(
        description='Convert structured Markdown to HWPX format',
        epilog='After conversion, run fix_namespaces.py on the output file.'
    )
    parser.add_argument('--template', required=True, help='HWPX template file')
    parser.add_argument('--md', required=True, help='Markdown content file')
    parser.add_argument('--output', required=True, help='Output HWPX file')
    parser.add_argument('--cover-keywords', nargs='*', default=COVER_KEYWORDS,
                        help='Keywords to identify cover page paragraphs (preserved from template)')
    args = parser.parse_args()

    print(f'📄 Template: {args.template}')
    print(f'📝 Markdown: {args.md}')
    print(f'📦 Output: {args.output}')

    with open(args.md, 'r', encoding='utf-8') as f:
        md_content = f.read()

    with zipfile.ZipFile(args.template, 'r') as z:
        section_xml = z.read('Contents/section0.xml')
        all_files = {name: z.read(name) for name in z.namelist()}

    section_tree = etree.fromstring(section_xml)
    existing_paras = section_tree.findall('.//{%s}p' % NS_HP)

    # Preserve cover page paragraphs (matching keywords)
    cover_paras = []
    if args.cover_keywords:
        for p in existing_paras:
            texts = []
            for t in p.iter('{%s}t' % NS_HP):
                if t.text:
                    texts.append(t.text)
            full = ''.join(texts).strip()
            if any(kw in full for kw in args.cover_keywords):
                cover_paras.append(deepcopy(p))

    # Parse markdown content
    new_paragraphs, stats = parse_markdown(md_content)

    print(f'\n📊 Generation stats:')
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'     {k:18s}: {v:3d}')
    print(f'     {"Total":18s}: {len(new_paragraphs):3d}')

    # Remove existing paragraphs and inject new content
    for p in existing_paras:
        p.getparent().remove(p)

    sec = section_tree
    for cp in cover_paras:
        sec.append(cp)
    sec.append(make_empty())
    for p in new_paragraphs:
        sec.append(p)

    new_section = etree.tostring(section_tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in all_files.items():
            if name == 'Contents/section0.xml':
                zout.writestr(name, new_section)
            else:
                zout.writestr(name, data)

    print(f'\n✅ Done: {args.output}')
    print(f'   Cover: {len(cover_paras)} paras + Content: {len(new_paragraphs)} paras (tables: {stats.get("table", 0)})')
    print(f'\n⚠️  Run fix_namespaces.py next!')


if __name__ == '__main__':
    main()
