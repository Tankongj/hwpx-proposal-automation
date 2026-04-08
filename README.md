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
| **Python 스크립트 7종** | PPT 파싱, PDF 추출, 템플릿 분석, 마크다운→HWPX 변환, 네임스페이스 복원, 자가검증 |
| **AI 스킬 5종** | PPT 파싱 결과 기반 RFP 분석 → 구조 설계 → 콘텐츠 작성 → 리뷰 → HWPX 변환 |
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

## 💡 Advanced AI & 외부 생태계 통합 (Harness Engineering)

본 프로젝트는 최신 AI 에이전트 패러다임인 **Harness Engineering** 철학에 입각하여 설계되었습니다.

- **PPT 자동 파싱 (`extract_ppt.py`)**: `python-pptx`를 이용해 PPT 슬라이드의 텍스트와 표 구조를 직접 JSON으로 추출하여 AI가 완벽히 이해할 수 있도록 돕습니다.
- **외부 도구 완벽 호환**: 이 저장소의 파이프라인은 직접 만든 파이썬 스크립트 외에도 오픈소스 HWPX 조작 생태계(`hwpilot`, `hwpxskill` 등)와 결합할 수 있도록 유연하게 짜여 있습니다.
- **AI 에이전트 워크플로우 보장 (`AGENTS.md`)**: 에이전트가 어떤 순서로 판단하고 작업할지 명확히 제한하여 환각(Hallucination) 없이 반복적인 성과를 냅니다.

---

## Quick Start (빠른 시작 가이드)

본 저장소의 스크립트들은 파이썬 환경만 있으면 작동하도록 설계되었습니다. 복잡한 한글 오피스 API 연동이 필요 없습니다! 🚀

### 0. 설치 방법 (Installation)

```bash
# 저장소 클론 (Clone the repository)
git clone https://github.com/Tankongj/hwpx-proposal-automation.git
cd hwpx-proposal-automation

# 의존성 패키지 설치 (Install dependencies)
pip install -r requirements.txt
```

> **Tip:** 가상환경(`python -m venv venv`)을 만들어서 설치하시는 것을 권장합니다.

---

### 👨‍💻 사람이 할 일 vs 🤖 AI가 할 일 (작업 분담 가이드)

이 도구는 **인간의 창의적 작업(기초 데이터 준비)**과 **AI의 단순 노동(양식 맞춤 조립)**을 완벽히 분리합니다.

**✅ 사람이 할 일 (마우스 드래그 앤 드롭)**
1. `templates/` 폴더에 빈 제안서 양식 `.hwpx` 채워넣기
2. `input/` 폴더에 가공할 PPT 내용, PDF 공고문, 참고자료 파일 넣어두기
3. (선택) `examples/example-content.md`를 참고해 뼈대 내용만 마크다운으로 정리해두기

**✅ AI/자동화가 할 일 (아래 스크립트들이 수행)**
위처럼 재료만 모아두면, 다음 스크립트들이 **"내용 파싱 → 템플릿 주입 → HWPX 생성 → 표 오류 복원 → 규격 검증"** 까지의 모든 과정을 10초 만에 자동으로 완료합니다.

---

### 1단계: 내 템플릿 분석하기 (Analyze Template)
먼저, 여러분이 가진 빈 한글 파일(HWPX)의 스타일 ID를 알아내야 합니다.

```bash
python scripts/analyze_template.py my-template.hwpx
```
- 화면에 빈 파일 내의 임시 텍스트와 파일 구조가 출력됩니다.
- 이 정보를 바탕으로 폰트나 글자 크기가 지정된 `charPrIDRef` 값을 찾아 향후 커스텀에 활용할 수 있습니다. 자세한 방법은 [Style System 문서](docs/style-system.md)를 참고하세요.

### 2단계: 마크다운 초안 작성하기 (Write Draft)
`examples/example-content.md`를 참고하여, HWPX로 변환될 내용의 마크다운 초안을 작성합니다.
> **문법 규칙:** 대주제는 `□`, 중주제는 `○`, 소주제는 `―`로 시작하면 자동으로 한글(HWPX)의 들여쓰기와 스타일 매핑이 적용됩니다.

### 3단계: 마크다운을 HWPX로 변환 (Convert to HWPX)
가장 핵심이 되는 스크립트입니다. 마크다운의 내용을 빈 템플릿의 서식에 맞춰 HWPX로 찍어냅니다.

```bash
python scripts/md_to_hwpx.py \
  --template my-template.hwpx \
  --md my-draft.md \
  --output result.hwpx
```
- `--cover-keywords "제안서" "2026"` 처럼 옵션을 주면 템플릿의 표지가 유지됩니다.

### 4단계: 네임스페이스 복원 (Fix Namespaces - 필수!)
변환 직후의 파일은 구조적으로 약간 꼬여있을 수 있습니다. 한글 뷰어에서 내용이 누락되는(빈 페이지 여백 이슈) 것을 막기 위해 **반드시** 후처리를 실행해야 합니다.

```bash
python scripts/fix_namespaces.py result.hwpx
```

### 5단계: 문서 자동 검증 (Verify Output)
수십 페이지가 넘는 제안서에 누락된 부분이 없는지 5초 만에 검증해 보세요!

```bash
# 정성제안서 기호 및 문체 검증
python scripts/verify_hwpx.py result.hwpx --type qualitative

# 정량제안서 표 공란율 및 특정 키워드 검증
python scripts/verify_hwpx.py result.hwpx --type quantitative --company-keywords "내회사이름"
```

---

### (고급 설정) ZIP 레벨 치환 사용하기
단순히 표지 날짜나 이름만 바꾸려면 `write_hwpx.py`를 파이썬 코드에서 불러와 사용할 수 있습니다.

```python
from scripts.write_hwpx import zip_replace, zip_replace_sequential

# 일괄 치환 (모든 곳의 해당 단어를 변경)
zip_replace("template.hwpx", "output.hwpx", {
    "PLACEHOLDER_TITLE": "우주 최강 제안서",
    "PLACEHOLDER_DATE": "2026. 4. 8.",
})

# 순차 치환 (이력서 등 동일 항목이 반복될 때 순서대로 값 넣기)
zip_replace_sequential("output.hwpx", "output.hwpx",
    "PLACEHOLDER_NAME", ["홍길동", "김파이썬", "박지피티"])
```

### (고급 설정) 기존 파일 수정 및 표 자동보정 API 사용하기 (v0.2+)
새로 추가된 `hwpx_editor` 패키지를 이용하면 단순 치환을 넘어, 기존 문서의 단락을 삽입/수정하고 깨진 표 구조를 자동 보정할 수 있습니다.

```python
from scripts.hwpx_editor import open_hwpx, update_section, replace_text

# 기존 파일 불러오기 및 텍스트 안전 변경 (바이트 보존)
update_section('my-proposal.hwpx', 'Contents/section0.xml', 
               lambda xml: replace_text(xml, '2025년', '2026년'),
               output_path='updated-proposal.hwpx')
```

### AI 에이전트와 함께 쓰기 (Gemini/Claude)
이 저장소에 있는 `skills/` 디렉토리를 여러분의 AI 코드 에이전트 환경에 복사해 넣으면, AI가 제안서를 분석하고, 작성하고, HWPX로 만들어 검사하는 전 과정을 자동으로 수행합니다! (상세 내용은 `workflows/` 폴더 참조)

---

## Project Structure

```
hwpx-proposal-automation/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
│
├── scripts/                     # Python automation scripts
│   ├── extract_ppt.py           # PPT/PPTX slide & table extractor
│   ├── analyze_template.py      # HWPX template text inspector
│   ├── write_hwpx.py            # ZIP-level batch/sequential replacement
│   ├── md_to_hwpx.py            # Markdown → HWPX converter (core)
│   ├── fix_namespaces.py        # XML namespace post-processor
│   ├── verify_hwpx.py           # HWPX self-verification system
│   ├── extract_pdf.py           # PDF text extractor
│   └── hwpx_editor/             # Advanced byte-preserving HWPX editor API
│       ├── _parser.py           # Depth-tracking string XML parser
│       ├── table_fixer.py       # Table pagination and colSpan solver
│       └── modify_hwpx.py       # Safe XML text/paragraph replacer
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
| [Competitive Analysis](docs/competitive-analysis.md) | Comparison with other HWPX open-source tools |

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
- **python-pptx** — Standard library for PPT extraction
- **hwpilot & hwpxskill** — Excellent external tools for granular HWPX editing
- **Antigravity** — AI coding agent that built and iterated this system

---

<div align="center">

Made with 🌾 for the Korean public sector

</div>
