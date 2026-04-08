# HWPX Format Guide — Reverse-Engineered Internals

> ⚠️ Much of this information is **not documented** in official Hancom resources.
> It was discovered through extensive trial and error (53+ versions iterated).

## 1. What is HWPX?

HWPX is the open XML document format for **Hancom Office Hangul (한컴오피스 한글)**, based on:
- **KS X 6101** — Korean open document standard (OWPML)
- **ZIP + XML** package structure (similar concept to .docx, .xlsx)

It replaced the proprietary `.hwp` binary format.

## 2. Package Structure

```
document.hwpx (ZIP archive)
├── META-INF/
│   └── manifest.xml           # Lists all parts in the package
├── Contents/
│   ├── content.hpf            # Master index — references all sections
│   ├── header.xml             # ★ Style definitions (fonts, sizes, charPr)
│   ├── section0.xml           # ★ Main document body
│   ├── section1.xml           # Additional sections
│   └── ...
├── BinData/                   # Embedded binary resources
│   ├── image001.png
│   └── ...
└── Preview/
    └── PrvImage.png           # Document thumbnail
```

## 3. Paragraph Structure

Every paragraph in HWPX follows this XML structure:

```xml
<hp:p paraPrIDRef="8" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="63">
    <hp:t>This is the actual text content</hp:t>
  </hp:run>
  <hp:linesegarray>
    <hp:lineseg textStartPos="0" lineHeight="1000" ... />
  </hp:linesegarray>
</hp:p>
```

### Key Attributes

| Attribute | Location | Purpose |
|-----------|----------|---------|
| `paraPrIDRef` | `<hp:p>` | Paragraph formatting (spacing, alignment) |
| `styleIDRef` | `<hp:p>` | Named style reference (0=body, 1=outline1, etc.) |
| `charPrIDRef` | `<hp:run>` | ★ Character formatting (font, size) — defined in `header.xml` |
| `pageBreak` | `<hp:p>` | Page break before this paragraph (1=yes, 0=no) |

### Critical: charPrIDRef

The `charPrIDRef` attribute determines the actual font and size used. The values are
**defined in `header.xml`** and must be looked up — they are NOT sequential or predictable.

**Always use `analyze_template.py` to discover the correct values for your template.**

## 4. Style System (Korean Proposal Convention)

Korean government proposals use a 5-level hierarchical symbol system:

```
Level 0: □  (Major topic, bold)      — Highest level
Level 1: ❍  (Sub topic)              — Second level
Level 2: -  (Detail)                 — Third level
Level 3: ·  (Sub-detail)             — Fourth level
Level 4: *  (Reference/footnote)     — Lowest level
```

When using Hancom Office's built-in styles (Ctrl+1 through Ctrl+5), levels 1-4
automatically insert bullet symbols. **Do NOT manually add symbols in text** or
you'll get duplicate bullets.

Only Level 0 (□) should be typed directly in the text.

## 5. Table Structure

Tables in HWPX must follow strict nesting:

```xml
<hp:tbl textWrap="SQUARE" pageBreak="TABLE">
  <shapeComponent>
    <pos treatAsChar="0" .../>    <!-- ★ Critical for page-breaking -->
    <sz width="47688" height="67668"/>
  </shapeComponent>
  <hp:tr>                          <!-- Table row -->
    <hp:tc>                        <!-- Table cell -->
      <hp:subList>                 <!-- ★ REQUIRED wrapper -->
        <hp:p>                     <!-- Paragraph inside cell -->
          <hp:run>
            <hp:t>Cell text</hp:t>
          </hp:run>
        </hp:p>
      </hp:subList>
    </hp:tc>
  </hp:tr>
</hp:tbl>
```

> ⚠️ **CRITICAL**: Cells must use `tc → subList → p` structure.
> Placing `<hp:p>` directly inside `<hp:tc>` (without `<hp:subList>`)
> causes Hancom Office to crash or display corrupted content.

## 6. Content.hpf Integrity

`content.hpf` is the master index. Every section XML file must be referenced here.
If you add a new section (e.g., `section1.xml` for resumes), it must be registered
in `content.hpf` or Hancom Office will ignore it.

## 7. Namespace Map

HWPX uses two generations of namespaces:

### 2011 Version (most common)
```
hp  = http://www.hancom.co.kr/hwpml/2011/paragraph
hs  = http://www.hancom.co.kr/hwpml/2011/section
ht  = http://www.hancom.co.kr/hwpml/2011/text
hc  = http://www.hancom.co.kr/hwpml/2011/core
```

### 2018 Version (newer documents)
```
hp6 = urn:hancom:hwpml:2018:paragraph
hs6 = urn:hancom:hwpml:2018:section
ht6 = urn:hancom:hwpml:2018:text
hc6 = urn:hancom:hwpml:2018:core
```

When `lxml` serializes XML, it may add `ns0:`, `ns1:` etc. prefixes that Hancom
Office cannot parse. **Always run `fix_namespaces.py` after any XML manipulation.**

## 8. Font Embedding

HWPX files do **not** embed fonts. The target machine must have the required fonts
installed. Common fonts in Korean government documents:

| Font Name | Korean | Usage |
|-----------|--------|-------|
| HumanMyungJo | 휴먼명조 | Body text |
| HY GeonGoThic | HY견고딕 | Section titles |
| HanYang JungGothic | 한양중고딕 | References, footnotes |
| HanYang ShinMyungJo | 한양신명조 | Default (often unwanted) |
