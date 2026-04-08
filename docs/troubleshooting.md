# Troubleshooting Guide

Common issues encountered when working with HWPX files programmatically,
and their solutions.

---

## 1. Blank Pages in Hancom Office

**Symptom**: Generated HWPX file opens but shows blank pages.

**Cause**: XML namespace corruption after text replacement.

**Solution**: Always run `fix_namespaces.py` after any ZIP-level replacement:
```bash
python scripts/fix_namespaces.py output.hwpx
```

---

## 2. Wrong Font/Size Displayed

**Symptom**: Text appears in wrong font or size despite setting `charPrIDRef`.

**Cause**: Using wrong `charPrIDRef` value. Common mistake: using ID `30` (10pt 한양신명조)
instead of the correct ID from your template.

**Solution**:
1. Analyze your template: `python scripts/analyze_template.py your-template.hwpx`
2. Inspect `header.xml` inside the HWPX ZIP to find correct charPr definitions
3. Update `STYLE_MAP` in `md_to_hwpx.py`

**Known bad value**: `charPrIDRef=30` → 10pt 한양신명조 (default, usually wrong)

---

## 3. Garbled Line Spacing / Character Width

**Symptom**: Characters appear compressed or stretched.

**Cause**: `linesegarray` contains cached layout data from the template.

**Solution**: Remove `linesegarray` after `deepcopy`:
```python
from copy import deepcopy
from lxml import etree

NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'

new_para = deepcopy(template_para)
# Remove all linesegarray elements
for lsa in new_para.findall(f'{{{NS}}}linesegarray'):
    new_para.remove(lsa)
```

---

## 4. Tables Don't Break Across Pages

**Symptom**: Table is pushed to next page instead of splitting.

**Cause**: `pos.treatAsChar="1"` in the table's `shapeComponent`.

**Solution**: See [Table Page-break Guide](table-pagebreak.md) for full details.

Quick fix:
```python
import re
xml = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', xml)
```

---

## 5. Table Cell Content Not Displaying

**Symptom**: Table exists but cells appear empty.

**Cause**: Missing `<hp:subList>` wrapper. HWPX requires:
```
tc → subList → p → run → t
```
NOT:
```
tc → p → run → t  (⚠️ WRONG)
```

**Solution**: Always use the `tc → subList → p` nesting:
```xml
<hp:tc>
  <hp:subList>
    <hp:p>
      <hp:run charPrIDRef="65">
        <hp:t>Cell content here</hp:t>
      </hp:run>
    </hp:p>
  </hp:subList>
</hp:tc>
```

---

## 6. Images Not Showing

**Symptom**: Image placeholder appears but image is missing.

**Cause**: Image file added to `BinData/` folder but not registered in `header.xml`'s
`binDataItem` list.

**Workaround**: Currently, programmatic image insertion is unreliable.
Use `[IMG] description (filename.png)` placeholder text and insert images manually
in Hancom Office.

---

## 7. `HwpxDocument.open()` Crashes

**Symptom**: `python-hwpx`'s `HwpxDocument.open()` fails with XML parsing errors.

**Cause**: Complex government proposal templates contain structures that
`python-hwpx` cannot parse.

**Solution**: Use **ZIP-level replacement** instead:
```python
from scripts.write_hwpx import zip_replace

zip_replace("template.hwpx", "output.hwpx", {
    "placeholder_text": "actual_content"
})
```

---

## 8. Duplicate Bullet Symbols

**Symptom**: Lines show double bullets like "❍ ○ Sub topic" instead of "❍ Sub topic".

**Cause**: Hancom's built-in styles (Ctrl+2~5) automatically insert bullet symbols.
Adding symbols in the text content creates duplicates.

**Solution**:
- Level 0 (□): Type `□` directly in text ✅
- Level 1-4: Do NOT include ❍, -, ·, * in text — the style inserts them automatically

---

## 9. COM API `TreatAsChar` Not Working

**Symptom**: Setting `Table.SetItem("TreatAsChar", False)` via COM API doesn't
enable page-breaking.

**Cause**: COM API only modifies `tbl.textWrap`, not `pos.treatAsChar` in XML.

**Solution**: Use XML direct modification:
```python
import re
xml = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', xml)
```

---

## 10. Windows Path Issues with Korean Characters

**Symptom**: Scripts fail when file paths contain Korean characters.

**Solution**: Always use UTF-8 encoding when reading/writing files:
```python
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
```

For `pathlib`:
```python
from pathlib import Path
content = Path(path).read_text(encoding='utf-8')
```
