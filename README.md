<div align="center">

# 📄 HWPX Proposal Automation

**Automate Korean government proposal generation in HWPX (Hancom Office) format**

PPT/PDF → Markdown → HWPX — fully automated with AI agent skills and Python scripts.

[한국어](#한국어) · [English](#english) · [Quick Start](#quick-start) · [Documentation](docs/)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

</div>

---

## English

### What is this?

HWPX is the open XML document format used by **Hancom Office (한컴오피스 한글)**, the most widely used word processor in Korean government and public institutions. This project provides:

1. **Python scripts** to programmatically create and modify HWPX documents
2. **AI agent skills** (for Gemini/Claude-based coding agents) that automate the entire proposal writing pipeline
3. **Reverse-engineered documentation** of the HWPX format — much of which is not covered in official docs

### Why does this exist?

Korean government proposals (제안서) must be submitted in `.hwpx` format with strict formatting requirements. Manually converting PPT presentations into formatted HWPX documents is tedious and error-prone. This project automates:

- **PDF/PPT text extraction** → structured data
- **Markdown draft generation** → review and iterate
- **HWPX template injection** → preserving the original form's styles
- **Automated verification** → checking structure, symbols, writing style

### Key Technical Discoveries

These findings are **not documented** in official Hancom resources:

| Discovery | Details |
|-----------|---------|
| `charPrIDRef` mapping | Actual font/size is determined by `header.xml` charPr definitions, not style names |
| `pos.treatAsChar` | Controls table page-breaking behavior — `tbl.textWrap` alone is insufficient |
| `linesegarray` cache | Must be removed after `deepcopy` — Hancom regenerates on open |
| `hp:subList` requirement | Table cells require `tc → subList → p` structure, not direct `p` |
| Namespace prefix issue | `lxml` serialization adds `ns0:` prefix — must be removed via regex |
| `HwpxDocument.open()` limitation | Fails on complex templates — ZIP-level replacement is safer |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Skills Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Analyzer │→│ Architect│→│  Writer  │→│ Reviewer │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│         RFP Analysis  Structure    Content    Quality        │
│                       Design       Generation  Audit         │
├─────────────────────────────────────────────────────────────┤
│                    Python Scripts Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │extract   │ │analyze   │ │md_to_hwpx│ │fix_ns    │        │
│  │_pdf.py   │ │_template │ │.py       │ │.py       │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐                                   │
│  │write_hwpx│ │verify    │   Libraries: lxml, python-hwpx   │
│  │.py       │ │_hwpx.py  │              pdfplumber, zipfile  │
│  └──────────┘ └──────────┘                                   │
├─────────────────────────────────────────────────────────────┤
│  Input: PPT/PDF + HWPX Template  →  Output: HWPX + PDF      │
└─────────────────────────────────────────────────────────────┘
```

---

## 한국어

### 이 프로젝트는 무엇인가요?

한국 정부·공공기관 **제안서(HWPX)** 작성을 자동화하는 도구 모음입니다.

PPT/PDF 제안서를 한컴오피스 한글 서식(`.hwpx`)에 맞게 자동 변환합니다.

### 핵심 구성 요소

| 구성 | 설명 |
|------|------|
| **Python 스크립트 6종** | PDF 추출, 템플릿 분석, 마크다운→HWPX 변환, 네임스페이스 복원, 자가검증 |
| **AI 스킬 5종** | RFP 분석 → 구조 설계 → 콘텐츠 작성 → 리뷰 → HWPX 변환 |
| **역공학 문서** | 공식 문서에 없는 HWPX 포맷 기술 지식 |
| **워크플로우** | 제안서 작성 전체 프로세스 자동화 |

### 작동 원리

```
PPT/PDF 제안서 ──→ 텍스트 추출 ──→ 마크다운 초안 ──→ HWPX 변환
                        ↓                 ↓              ↓
                  RFP 분석          사용자 검토     네임스페이스 복원
                  평가매트릭스       내용 수정       자동 검증
                                                      ↓
                                                 ✅ 최종 HWPX
```

### HWPX 포맷 핵심 기술

이 프로젝트에서 발견한 **공식 문서에 없는** 핵심 기술들:

1. **ZIP-level XML 치환** — `HwpxDocument.open()`보다 안전한 방식
2. **charPrIDRef 실측값** — header.xml의 실제 폰트/크기 매핑
3. **`pos.treatAsChar` 제어** — 표 페이지 넘김의 진짜 핵심 속성
4. **`linesegarray` 캐시 제거** — deepcopy 후 필수 후처리
5. **네임스페이스 접두사 제거** — lxml 직렬화 후 필수 정규식 처리

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hwpx-proposal-automation.git
cd hwpx-proposal-automation

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### 1. Analyze an HWPX template
```bash
python scripts/analyze_template.py your-template.hwpx
```

#### 2. Convert Markdown to HWPX
```bash
python scripts/md_to_hwpx.py \
  --template your-template.hwpx \
  --md your-content.md \
  --output result.hwpx
```

#### 3. Fix namespaces (required!)
```bash
python scripts/fix_namespaces.py result.hwpx
```

#### 4. Verify the output
```bash
python scripts/verify_hwpx.py result.hwpx --type auto
```

### Using ZIP-level Replacement

```python
from scripts.write_hwpx import zip_replace, zip_replace_sequential

# Replace all occurrences
zip_replace("template.hwpx", "output.hwpx", {
    "PLACEHOLDER_TITLE": "My Project Title",
    "PLACEHOLDER_DATE": "2026. 4. 8.",
})

# Replace same placeholder with different values sequentially
zip_replace_sequential("output.hwpx", "output.hwpx",
    "PLACEHOLDER_NAME", ["Alice", "Bob", "Charlie"])
```

### Using AI Skills (with Gemini/Claude agents)

Copy the `skills/` directory to your AI agent's skill directory and trigger with:
- "제안서 작성" → activates the full pipeline
- "RFP 분석" → activates proposal-analyzer
- "HWPX 만들어" → activates hwpx-proposal

---

## Project Structure

```
hwpx-proposal-automation/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
│
├── scripts/                     # Python automation scripts
│   ├── analyze_template.py      # HWPX template text inspector
│   ├── write_hwpx.py            # ZIP-level batch/sequential replacement
│   ├── md_to_hwpx.py            # Markdown → HWPX converter (core)
│   ├── fix_namespaces.py        # XML namespace post-processor
│   ├── verify_hwpx.py           # HWPX self-verification system
│   └── extract_pdf.py           # PDF text extractor
│
├── skills/                      # AI Agent skill definitions
│   ├── hwpx-proposal/           # HWPX document creation skill
│   ├── proposal-analyzer/       # RFP analysis skill
│   ├── proposal-architect/      # Structure design skill
│   ├── proposal-writer/         # Content generation skill
│   └── proposal-reviewer/       # 7-Dimension review skill
│
├── docs/                        # Technical documentation
│   ├── architecture.md          # System architecture
│   ├── hwpx-format-guide.md     # HWPX format reverse-engineering
│   ├── style-system.md          # Style ID mapping tables
│   ├── table-pagebreak.md       # Table page-break solution
│   └── troubleshooting.md       # Common issues & fixes
│
├── workflows/                   # Automation workflows
│   └── write-proposal.md        # End-to-end proposal workflow
│
├── templates/                   # Example HWPX templates
│   └── (add your .hwpx here)
│
└── examples/                    # Usage examples
    └── example-content.md       # Sample markdown input
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design and data flow |
| [HWPX Format Guide](docs/hwpx-format-guide.md) | Reverse-engineered HWPX internals |
| [Style System](docs/style-system.md) | charPrIDRef, font tables, style mapping |
| [Table Page-break](docs/table-pagebreak.md) | How to make tables break across pages |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and their solutions |

---

## Contributing

Contributions are welcome! This project benefits the Korean developer community working with Hancom Office documents. Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **HWPX/OWPML Standard** — KS X 6101 (Korean open document standard)
- **python-hwpx** — Python library for HWPX document handling
- **Antigravity** — AI coding agent that built and iterated this system

---

<div align="center">

Made with 🌾 for the Korean public sector

</div>
