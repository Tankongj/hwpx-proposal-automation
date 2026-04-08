---
name: hwpx-proposal
description: HWPX 제안서 자동 생성 스킬. 마크다운 초안을 한컴오피스 HWPX 서식으로 변환하고 자동 검증을 수행합니다.
---

# HWPX Proposal Skill

PPT/PDF/마크다운 형태의 제안서 초안을 한컴오피스 HWPX 포맷으로 자동 변환하는 역할을 수행합니다.
내부적으로 `python-hwpx` 및 ZIP-level 치환 기술을 활용하여 템플릿의 스타일 손상 없이 데이터를 주입합니다.

## 핵심 기능

1. **템플릿 분석**: `analyze_template.py`를 사용하여 HWPX 템플릿 내부의 텍스트와 스타일 ID 목록을 추출합니다.
2. **MD 변환**: `md_to_hwpx.py`를 통해 정부 제안서 기호 체계(□, ○, ―, ※)에 맞게 마크다운 서식을 HWPX 단락으로 변환합니다.
3. **네임스페이스 복원**: 변환 과정에서 손상될 수 있는 XML 네임스페이스를 `fix_namespaces.py`를 통해 복구합니다.
4. **품질 검증**: `verify_hwpx.py`를 실행하여 구조 완전성 및 스타일 규정 준수 여부를 확인합니다.

## 사용 방법

에이전트는 사용자가 "제안서를 HWPX로 만들어줘" 형태의 요청을 할 때 아래 명령을 순차적으로 실행하여야 합니다.

### 1단계: 템플릿 분석 (필요 시)
```bash
python scripts/analyze_template.py templates/target_template.hwpx --output output/mapping.json
```

### 2단계: 변환 실행
```bash
python scripts/md_to_hwpx.py --template templates/target_template.hwpx --md draft.md --output output/final_proposal.hwpx
```

### 3단계: 필수 후처리
```bash
python scripts/fix_namespaces.py output/final_proposal.hwpx
```

### 4단계: 품질 검증
```bash
python scripts/verify_hwpx.py output/final_proposal.hwpx --type auto
```

## 주의 사항
- 변환 스크립트 실행 후 반드시 네임스페이스 복원 스크립트를 실행해야 합니다 (안 그러면 뷰어에서 빈 페이지로 나옴).
- 표(Table) 내부 변환 시 깨짐 방지를 위해 리스트 형태로 폴백(Fallback)될 수 있습니다.
- 스타일 매핑이 맞지 않으면 `md_to_hwpx.py` 내의 `STYLE_MAP` 딕셔너리를 해당 템플릿에 맞춰 수정해야 합니다.
