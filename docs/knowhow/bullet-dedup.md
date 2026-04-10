# 글머리표(Bullet) 중복 방지 — 자동 삽입 vs 수동 텍스트 충돌

## 1. 결론 (TL;DR)

- HWPX 스타일(Ctrl+2~6)은 글머리표(□, ❍, -, ·, *)를 **자동 삽입**한다.
- 마크다운/텍스트에 기호를 직접 넣으면 **"□ □ 대주제"** 처럼 이중으로 표시된다.
- `strip_auto_prefixes()` 함수로 텍스트의 기호 접두사를 레벨별로 제거해야 한다.
- **예외**: `□` (L0, Ctrl+1)만 텍스트에 직접 입력 — 이 레벨의 paraPr은 불릿 자동삽입 없음.

## 2. 문제 및 현상 (UI 분석)

### 정상

```
□ 사업 추진 배경
❍ 귀농귀촌 아카데미는 ...
- 교육 수료인원 14,000명
```

### 오류 (이중 불릿)

```
□ □ 사업 추진 배경        ← □가 두 번!
❍ ○ 귀농귀촌 아카데미는 ...  ← ❍와 ○ 중복!
- ― 교육 수료인원 14,000명  ← dash 중복!
```

### 한컴에서 확인

- `Ctrl+2` (본문 스타일): paraPr에 BULLET type=1 → `□` 자동 삽입
- `Ctrl+3` (개요 1 스타일): paraPr에 BULLET type=2 → `❍` 자동 삽입
- `Ctrl+4` (개요 2 스타일): paraPr에 BULLET type=3 → `-` 자동 삽입
- `Ctrl+5` (개요 3 스타일): paraPr에 BULLET type=4 → `·` 자동 삽입
- `Ctrl+6` (개요 4 스타일): paraPr에 BULLET type=5 → `*` 자동 삽입

## 3. 원인 분석 (XML 구조)

### header.xml의 paraPr 정의

```xml
<!-- paraPrIDRef=11 (Ctrl+2, L1) -->
<paraPr id="11">
  <paraHead type="BULLET" level="1" ... />  <!-- "□" 자동 생성 -->
</paraPr>

<!-- paraPrIDRef=12 (Ctrl+3, L2) -->
<paraPr id="12">
  <paraHead type="BULLET" level="2" ... />  <!-- "❍" 자동 생성 -->
</paraPr>
```

**핵심**: `paraHead` 요소가 있는 paraPr을 사용하면, 한컴은 텍스트 앞에 해당 불릿 기호를 자동으로 렌더링한다. 텍스트 자체에 기호가 있으면 이중으로 보인다.

### NUMBER 타입 (자동 번호)

```xml
<!-- paraPrIDRef=8 (Ctrl+8, H3) -->
<paraPr id="8">
  <paraHead type="NUMBER" level="2" format="N)" ... />  <!-- "1)", "2)" 자동 생성 -->
</paraPr>

<!-- paraPrIDRef=9 (Ctrl+7, H4) -->
<paraPr id="9">
  <paraHead type="NUMBER" level="3" format="(N)" ... />  <!-- "(1)", "(2)" 자동 생성 -->
</paraPr>
```

## 4. 해결 방안 (코드 스니펫)

### strip_auto_prefixes() 함수

```python
import re

def strip_auto_prefixes(paragraphs: list[dict]) -> list[dict]:
    """스타일 자동 불릿과 중복되는 텍스트 접두사를 레벨별로 제거한다."""
    
    # 각 레벨별 자동 삽입 기호에 대응하는 정규식
    PREFIX_PATTERNS = {
        'H3': re.compile(r'^\d+\)\s*'),           # "1) ", "2) " → 제거
        'H4': re.compile(r'^\(\d+\)\s*'),          # "(1) ", "(2) " → 제거
        'H5': re.compile(r'^[\u2460-\u2473]\s*'),  # "① ", "② " → 제거
        'L1': re.compile(r'^[□■]\s*'),             # "□ " → 제거
        'L2': re.compile(r'^[-\u2013\u2014]\s*'),  # "- ", "― " → 제거
    }
    
    result = []
    for para in paragraphs:
        ptype = para['type']
        text = para['text']
        
        pattern = PREFIX_PATTERNS.get(ptype)
        if pattern:
            text = pattern.sub('', text)
        
        result.append({**para, 'text': text})
    
    return result
```

### 마크다운 파싱 규칙

```markdown
# 올바른 마크다운 입력 (□만 직접 입력)
- □ 대주제 텍스트         → L0: "□ 대주제 텍스트" (□ 직접 입력)
- 중주제 텍스트            → L1: "중주제 텍스트" (❍ 자동 삽입)
- * 세부 내용              → L2: "세부 내용" (- 자동 삽입)

# 잘못된 마크다운 입력 (기호 직접 입력 → 중복!)
- ○ 중주제 텍스트          → ❌ "❍ ○ 중주제 텍스트"
- ― 세부 내용              → ❌ "- ― 세부 내용"
```

## 5. 주의사항

- 모든 한글 서식에서 동일한 BULLET/NUMBER 시스템을 사용하지만, **paraPrIDRef 번호는 서식마다 다르다**.
- `analyze_template.py`로 각 paraPr에 `paraHead`가 있는지 반드시 확인.
- v4 서식 기준 매핑 (다른 서식에서는 달라질 수 있음):

| paraPrIDRef | 자동 삽입 | 대응 레벨 |
|-------------|----------|----------|
| 8 | `N)` | H3 |
| 9 | `(N)` | H4 |
| 10 | `①②③` | H5 |
| 11 | `□` | L1 |
| 12 | `❍` | (Ctrl+3) |
| 13 | `-` | L2 |
| 14 | `·` | (Ctrl+5) |
| 15 | `*` | (Ctrl+6) |
