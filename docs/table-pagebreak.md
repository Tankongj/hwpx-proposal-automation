# Table Page-Break Solution

> This document explains how to make HWPX tables break across pages — a problem
> that is **not documented** in official Hancom resources.

## Problem

When you create or modify tables programmatically in HWPX, they may refuse to
break across pages. Instead, the entire table is pushed to the next page, leaving
a large blank space.

## Root Cause

Table page-breaking requires **THREE conditions** to be met simultaneously:

```xml
1. <hp:tbl textWrap="SQUARE">          ← "Treat as character" OFF
2. <hp:tbl pageBreak="TABLE">          ← Page-break enabled
3. <pos treatAsChar="0">               ← ★ The ACTUAL control (most important!)
```

> Setting `tbl.textWrap` and `tbl.pageBreak` is **not enough**.
> If `pos.treatAsChar="1"`, page-breaking is always disabled regardless
> of the other attributes.

## Attribute Mapping

| Hancom UI | XML Attribute | Value (enabled) | Value (disabled) |
|-----------|--------------|-----------------|------------------|
| Treat as char | `tbl.textWrap` | `TOP_AND_BOTTOM` | `SQUARE` |
| Treat as char | `pos.treatAsChar` | `1` | `0` |
| Page break | `tbl.pageBreak` | `TABLE` | `NONE` |
| Cell-level break | `tbl.pageBreak` | `CELL` | — |

## XML Location of pos.treatAsChar

```xml
<hp:tbl textWrap="SQUARE" pageBreak="TABLE" ...>
  <shapeComponent ...>
    <pos treatAsChar="0" vertRelTo="PARA" horzRelTo="PARA"
         affectLSpacing="0" flowWithText="1"
         allowOverlap="0" holdAnchorAndSO="0"
         vertAlign="TOP" horzAlign="LEFT"
         vertOffset="0" horzOffset="0"/>
    <sz width="47688" height="67668"/>
  </shapeComponent>
  <hp:tr>...</hp:tr>
</hp:tbl>
```

## Solution: XML Direct Modification

```python
import zipfile
import re

with zipfile.ZipFile('input.hwpx') as zin:
    xml = zin.read('Contents/section0.xml').decode('utf-8')

# 1. Set all pos.treatAsChar to 0
xml = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', xml)

# 2. Fix horzRelTo if needed (some templates use COLUMN instead of PARA)
# xml = re.sub(r'horzRelTo="COLUMN"', 'horzRelTo="PARA"', xml)

# 3. Reset cached linesegarray vertsize (large values = cached page height)
xml = re.sub(r'vertsize="(\d{5,})"', 'vertsize="1200"', xml)

with zipfile.ZipFile('output.hwpx', 'w') as zout:
    # Copy all files, replace section0.xml
    ...
```

## Why COM API Doesn't Work

The Hancom Automation COM API provides `Table.SetItem("TreatAsChar", False)`, but:

- It only changes `tbl.textWrap` in XML
- It does **NOT** change `pos.treatAsChar`
- Therefore, page-breaking still doesn't work

**XML direct modification is the only reliable programmatic solution.**

## linesegarray and vertsize

The parent `<hp:p>` element contains `<hp:linesegarray>` with cached layout data.
The `vertsize` attribute stores a cached page height:

- Large value (e.g., `63048`) → Fixed at one page height
- Small value (e.g., `1200`) → Hancom will recalculate on open

**After modifying tables, remove or reset `linesegarray`** to force Hancom to
recalculate the layout.

## Verification Script

```python
from lxml import etree
import zipfile

with zipfile.ZipFile('file.hwpx') as z:
    xml = z.read('Contents/section0.xml')
tree = etree.fromstring(xml)

NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
for i, tbl in enumerate(tree.iter(f'{{{NS}}}tbl')):
    for elem in tbl.iter():
        if 'treatAsChar' in elem.attrib:
            print(f'Table[{i}] pos.treatAsChar = {elem.get("treatAsChar")}')
```
