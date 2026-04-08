#!/usr/bin/env python3
"""
analyze_template.py — HWPX 템플릿 내부 텍스트 전수 조사 도구

HWPX 파일 내부의 모든 텍스트를 추출하여 플레이스홀더 매핑에 사용할 수 있도록
구조화된 형태로 출력한다.

Usage:
    python analyze_template.py template.hwpx [--output mapping.json]
"""

import sys
import json
import zipfile
from pathlib import Path
from lxml import etree

# HWPX 내부 XML에서 텍스트를 추출하는 네임스페이스
HWPX_NAMESPACES = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hp6': 'urn:hancom:hwpml:2018:paragraph',
    'ht': 'http://www.hancom.co.kr/hwpml/2011/text',
    'ht6': 'urn:hancom:hwpml:2018:text',
}


def extract_texts_from_xml(xml_content: bytes) -> list[dict]:
    """XML 컨텐츠에서 모든 텍스트 노드를 추출한다."""
    texts = []
    try:
        root = etree.fromstring(xml_content)
    except etree.XMLSyntaxError:
        return texts

    for elem in root.iter():
        tag_local = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
        if tag_local == 't' and elem.text and elem.text.strip():
            texts.append({
                'text': elem.text,
                'tag': elem.tag,
                'parent': elem.getparent().tag if elem.getparent() is not None else None,
            })
    return texts


def analyze_hwpx(hwpx_path: str, output_path: str = None) -> dict:
    """HWPX 파일 내부의 모든 텍스트를 추출·분석한다."""
    hwpx_path = Path(hwpx_path)
    if not hwpx_path.exists():
        print(f"Error: File not found: {hwpx_path}")
        sys.exit(1)

    result = {
        'file': str(hwpx_path),
        'sections': [],
        'all_texts': [],
        'unique_texts': [],
        'text_count': 0,
    }

    with zipfile.ZipFile(hwpx_path, 'r') as zf:
        xml_files = [f for f in zf.namelist() if f.endswith('.xml')]

        for xml_file in sorted(xml_files):
            xml_content = zf.read(xml_file)
            texts = extract_texts_from_xml(xml_content)

            if texts:
                section = {
                    'file': xml_file,
                    'texts': [t['text'] for t in texts],
                    'count': len(texts),
                }
                result['sections'].append(section)
                result['all_texts'].extend([t['text'] for t in texts])

    # 고유 텍스트 목록 (순서 유지)
    seen = set()
    for text in result['all_texts']:
        stripped = text.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            result['unique_texts'].append(stripped)

    result['text_count'] = len(result['all_texts'])

    # 출력
    print(f"\n📄 File: {hwpx_path.name}")
    print(f"📊 XML files: {len(result['sections'])}")
    print(f"📝 Total texts: {result['text_count']}")
    print(f"🔤 Unique texts: {len(result['unique_texts'])}")
    print(f"\n{'='*60}")

    for section in result['sections']:
        print(f"\n📁 {section['file']} ({section['count']} items)")
        print(f"{'-'*40}")
        for i, text in enumerate(section['texts'], 1):
            display = text.replace('\n', '\\n')
            if len(display) > 80:
                display = display[:77] + '...'
            print(f"  [{i:3d}] {repr(display)}")

    # JSON 출력 (선택)
    if output_path:
        output = Path(output_path)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n💾 Mapping saved: {output}")

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='HWPX template text inspector')
    parser.add_argument('hwpx_file', help='Path to the HWPX file to analyze')
    parser.add_argument('--output', '-o', help='Output JSON mapping file path')

    args = parser.parse_args()
    analyze_hwpx(args.hwpx_file, args.output)
