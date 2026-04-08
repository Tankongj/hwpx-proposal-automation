# Project Harness (AGENTS.md)

> This is a template for the AI project harness. Place this file in your root directory
> and instruct the AI to follow the rules defined here.

## Project Overview

- **Project**: [Your Project Name]
- **Goal**: [What you want to achieve]
- **Environment**: AI Agent + HWPX Proposal Automation Toolkit

## Directory Structure

```
your-project-folder/
├── 01_Reference_Material/   # PDF/PPT source documents
├── 02_RFP/                  # RFP and guidelines
├── 03_Templates/            # Empty HWPX templates
├── 04_Drafts/               # Generated markdown files
├── 05_Output/               # Final generated HWPX files
├── AGENTS.md                # This file
└── scripts/                 # (Copied from hwpx-proposal-automation)
```

## AI Agent Rules

1. **Language**: Write all proposal content in Korean.
2. **Formatting**: Strictly maintain the HWPX template's formatting tags (□, ○, ―, ·, ※).
3. **Tone**: Use formal Korean reporting style (명사/개조식: "~임", "~함", "~됨").
4. **Vague Expressions**: Forbid the use of "가능하다", "할 수 있다", "예정이다". Use affirmative expressions.
5. **No Duplicate Bullets**: Do NOT use actual bullet point characters inside the text. The markdown script uses `□, ○, ―` which maps to the template's Auto-Bullets.

## Workflow

To generate a proposal, the AI must follow this exact sequence:

1. Analyze RFP PDF using Python or `proposal-analyzer`.
2. Generate Proposal Structure (Markdown).
3. Generate Proposal Draft (Markdown).
4. Run `md_to_hwpx.py` to create HWPX.
5. Run `fix_namespaces.py` immediately.
6. Run `verify_hwpx.py` to check for errors.
