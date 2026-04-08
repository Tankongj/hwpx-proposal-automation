---
description: 제안서 작성 전체 프로세스를 순차적으로 수행하는 워크플로우 (PPT/PDF -> HWPX)
---

# Write Proposal Workflow

이 워크플로우는 AI 에이전트와 Python 스크립트가 협력하여 제안서를 자동 생성하는 표준 파이프라인입니다.

## Step 1. 제안요청서(RFP) 분석
- `proposal-analyzer` 스킬을 사용하여 제공된 RFP 또는 평가 기준 문서를 분석합니다.
- 평가 매트릭스와 작성 제약 사항이 포함된 `rfp_analysis.md`를 생성합니다.

## Step 2. 사업계획서/제안서 구조 설계
- `proposal-architect` 스킬을 사용하여 목차와 분량 배분을 기획합니다.
- 평가 매트릭스를 기반으로 `proposal_structure.md`를 생성합니다.

## Step 3. 콘텐츠 초안 작성 (Markdown)
- `proposal-writer` 스킬을 사용하여 개조식 텍스트 기반의 본문을 작성합니다.
- `proposal_draft.md` 파일로 저장합니다. 템플릿의 기호(□, ○, 등)를 반드시 준수해야 합니다.

## Step 4. 품질 검토 및 교정
- `proposal-reviewer` 스킬을 사용하여 7-Dimension 검토를 수행합니다.
- 문제가 있다면 `proposal_draft.md`를 즉시 수정합니다.

## Step 5. HWPX 변환 (Python Script)
// turbo-all
- 작성된 마크다운을 HWPX 포맷으로 변환합니다.
- 실행할 명령:
  `python scripts/md_to_hwpx.py --template templates/your_template.hwpx --md proposal_draft.md --output result.hwpx`

## Step 6. 네임스페이스 후처리 (Python Script)
- 변환된 HWPX의 깨진 XML을 복원합니다.
- 실행할 명령:
  `python scripts/fix_namespaces.py result.hwpx`

## Step 7. 자가 검증 (Python Script)
- 최종 문서가 정상적인지 확인합니다.
- 실행할 명령:
  `python scripts/verify_hwpx.py result.hwpx --type auto`
