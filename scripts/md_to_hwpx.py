#!/usr/bin/env python3
"""
md_to_hwpx.py — Convert structured Markdown into HWPX format (v2).

Reads a markdown file and injects it into an HWPX template, preserving styles.
Supports advanced features discovered through 53+ iteration cycles:

  - Style Remapper: safely merge styles from reference documents
  - Font Remapper: name-based font mapping across documents
  - Auto-bullet dedup: strip text prefixes that duplicate style bullets
  - linesegarray cache removal: prevent glyph corruption after deepcopy
  - secPr preservation: maintain template page setup during reference merge

Usage:
    # Basic conversion
    python md_to_hwpx.py --template form.hwpx --md content.md --output result.hwpx

    # With YAML style config
    python md_to_hwpx.py --template form.hwpx --md content.md --output result.hwpx \\
        --config style_config.yaml

    # With reference document for cover/TOC pages
    python md_to_hwpx.py --template form.hwpx --md content.md --output result.hwpx \\
        --reference ref.hwpx --cover-range 0:20 --toc-range 20:69

After running, execute fix_namespaces.py on the output:
    python fix_namespaces.py result.hwpx

See:
    docs/knowhow/style-remapper.md
    docs/knowhow/bullet-dedup.md
    docs/knowhow/namespace-corruption.md
    docs/style-system.md
"""

import argparse
import zipfile
import os
import re
import sys
import io
from copy import deepcopy
from pathlib import Path
from lxml import etree

# Force UTF-8 stdout on Windows
if sys.stdout and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NS_HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'

# ============================================================
# Default Style Configuration
# Override with --config YAML file for your template
# ============================================================
DEFAULT_STYLE_MAP = {
    'chapter_title': {'para': '3', 'char': '19', 'style': '0'},
    'section_title': {'para': '3', 'char': '18', 'style': '0'},
    'subsection':    {'para': '3', 'char': '18', 'style': '0'},
    'H3':            {'para': '8', 'char': '20', 'style': '7'},
    'H4':            {'para': '9', 'char': '21', 'style': '6'},
    'H5':            {'para': '10','char': '2',  'style': '0'},
    'square':        {'para': '8', 'char': '0',  'style': '0'},
    'circle':        {'para': '9', 'char': '21', 'style': '0'},
    'dash':          {'para': '13','char': '22', 'style': '0'},
    'L1':            {'para': '11','char': '2',  'style': '1'},
    'L2':            {'para': '13','char': '22', 'style': '3'},
    'note':          {'para': '15','char': '1',  'style': '0'},
    'body':          {'para': '11','char': '2',  'style': '0'},
    'empty':         {'para': '11','char': '2',  'style': '0'},
}


def load_config(config_path):
    """Load style configuration from YAML file."""
    if config_path is None:
        return DEFAULT_STYLE_MAP

    try:
        import yaml
    except ImportError:
        print("WARNING: PyYAML not installed. Using default styles. Install with: pip install PyYAML")
        return DEFAULT_STYLE_MAP

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    style_map = dict(DEFAULT_STYLE_MAP)  # Start with defaults
    if 'styles' in config:
        for key, vals in config['styles'].items():
            style_map[key] = {
                'para': str(vals.get('paraPrIDRef', '0')),
                'char': str(vals.get('charPrIDRef', '0')),
                'style': str(vals.get('styleIDRef', '0')),
            }
    return style_map


# ============================================================
# Paragraph Builders
# ============================================================

def create_paragraph(text, para_ref, char_ref, style_ref='0', page_break=False, ns_map=None):
    """Create an HWPX paragraph element (<hp:p>)."""
    if ns_map:
        p = etree.Element(f'{{{NS_HP}}}p', nsmap=ns_map)
    else:
        p = etree.Element(f'{{{NS_HP}}}p')
    p.set('paraPrIDRef', str(para_ref))
    p.set('styleIDRef', str(style_ref))
    p.set('pageBreak', '1' if page_break else '0')
    p.set('columnBreak', '0')
    p.set('merged', '0')

    run = etree.SubElement(p, f'{{{NS_HP}}}run')
    run.set('charPrIDRef', str(char_ref))
    t = etree.SubElement(run, f'{{{NS_HP}}}t')
    t.text = text
    return p


def remove_lineseg(elem):
    """Remove all linesegarray elements (Hancom auto-recalculates).

    CRITICAL: Must call after deepcopy to prevent glyph corruption.
    See docs/style-system.md rule #2.
    """
    for ls in list(elem.iter(f'{{{NS_HP}}}linesegarray')):
        ls.getparent().remove(ls)


# ============================================================
# Auto-Bullet Deduplication
# See docs/knowhow/bullet-dedup.md
# ============================================================

# Patterns for auto-inserted prefixes by level
AUTO_PREFIX_PATTERNS = {
    'H3': re.compile(r'^\d+\)\s*'),           # "1) " → strip
    'H4': re.compile(r'^\(\d+\)\s*'),          # "(1) " → strip
    'H5': re.compile(r'^[\u2460-\u2473]\s*'),  # "① " → strip
    'L1': re.compile(r'^[□■]\s*'),             # "□ " → strip
    'L2': re.compile(r'^[-\u2013\u2014]\s*'),  # "- ", "― " → strip
}


def strip_auto_prefixes(paragraphs):
    """Remove text prefixes that duplicate style auto-bullets.

    HWPX styles (Ctrl+2~6) automatically insert bullet/number symbols.
    If the markdown text already includes these symbols, they'll appear twice.
    """
    result = []
    for para in paragraphs:
        ptype = para['type']
        text = para['text']
        pattern = AUTO_PREFIX_PATTERNS.get(ptype)
        if pattern:
            text = pattern.sub('', text)
        result.append({**para, 'text': text})
    return result


# ============================================================
# Markdown Parser
# ============================================================

def parse_markdown(md_content):
    """Parse markdown content into typed paragraph dicts.

    Returns: list of {'type': str, 'text': str, ...}
    """
    paragraphs = []
    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped or stripped.startswith('---') or stripped.startswith('```'):
            i += 1
            continue

        if stripped.startswith('> '):
            i += 1
            continue

        # Headings
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            text = stripped.lstrip('#').strip()
            if level == 1:
                paragraphs.append({'type': 'H1', 'text': text})
            elif level == 2:
                paragraphs.append({'type': 'H2', 'text': text})
            elif level == 3:
                paragraphs.append({'type': 'H3', 'text': text})
            elif level == 4:
                paragraphs.append({'type': 'H4', 'text': text})
            elif level == 5:
                paragraphs.append({'type': 'H5', 'text': text})
            i += 1
            continue

        # Table blocks (convert to list format for HWPX compatibility)
        if stripped.startswith('|') and stripped.endswith('|'):
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
                for tl in table_lines[1:]:
                    if re.match(r'^\|[\s\-|:]+\|$', tl):
                        continue
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    details = []
                    first = cells[0] if cells else ''
                    for ci in range(1, min(len(headers), len(cells))):
                        if cells[ci]:
                            details.append(f'{headers[ci]}: {cells[ci]}')
                    if details:
                        text = f'{first} — {", ".join(details)}'
                    else:
                        text = first
                    paragraphs.append({'type': 'L1', 'text': text})
            continue

        # Bullet lists
        if stripped.startswith('- '):
            paragraphs.append({'type': 'L1', 'text': stripped[2:].strip()})
            i += 1
            continue

        if stripped.startswith('* '):
            paragraphs.append({'type': 'L2', 'text': stripped[2:].strip()})
            i += 1
            continue

        # Korean proposal symbols
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)  # Remove bold markers
        if text.startswith('□'):
            paragraphs.append({'type': 'L1', 'text': text})
        elif text.startswith('○') or text.startswith('❍'):
            paragraphs.append({'type': 'L1', 'text': text})
        elif text.startswith('―') or text.startswith('  ―'):
            paragraphs.append({'type': 'L2', 'text': text.lstrip()})
        elif text.startswith('※'):
            paragraphs.append({'type': 'note', 'text': text})
        else:
            paragraphs.append({'type': 'L1', 'text': text})

        i += 1

    return paragraphs


# ============================================================
# Style Remapper Engine
# See docs/knowhow/style-remapper.md
# ============================================================

def merge_reference_styles(tmpl_hdr_root, ref_hdr_root, ref_paras, para_range):
    """Merge styles from reference document into template header.

    Returns:
        style_id_maps: mapping dicts for charPr, paraPr, borderFill
        merged_header_xml: updated header XML bytes
    """
    HH_NS = 'http://www.hancom.co.kr/hwpml/2011/head'

    # Collect needed IDs from reference paragraphs
    bf_needed, cp_needed, pp_needed = set(), set(), set()
    for i in range(min(para_range[1], len(ref_paras))):
        if i < para_range[0]:
            continue
        p = ref_paras[i]
        pp_needed.add(p.get('paraPrIDRef', ''))
        for elem in p.iter():
            bfr = elem.get('borderFillIDRef', '')
            if bfr:
                bf_needed.add(bfr)
            tag = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
            if tag == 'run':
                cpr = elem.get('charPrIDRef', '')
                if cpr:
                    cp_needed.add(cpr)
            if tag == 'p':
                ppr = elem.get('paraPrIDRef', '')
                if ppr:
                    pp_needed.add(ppr)

    # --- Font Remapper ---
    tmpl_fonts_by_name = {}
    tmpl_max_font_id = 0
    tmpl_fontfaces_container = None
    for elem in tmpl_hdr_root.iter():
        t = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
        if t == 'fontface':
            name = elem.get('name')
            fid = int(elem.get('id', '0'))
            if name:
                tmpl_fonts_by_name[name] = str(fid)
            if fid > tmpl_max_font_id:
                tmpl_max_font_id = fid
        elif t == 'fontfaces':
            tmpl_fontfaces_container = elem

    ref_font_elems = {}
    for elem in ref_hdr_root.iter():
        t = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
        if t == 'fontface':
            ref_font_elems[elem.get('id')] = elem

    def get_remapped_font_id(ref_font_id):
        nonlocal tmpl_max_font_id
        if not ref_font_id:
            return None
        ref_elem = ref_font_elems.get(ref_font_id)
        if ref_elem is None:
            return ref_font_id
        ref_name = ref_elem.get('name')
        if ref_name in tmpl_fonts_by_name:
            return tmpl_fonts_by_name[ref_name]
        tmpl_max_font_id += 1
        new_id_str = str(tmpl_max_font_id)
        tmpl_fonts_by_name[ref_name] = new_id_str
        if tmpl_fontfaces_container is not None:
            new_elem = deepcopy(ref_elem)
            new_elem.set('id', new_id_str)
            tmpl_fontfaces_container.append(new_elem)
        return new_id_str

    # --- Style Remapper ---
    style_id_maps = {'borderFill': {}, 'charPr': {}, 'paraPr': {}}
    container_map = {
        'borderFill': 'borderFills',
        'charPr': 'charProperties',
        'paraPr': 'paraProperties',
    }
    merge_count = 0

    for tag_name, needed_ids in [('borderFill', bf_needed),
                                  ('charPr', cp_needed),
                                  ('paraPr', pp_needed)]:
        if not needed_ids:
            continue
        max_id = 0
        container = None
        for elem in tmpl_hdr_root.iter():
            t = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
            if t == tag_name:
                idx = int(elem.get('id', '0'))
                if idx > max_id:
                    max_id = idx
            elif t == container_map[tag_name]:
                container = elem
        if container is None:
            continue

        ref_map = {}
        for elem in ref_hdr_root.iter():
            t = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
            if t == tag_name and elem.get('id', '') in needed_ids:
                ref_map[elem.get('id', '')] = elem

        added = 0
        for old_id in list(needed_ids):
            if not old_id:
                continue
            ref_elem = ref_map.get(old_id)
            if ref_elem is None:
                continue
            max_id += 1
            new_id = str(max_id)
            style_id_maps[tag_name][old_id] = new_id
            new_elem = deepcopy(ref_elem)
            new_elem.set('id', new_id)

            if tag_name == 'charPr':
                for child in new_elem.iter():
                    ct = etree.QName(child.tag).localname if isinstance(child.tag, str) else ''
                    if ct == 'fontRef':
                        for attr in ['hangul', 'latin', 'hanja', 'japanese', 'other', 'symbol', 'user']:
                            if attr in child.attrib:
                                mapped = get_remapped_font_id(child.get(attr))
                                if mapped:
                                    child.set(attr, mapped)

            if tag_name == 'paraPr':
                bf_ref = new_elem.get('borderFillIDRef')
                if bf_ref and bf_ref in style_id_maps['borderFill']:
                    new_elem.set('borderFillIDRef', style_id_maps['borderFill'][bf_ref])

            container.append(new_elem)
            added += 1
            merge_count += 1

        if added > 0:
            cnt_attr = 'itemCnt' if 'itemCnt' in container.attrib else 'count'
            if cnt_attr in container.attrib:
                container.set(cnt_attr, str(int(container.get(cnt_attr, '0')) + added))

    print(f'  -> Merged {merge_count} style definitions via Remapper')
    return style_id_maps


def rewrite_section_ids(section_xml_str, style_id_maps):
    """Rewrite all *IDRef attributes in section XML using the remap table."""
    def remap_attr(match, map_dict):
        old_val = match.group(2)
        new_val = map_dict.get(old_val, old_val)
        return f"{match.group(1)}{new_val}{match.group(3)}"

    for attr_name, map_dict in [
        ('paraPrIDRef', style_id_maps['paraPr']),
        ('charPrIDRef', style_id_maps['charPr']),
        ('borderFillIDRef', style_id_maps['borderFill']),
    ]:
        def replacer(match, md=map_dict):
            return remap_attr(match, md)
        section_xml_str = re.sub(f'({attr_name}=")([^"]+)(")', replacer, section_xml_str)

    return section_xml_str


# ============================================================
# Main Conversion
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convert structured Markdown to HWPX format',
        epilog='After conversion, run fix_namespaces.py on the output file.'
    )
    parser.add_argument('--template', required=True, help='HWPX template file')
    parser.add_argument('--md', required=True, help='Markdown content file')
    parser.add_argument('--output', required=True, help='Output HWPX file')
    parser.add_argument('--config', default=None,
                        help='YAML style configuration file (see examples/style_config_example.yaml)')
    parser.add_argument('--reference', default=None,
                        help='Reference HWPX for cover/TOC page import')
    parser.add_argument('--cover-range', default=None,
                        help='Paragraph range for cover pages (e.g., "0:20")')
    parser.add_argument('--toc-range', default=None,
                        help='Paragraph range for TOC pages (e.g., "20:69")')
    parser.add_argument('--summary-range', default=None,
                        help='Paragraph range for summary table (e.g., "69:163")')
    parser.add_argument('--cover-keywords', nargs='*', default=[],
                        help='Keywords to identify cover page paragraphs in template')
    args = parser.parse_args()

    print(f'📄 Template:  {args.template}')
    print(f'📝 Markdown:  {args.md}')
    print(f'📦 Output:    {args.output}')
    if args.config:
        print(f'⚙️  Config:    {args.config}')
    if args.reference:
        print(f'📋 Reference: {args.reference}')

    # Load style config
    style_map = load_config(args.config)

    # Parse markdown
    with open(args.md, 'r', encoding='utf-8') as f:
        md_content = f.read()

    paragraphs = parse_markdown(md_content)
    print(f'\n[1/6] Parsed {len(paragraphs)} paragraphs from markdown')

    # Strip auto-bullet duplicates
    paragraphs = strip_auto_prefixes(paragraphs)
    print(f'[2/6] Auto-prefix deduplication applied')

    # Read template
    with zipfile.ZipFile(args.template, 'r') as z:
        section_xml = z.read('Contents/section0.xml')
        header_xml = z.read('Contents/header.xml')
        all_files = {name: z.read(name) for name in z.namelist()
                     if name not in ('Contents/section0.xml', 'Contents/header.xml')}

    section_tree = etree.fromstring(section_xml)
    ns_map = section_tree.nsmap
    existing_paras = section_tree.findall(f'{{{NS_HP}}}p')

    # Preserve template paragraph structures for deepcopy
    h1_template = deepcopy(existing_paras[1]) if len(existing_paras) > 1 else None
    h2_template = deepcopy(existing_paras[2]) if len(existing_paras) > 2 else None

    # --- Reference document merge (optional) ---
    front_paras = []
    merged_header = header_xml

    if args.reference and os.path.exists(args.reference):
        print(f'[3/6] Merging reference document styles')
        with zipfile.ZipFile(args.reference, 'r') as rz:
            ref_sec_xml = rz.read('Contents/section0.xml')
            ref_header_xml = rz.read('Contents/header.xml')

        tmpl_hdr_root = etree.fromstring(header_xml)
        ref_hdr_root = etree.fromstring(ref_header_xml)
        ref_root = etree.fromstring(ref_sec_xml)
        ref_paras = ref_root.findall(f'{{{NS_HP}}}p')

        # Determine merge range
        max_para = len(ref_paras)
        ranges = []
        for r_arg, label in [(args.cover_range, 'cover'),
                              (args.toc_range, 'toc'),
                              (args.summary_range, 'summary')]:
            if r_arg:
                start, end = map(int, r_arg.split(':'))
                ranges.append((start, min(end, max_para), label))

        overall_range = (0, max(e for _, e, _ in ranges)) if ranges else (0, 0)

        if overall_range[1] > 0:
            style_id_maps = merge_reference_styles(
                tmpl_hdr_root, ref_hdr_root, ref_paras, overall_range)

            # Rewrite IDs in reference section XML
            ref_sec_str = ref_sec_xml.decode('utf-8') if isinstance(ref_sec_xml, bytes) else ref_sec_xml
            ref_sec_str = rewrite_section_ids(ref_sec_str, style_id_maps)
            ref_root = etree.fromstring(ref_sec_str.encode('utf-8'))
            ref_paras = ref_root.findall(f'{{{NS_HP}}}p')

            # Extract front page paragraphs
            for start, end, label in ranges:
                for i in range(start, min(end, len(ref_paras))):
                    p = deepcopy(ref_paras[i])
                    remove_lineseg(p)
                    front_paras.append(p)
                print(f'  -> {label}: {end - start} paragraphs')

            # Preserve template secPr in first paragraph
            tmpl_secpr = existing_paras[0].find(f'.//{{{NS_HP}}}secPr') if existing_paras else None
            if front_paras and tmpl_secpr is not None:
                ref_secpr = front_paras[0].find(f'.//{{{NS_HP}}}secPr')
                if ref_secpr is not None:
                    parent = ref_secpr.getparent()
                    idx = list(parent).index(ref_secpr)
                    parent.remove(ref_secpr)
                    parent.insert(idx, deepcopy(tmpl_secpr))
                    print(f'  -> secPr preserved from template')

            merged_header = etree.tostring(tmpl_hdr_root, xml_declaration=True,
                                           encoding='UTF-8', pretty_print=True)
    else:
        print(f'[3/6] No reference document (skipped)')

    # --- Build content paragraphs ---
    print(f'[4/6] Building content paragraphs')

    # Preserve cover from template (keyword-based)
    cover_paras = []
    if args.cover_keywords and not front_paras:
        for p in existing_paras:
            texts = []
            for t in p.iter(f'{{{NS_HP}}}t'):
                if t.text:
                    texts.append(t.text)
            full = ''.join(texts).strip()
            if any(kw in full for kw in args.cover_keywords):
                cover_paras.append(deepcopy(p))

    # Remove existing paragraphs
    for p in list(section_tree.iterchildren(f'{{{NS_HP}}}p')):
        section_tree.remove(p)

    # Insert front pages (from reference or cover keywords)
    if front_paras:
        for p in front_paras:
            section_tree.append(p)
    elif cover_paras:
        for p in cover_paras:
            section_tree.append(p)

    # Insert content paragraphs
    stats = {}
    first_h1 = True
    h2_counter = 0

    for para in paragraphs:
        ptype = para['type']
        text = para['text']

        if ptype == 'H1' and h1_template is not None:
            p_elem = deepcopy(h1_template)
            remove_lineseg(p_elem)
            for run in p_elem.iterchildren(f'{{{NS_HP}}}run'):
                for t_elem in run.iterchildren(f'{{{NS_HP}}}t'):
                    t_elem.text = text
                    break
                break
            if first_h1:
                p_elem.set('pageBreak', '1')
                first_h1 = False
            h2_counter = 0
            section_tree.append(p_elem)

        elif ptype == 'H2' and h2_template is not None:
            h2_counter += 1
            p_elem = deepcopy(h2_template)
            remove_lineseg(p_elem)
            tbl = p_elem.find(f'.//{{{NS_HP}}}tbl')
            if tbl is not None:
                cells = list(tbl.iter(f'{{{NS_HP}}}tc'))
                if len(cells) >= 3:
                    cell0_t = cells[0].find(f'.//{{{NS_HP}}}t')
                    if cell0_t is not None:
                        cell0_t.text = str(h2_counter)
                    cell2_t = cells[2].find(f'.//{{{NS_HP}}}t')
                    if cell2_t is not None:
                        clean_text = re.sub(r'^\d+\s+', '', text)
                        cell2_t.text = f' {clean_text}'
            else:
                for t_elem in p_elem.iter(f'{{{NS_HP}}}t'):
                    t_elem.text = text
                    break
            section_tree.append(p_elem)

        else:
            s = style_map.get(ptype, style_map.get('body', DEFAULT_STYLE_MAP['body']))
            p_elem = create_paragraph(text, s['para'], s['char'], s.get('style', '0'),
                                      ns_map=ns_map)
            section_tree.append(p_elem)

        stats[ptype] = stats.get(ptype, 0) + 1

    # --- Serialize ---
    print(f'[5/6] Serializing HWPX')

    para_count = len(section_tree.findall(f'{{{NS_HP}}}p'))
    new_xml = etree.tostring(section_tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in all_files.items():
            zout.writestr(name, data)
        zout.writestr('Contents/header.xml', merged_header)
        zout.writestr('Contents/section0.xml', new_xml)

    # --- Report ---
    print(f'\n[6/6] Summary')
    print(f'  Total paragraphs: {para_count}')
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'    {k:18s}: {v:3d}')

    print(f'\n✅ Done: {args.output}')
    print(f'\n⚠️  Run fix_namespaces.py next!')
    print(f'   python scripts/fix_namespaces.py {args.output}')


if __name__ == '__main__':
    main()
