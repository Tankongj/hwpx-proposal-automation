# Project Harness (AGENTS.md)

> Instructions for AI agents working on HWPX proposal automation projects.
> Place this file in your project root and load the `skills/` directory into your agent.

## Project Overview

- **Project**: HWPX Proposal Automation
- **Goal**: Automate Korean government proposal generation (PPT/PDF → Markdown → HWPX)
- **Environment**: AI Agent + Python Scripts + HWPX Templates

## Directory Structure

```
your-project-folder/
├── input/                    # PDF/PPT source documents + reference proposals
│   ├── reference/            # Reference HWPX for cover/TOC  
│   └── *.pdf, *.pptx        # RFP and presentation files
├── templates/                # Empty HWPX templates
│   └── my-template.hwpx
├── examples/                 # Configuration examples
│   ├── style_config_example.yaml
│   ├── inserts_example.json
│   └── example-content.md
├── output/                   # Generated HWPX files
├── scripts/                  # Python automation scripts
├── skills/                   # AI agent skill definitions
├── docs/                     # Technical documentation
│   └── knowhow/              # ★ Reverse-engineering knowledge base
├── workflows/                # Step-by-step workflow guides
└── AGENTS.md                 # This file
```

## ★ Mandatory Pre-Reading (Know-How Base)

**Before writing any HWPX-related code, the AI agent MUST read these documents:**

1. `docs/knowhow/style-remapper.md` — Style ID conflict resolution
2. `docs/knowhow/namespace-corruption.md` — lxml namespace prefix problem
3. `docs/knowhow/bullet-dedup.md` — Auto-bullet duplication prevention
4. `docs/knowhow/com-api-pitfalls.md` — Hancom COM API limitations
5. `docs/table-pagebreak.md` — Table page-breaking (3 conditions)
6. `docs/style-system.md` — charPrIDRef measured values
7. `docs/hwpx-format-guide.md` — HWPX internal structure

**Failure to read these documents will result in repeating known bugs.**

## AI Agent Rules

1. **Language**: Write all proposal content in Korean.
2. **Formatting**: Strictly maintain the HWPX template's formatting system.
3. **Tone**: Use formal Korean reporting style (명사/개조식: "~임", "~함", "~됨").
4. **Vague Expressions**: Forbid: "가능하다", "할 수 있다", "예정이다". Use affirmative expressions.
5. **No Duplicate Bullets**: Do NOT add bullet characters (□, ○, ―) inside text content — the HWPX style system automatically inserts them. Only □ (L0/Ctrl+1) should be typed directly.
6. **deepcopy + lineseg removal**: Always remove `<hp:linesegarray>` after deepcopy.
7. **Namespace fix required**: Always run `fix_namespaces.py` after any XML manipulation.
8. **Never use HwpxDocument.open()**: Use ZIP-level manipulation only.

## Workflow

To generate a proposal, the AI must follow this exact sequence:

### Standard Pipeline (All OS)

1. **Analyze RFP** — Extract evaluation criteria using `proposal-analyzer` skill or `extract_pdf.py`
2. **Design Structure** — Create chapter/section outline using `proposal-architect` skill
3. **Write Content** — Generate markdown draft (50K+ chars) using `proposal-writer` skill
4. **Review Content** — Self-audit against evaluation matrix using `proposal-reviewer` skill
5. **Analyze Template** — `python scripts/analyze_template.py my-template.hwpx`
6. **Convert to HWPX** — `python scripts/md_to_hwpx.py --template form.hwpx --md content.md --output result.hwpx`
7. **Fix Namespaces** — `python scripts/fix_namespaces.py result.hwpx` (⚠️ MANDATORY)
8. **Verify Output** — `python scripts/verify_hwpx.py result.hwpx`

### COM API Extension (Windows + Hancom only, Optional)

9. **Insert Visuals** — `python scripts/enhance_hwpx.py --input result.hwpx --output enhanced.hwpx --inserts inserts.json`
10. **Preview** — `python scripts/visualize_hwpx.py enhanced.hwpx preview.html`

## Configuration

Instead of hardcoding style IDs, use `examples/style_config_example.yaml` as a template:

```yaml
styles:
  H1: {styleIDRef: "10", paraPrIDRef: "3", charPrIDRef: "19"}
  H2: {styleIDRef: "8",  paraPrIDRef: "3", charPrIDRef: "18"}
  L1: {styleIDRef: "1",  paraPrIDRef: "11", charPrIDRef: "2"}
```

Discover correct values for your template using `analyze_template.py`.
