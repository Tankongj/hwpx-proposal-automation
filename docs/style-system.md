# Style System — charPrIDRef & Font Mapping

> This document explains how HWPX styles work internally and how to customize
> the style mapping for your own templates.

## Overview

HWPX uses `charPrIDRef` (character property ID reference) as the primary mechanism
for controlling font, size, and formatting. These IDs are defined in `header.xml`
and are **template-specific** — every template has different ID values.

## How to Find Your Template's Style IDs

Run the template analyzer:

```bash
python scripts/analyze_template.py your-template.hwpx --output mapping.json
```

Then inspect `header.xml` inside the HWPX ZIP to find `charPr` definitions:

```python
import zipfile
from lxml import etree

with zipfile.ZipFile('your-template.hwpx') as z:
    header = z.read('Contents/header.xml')
    tree = etree.fromstring(header)
    
    # Find all charPr definitions
    for cp in tree.iter():
        if 'charPr' in (etree.QName(cp.tag).localname or ''):
            print(cp.attrib)
```

## Example Style Map (Reference Implementation)

This is an example from a real government proposal template. **Your values will differ.**

| Level | Symbol | charPrIDRef | Font | Size | Style |
|-------|--------|-------------|------|------|-------|
| Chapter | Ⅰ~Ⅴ | 63 | HumanMyungJo | 20pt | styleIDRef=16 |
| Section | 1~9 | 64 | HY GeonGoThic | 18pt | styleIDRef=153 |
| L0 | □ | 63 | HumanMyungJo | 20pt* | styleIDRef=0 (Ctrl+1) |
| L1 | ❍ | 65 | HumanMyungJo | 15pt | styleIDRef=1 (Ctrl+2) |
| L2 | - | 66 | HumanMyungJo | 15pt | styleIDRef=2 (Ctrl+3) |
| L3 | · | 66 | HumanMyungJo | 15pt | styleIDRef=3 (Ctrl+4) |
| L4 | * | 67 | HanYang JungGothic | 13pt | styleIDRef=4 (Ctrl+5) |

> *L0's charPr[63] defines 20pt, but styleIDRef=0 overrides to 18pt in display.

## Font Reference Table (Example)

| fontRef ID | Font Face |
|------------|-----------|
| 7 | 휴먼명조 (HumanMyungJo) |
| 8 | HY견고딕 (HY GeonGoThic) |
| 10 | HY중고딕 (HY JungGothic) |
| 14 | 한양신명조 (HanYang ShinMyungJo) |
| 15 | 한양중고딕 (HanYang JungGothic) |

## Customizing md_to_hwpx.py

Edit the `STYLE_MAP` dictionary in `scripts/md_to_hwpx.py`:

```python
STYLE_MAP = {
    'chapter_title': {'para': '8', 'char': '63'},   # Your chapter charPrIDRef
    'section_title': {'para': '8', 'char': '64'},   # Your section charPrIDRef
    'square':        {'para': '8', 'char': '52'},   # Your □ L0 charPrIDRef
    'circle':        {'para': '8', 'char': '65'},   # Your ○ L1 charPrIDRef
    'dash':          {'para': '8', 'char': '65'},   # Your ― L2 charPrIDRef
    'note':          {'para': '8', 'char': '66'},   # Your ※ L3 charPrIDRef
    'body':          {'para': '8', 'char': '65'},   # Your body text charPrIDRef
}
```

## Absolute Rules

1. **Use deepcopy for template paragraphs** — never create from scratch with guessed IDs
2. **Remove linesegarray after deepcopy** — prevents line-spacing corruption
3. **Fix charPrIDRef after deepcopy** — template defaults (e.g., ID 13) may be wrong
4. **Set pageBreak=1 only for chapters** — all others must be 0
5. **Section titles use 3-cell table** — replace text in cell 0 (number) and cell 2 (title)
6. **Remove ns0: prefixes after serialization** — regex post-processing required
7. **Remove all paragraphs after cover page** — inject new content after preserved cover
8. **No duplicate bullets** — Style bullets (❍/-/·/*) are automatic; only □ goes in text
