#!/usr/bin/env python3
"""
verify_hwpx.py — HWPX Self-Verification System.

Analyzes a generated HWPX file and reports:
  - File structure integrity
  - Content fill rate (for quantitative proposals)
  - Symbol hierarchy consistency (for qualitative proposals)
  - Writing style compliance
  - Page count estimation

Usage:
    python verify_hwpx.py output.hwpx [--type qualitative|quantitative|auto]
    python verify_hwpx.py output.hwpx --type qualitative
    python verify_hwpx.py output.hwpx --company-keywords "CompanyA" "CEO Name"

Exit codes:
    0 = verification rate >= 70%
    1 = verification rate < 70%
"""
import zipfile
import os
import sys
import argparse
from lxml import etree

NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'

# ============================================================
# Utilities
# ============================================================


def get_all_text(element):
    """Extract all <t> text under an element."""
    texts = []
    for t in element.iter('{%s}t' % NS):
        if t.text:
            texts.append(t.text)
    return ''.join(texts).strip()


def read_hwpx(path):
    """Read HWPX file and parse sections."""
    result = {'sections': {}, 'files': {}}
    with zipfile.ZipFile(path, 'r') as z:
        result['filelist'] = z.namelist()
        for name in z.namelist():
            result['files'][name] = z.read(name)
            if name.startswith('Contents/section') and name.endswith('.xml'):
                result['sections'][name] = etree.fromstring(z.read(name))
    return result


# ============================================================
# Check Item Class
# ============================================================


class CheckItem:
    def __init__(self, name, category, check_fn):
        self.name = name
        self.category = category
        self.check_fn = check_fn
        self.passed = False
        self.detail = ''

    def run(self, hwpx_data, **kwargs):
        try:
            self.passed, self.detail = self.check_fn(hwpx_data, **kwargs)
        except Exception as e:
            self.passed = False
            self.detail = f'Error: {e}'


# ============================================================
# Common Checks
# ============================================================


def check_file_opens(data, **kwargs):
    """Verify basic HWPX structure."""
    has_section = any('section' in f for f in data['filelist'])
    has_header = 'Contents/header.xml' in data['filelist']
    has_hpf = 'Contents/content.hpf' in data['filelist']
    ok = has_section and has_header and has_hpf
    return ok, f"section={has_section}, header={has_header}, hpf={has_hpf}"


def check_hpf_integrity(data, **kwargs):
    """Verify content.hpf references all sections."""
    hpf_text = data['files']['Contents/content.hpf'].decode('utf-8', errors='replace')
    sections = [f for f in data['filelist']
                if f.startswith('Contents/section') and f.endswith('.xml')]
    missing = []
    for s in sections:
        sec_id = s.replace('Contents/', '').replace('.xml', '')
        if sec_id not in hpf_text:
            missing.append(sec_id)
    ok = len(missing) == 0
    detail = f"sections={len(sections)}, missing={missing}" if missing else f"sections={len(sections)}, all referenced"
    return ok, detail


def check_date_filled(data, **kwargs):
    """Check that date placeholders have been filled."""
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    full_text = get_all_text(section0)
    has_placeholder = '0.  0.' in full_text or '월    일' in full_text
    return not has_placeholder, f"Date placeholder: {'found ❌' if has_placeholder else 'none ✅'}"


# ============================================================
# Qualitative Proposal Checks (정성제안서)
# ============================================================


def check_qualitative_structure(data, **kwargs):
    """Verify chapter markers (Ⅰ~Ⅳ)."""
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    full_text = get_all_text(section0)
    chapters = ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ']
    found = [ch for ch in chapters if ch in full_text]
    ok = len(found) >= 3
    return ok, f"Chapters found: {found}"


def check_symbol_system(data, **kwargs):
    """Verify symbol hierarchy □→○→―→※."""
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    full_text = get_all_text(section0)
    symbols = {'□': full_text.count('□'), '○': full_text.count('○'),
               '―': full_text.count('―'), '※': full_text.count('※')}
    ok = all(v > 0 for v in symbols.values())
    return ok, f"□={symbols['□']}, ○={symbols['○']}, ―={symbols['―']}, ※={symbols['※']}"


def check_writing_style(data, **kwargs):
    """Verify Korean formal writing style (~임/~음/~함/~됨)."""
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    full_text = get_all_text(section0)
    endings = ['임', '음', '함', '됨']
    counts = {e: full_text.count(e) for e in endings}
    total = sum(counts.values())
    bad_patterns = ['할 수 있', '가능하다', '것이다']
    bad_counts = {b: full_text.count(b) for b in bad_patterns}
    bad_total = sum(bad_counts.values())
    ok = total > 20 and bad_total < 5
    return ok, f"Formal endings: {total}, vague expressions: {bad_total}"


def check_paragraph_count(data, **kwargs):
    """Estimate page count from paragraph count."""
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    paras = section0.findall('.//{%s}p' % NS)
    tables = section0.findall('.//{%s}tbl' % NS)
    est_pages = len(paras) / 35  # ~35 paragraphs per A4 page
    ok = 10 <= est_pages <= 55
    return ok, f"Paragraphs: {len(paras)}, Tables: {len(tables)}, Est. pages: {est_pages:.0f}"


# ============================================================
# Advanced Structural Checks (new in v2)
# ============================================================


def check_treat_as_char(data, **kwargs):
    """Check if all tables have pos.treatAsChar=0 for page-breaking.

    See docs/table-pagebreak.md — 3 conditions required.
    """
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return True, "section0 not found — skipped"

    import re
    xml_bytes = data['files'].get('Contents/section0.xml', b'')
    xml_str = xml_bytes.decode('utf-8', errors='replace') if isinstance(xml_bytes, bytes) else xml_bytes
    count_1 = len(re.findall(r'treatAsChar="1"', xml_str))
    count_0 = len(re.findall(r'treatAsChar="0"', xml_str))

    if count_1 == 0:
        return True, f"treatAsChar=0: {count_0}, treatAsChar=1: 0 ✅"
    return False, f"treatAsChar=0: {count_0}, treatAsChar=1: {count_1} ⚠️ (run fix_namespaces.py --fix-tables)"


def check_namespace_pollution(data, **kwargs):
    """Check for lxml namespace prefix pollution (ns0:, ns1:).

    See docs/knowhow/namespace-corruption.md
    """
    import re
    for name in data['filelist']:
        if not name.endswith('.xml'):
            continue
        xml_bytes = data['files'].get(name, b'')
        xml_str = xml_bytes.decode('utf-8', errors='replace') if isinstance(xml_bytes, bytes) else xml_bytes
        ns_matches = re.findall(r'</?ns\d+:', xml_str)
        if ns_matches:
            return False, f"{name}: found {len(ns_matches)} ns prefixes ⚠️ (run fix_namespaces.py)"
    return True, "No namespace pollution found ✅"


def check_lineseg_anomaly(data, **kwargs):
    """Check for abnormally large linesegarray vertsize values."""
    import re
    section0_bytes = data['files'].get('Contents/section0.xml', b'')
    xml_str = section0_bytes.decode('utf-8', errors='replace') if isinstance(section0_bytes, bytes) else section0_bytes
    large = re.findall(r'vertsize="(\d{5,})"', xml_str)
    if large:
        return False, f"Found {len(large)} large vertsize values (≥10000) — may cause layout issues"
    return True, "No linesegarray anomalies found ✅"


def check_bullet_duplication(data, **kwargs):
    """Check for double bullet symbols (e.g., '□ □' or '○ ○').

    See docs/knowhow/bullet-dedup.md
    """
    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return True, "section0 not found — skipped"
    full_text = get_all_text(section0)
    dups = 0
    for pattern in ['□ □', '○ ○', '❍ ❍', '― ―', '- - ']:
        count = full_text.count(pattern)
        dups += count
    if dups > 0:
        return False, f"Found {dups} probable double-bullet occurrences ⚠️"
    return True, "No bullet duplication found ✅"


# ============================================================
# Quantitative Proposal Checks (정량제안서)
# ============================================================


def check_table_fill_rate(data, **kwargs):
    """Calculate table cell fill rate."""
    total_cells = 0
    filled_cells = 0
    table_stats = []

    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"

    tables = section0.findall('.//{%s}tbl' % NS)
    for ti, tbl in enumerate(tables):
        t_total = 0
        t_filled = 0
        rows = tbl.findall('{%s}tr' % NS)
        for row in rows:
            cells = row.findall('{%s}tc' % NS)
            for cell in cells:
                t_total += 1
                text = get_all_text(cell)
                if text and text not in ['(빈칸)', '-', '']:
                    t_filled += 1
        total_cells += t_total
        filled_cells += t_filled
        rate = (t_filled / t_total * 100) if t_total > 0 else 0
        table_stats.append(f"Table{ti+1}: {t_filled}/{t_total} ({rate:.0f}%)")

    overall = (filled_cells / total_cells * 100) if total_cells > 0 else 0
    ok = overall >= 50
    detail = f"Total: {filled_cells}/{total_cells} ({overall:.0f}%) | " + ', '.join(table_stats[:5])
    return ok, detail


def check_resume_section(data, **kwargs):
    """Check if resume section (section1) exists."""
    has_s1 = 'Contents/section1.xml' in data['filelist']
    if has_s1:
        s1_size = len(data['files']['Contents/section1.xml'])
        return True, f"section1: {s1_size:,} bytes"
    return False, "section1 not found — resume not merged"


def check_company_data(data, **kwargs):
    """Check if company-specific keywords are present."""
    company_keywords = kwargs.get('company_keywords', [])
    if not company_keywords:
        return True, "No company keywords configured — skipped"

    section0 = data['sections'].get('Contents/section0.xml')
    if section0 is None:
        return False, "section0 not found"
    full_text = get_all_text(section0)
    found = [kw for kw in company_keywords if kw in full_text]
    missing = [kw for kw in company_keywords if kw not in full_text]
    ok = len(missing) == 0
    return ok, f"Found: {found}, Missing: {missing}"


# ============================================================
# Main Verification Engine
# ============================================================


def run_verification(hwpx_path, doc_type='auto', company_keywords=None):
    """Run verification on an HWPX file."""
    print(f"\n{'='*60}")
    print(f"📋 HWPX Self-Verification System")
    print(f"   File: {os.path.basename(hwpx_path)}")
    print(f"   Size: {os.path.getsize(hwpx_path):,} bytes")
    print(f"{'='*60}")

    data = read_hwpx(hwpx_path)

    # Auto-detect type from filename
    if doc_type == 'auto':
        fname = os.path.basename(hwpx_path).lower()
        if '정량' in fname or 'quantitative' in fname:
            doc_type = 'quantitative'
        else:
            doc_type = 'qualitative'

    print(f"   Type: {doc_type}\n")

    # Common checks
    checks = [
        CheckItem('File Structure', 'common', check_file_opens),
        CheckItem('content.hpf Integrity', 'common', check_hpf_integrity),
        CheckItem('Date Fields', 'common', check_date_filled),
        CheckItem('Namespace Pollution', 'advanced', check_namespace_pollution),
        CheckItem('Table treatAsChar', 'advanced', check_treat_as_char),
        CheckItem('Lineseg Anomaly', 'advanced', check_lineseg_anomaly),
        CheckItem('Bullet Duplication', 'advanced', check_bullet_duplication),
    ]

    if doc_type == 'qualitative':
        checks += [
            CheckItem('Chapter Structure (Ⅰ~Ⅳ)', 'qualitative', check_qualitative_structure),
            CheckItem('Symbol System (□○―※)', 'qualitative', check_symbol_system),
            CheckItem('Writing Style', 'qualitative', check_writing_style),
            CheckItem('Page Count', 'qualitative', check_paragraph_count),
        ]
    elif doc_type == 'quantitative':
        checks += [
            CheckItem('Table Fill Rate', 'quantitative', check_table_fill_rate),
            CheckItem('Resume Section', 'quantitative', check_resume_section),
            CheckItem('Company Data', 'quantitative', check_company_data),
        ]

    # Run checks
    extra_kwargs = {}
    if company_keywords:
        extra_kwargs['company_keywords'] = company_keywords

    for check in checks:
        check.run(data, **extra_kwargs)

    # Results
    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    rate = (passed / total * 100) if total > 0 else 0

    print(f"{'─'*60}")
    print(f"{'Item':<30} {'Result':^8} {'Detail'}")
    print(f"{'─'*60}")
    for c in checks:
        icon = '✅' if c.passed else '❌'
        print(f"{c.name:<30} {icon:^8} {c.detail}")

    print(f"\n{'='*60}")
    print(f"📊 Summary: {passed}/{total} passed ({rate:.0f}%)")

    if rate >= 90:
        print(f"🏆 Status: Excellent — Ready to submit")
    elif rate >= 70:
        print(f"⚠️ Status: Good — Minor fixes needed")
    elif rate >= 50:
        print(f"🔧 Status: Fair — Significant fixes needed")
    else:
        print(f"❌ Status: Poor — Major rework needed")

    print(f"{'='*60}")

    failed = [c for c in checks if not c.passed]
    if failed:
        print(f"\n🔴 Failed items:")
        for i, c in enumerate(failed, 1):
            print(f"  {i}. [{c.category}] {c.name}: {c.detail}")

    return {
        'passed': passed,
        'total': total,
        'rate': rate,
        'failed': [{'name': c.name, 'detail': c.detail} for c in failed],
        'checks': [{'name': c.name, 'passed': c.passed, 'detail': c.detail} for c in checks]
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HWPX Self-Verification System')
    parser.add_argument('hwpx_path', help='HWPX file to verify')
    parser.add_argument('--type', choices=['qualitative', 'quantitative', 'auto'],
                        default='auto', help='Document type (default: auto-detect)')
    parser.add_argument('--company-keywords', nargs='*', default=[],
                        help='Company-specific keywords to check for (quantitative only)')

    args = parser.parse_args()

    if not os.path.exists(args.hwpx_path):
        print(f"❌ File not found: {args.hwpx_path}")
        sys.exit(1)

    result = run_verification(args.hwpx_path, args.type, args.company_keywords)
    sys.exit(0 if result['rate'] >= 70 else 1)
