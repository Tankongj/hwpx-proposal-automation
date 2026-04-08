# System Architecture

## Overview

This project automates Korean government proposal generation (제안서) through a two-layer architecture:

1. **AI Agent Skills Layer** — High-level reasoning, content generation, quality review
2. **Python Scripts Layer** — Low-level HWPX file manipulation

## Data Flow

```
Input                    Processing                      Output
─────                    ──────────                      ──────

PPT/PDF ──→ extract_pdf.py ──→ Raw Text
                                  │
                                  ▼
RFP PDF ──→ proposal-analyzer ──→ Evaluation Matrix
                                  │
                                  ▼
                          proposal-architect ──→ Structure Design
                                  │                (TOC, page allocation)
                                  ▼
                          proposal-writer ──→ Markdown Draft (50K+ chars)
                                  │
                                  ▼
                          proposal-reviewer ──→ Quality Report
                                  │                (7-dimension audit)
                                  ▼
HWPX Template ──→ analyze_template.py ──→ Text Map
     │                                       │
     └────────────────────┬──────────────────┘
                          ▼
                    md_to_hwpx.py ──→ Raw HWPX
                          │
                          ▼
                    fix_namespaces.py ──→ Fixed HWPX
                          │
                          ▼
                    verify_hwpx.py ──→ Verification Report
                          │
                          ▼
                     ✅ Final HWPX + PDF
```

## Skill Chain

The 5 AI skills form a sequential pipeline:

| Order | Skill | Input | Output |
|-------|-------|-------|--------|
| 1 | `proposal-analyzer` | RFP document | Evaluation matrix |
| 2 | `proposal-architect` | Eval matrix | Structure design (TOC + page allocation) |
| 3 | `proposal-writer` | Structure design + Reference docs | Markdown content (50K+ chars) |
| 4 | `proposal-reviewer` | Markdown content + Eval matrix | Quality report + auto-fixes |
| 5 | `hwpx-proposal` | Markdown + HWPX template | Final HWPX document |

Each skill can also be used independently.

## Script Dependencies

```
analyze_template.py ─── lxml, zipfile
write_hwpx.py ───────── zipfile, json
md_to_hwpx.py ───────── lxml, zipfile, copy (core engine)
fix_namespaces.py ────── zipfile, re
verify_hwpx.py ──────── lxml, zipfile
extract_pdf.py ──────── pdfplumber
```

## HWPX File Internals

HWPX is a ZIP package containing XML parts (KS X 6101 / OWPML standard):

```
document.hwpx (ZIP)
├── META-INF/
│   └── manifest.xml         # Package manifest
├── Contents/
│   ├── content.hpf          # Document structure index
│   ├── header.xml           # Styles, fonts, charPr definitions
│   ├── section0.xml         # Main document content
│   ├── section1.xml         # Additional sections (e.g., resumes)
│   └── ...
├── BinData/                  # Embedded images/resources
│   ├── image1.png
│   └── ...
└── Preview/
    └── PrvImage.png          # Thumbnail
```

### Key Insight: ZIP-level Replacement

Instead of parsing and rebuilding the XML DOM (which can corrupt complex templates),
we work at the ZIP level:

1. Open the HWPX as a ZIP file
2. Read each XML file as a UTF-8 string
3. Perform text replacement (batch or sequential)
4. Write the modified strings back to a new ZIP
5. Fix any namespace corruption caused by the replacement

This is **more reliable** than using `HwpxDocument.open()` from python-hwpx,
which can fail on complex government proposal templates.
