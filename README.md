<div align="center">

# 📄 HWPX Proposal Automation

**한글(HWPX) 제안서 자동 생성 도구 — PPT/PDF → 마크다운 → HWPX**

HWPX (한컴오피스 한글) 포맷의 정부·공공기관 제안서를 **파이썬 스크립트로 자동 생성**합니다.

[빠른 시작](#-빠른-시작-5분-가이드) · [상세 사용법](#-상세-사용법) · [역공학 기술 문서](#-역공학-기술-문서) · [FAQ](#-자주-묻는-질문)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

</div>

---

## 📖 이게 뭔가요?

### 한 줄 요약

> **PPT 제안서에서 텍스트를 추출하고, AI가 마크다운 초안을 만들고, 한글 양식(`.hwpx`)에 자동 주입하는 도구**입니다.

### 왜 필요한가요?

한국의 정부·공공기관 입찰 제안서는 반드시 `.hwpx` (한컴오피스 한글) 포맷으로 제출해야 합니다.
하지만:

- PPT로 제안 내용을 만든 후 **한글로 옮기면 서식이 다 깨지고**
- 한글 양식에 맞춰 **글꼴·크기·들여쓰기를 하나하나 맞추는 건 지옥**이고
- 매번 같은 양식에 내용만 바꿔 넣는 **반복 노동이 많습니다**

이 도구는 그 전체 과정을 **자동화**합니다:

```
📊 PPT 제안서  →  🔄 텍스트 추출  →  🤖 AI 마크다운 초안  →  📄 완성된 .hwpx 제안서
```

### 누가 쓰면 좋나요?

- ✅ 정부·지자체 용역 제안서를 자주 쓰는 **기업/기관 담당자**
- ✅ 제안서 자동화에 관심 있는 **개발자**
- ✅ AI 에이전트로 제안서를 만들고 싶은 **테크 스타트업**
- ✅ HWPX 포맷을 프로그래밍으로 다루고 싶은 **한컴 생태계 개발자**

---

## ⚡ 빠른 시작 (5분 가이드)

### Step 0: 설치

```bash
# 1. 저장소 다운로드
git clone https://github.com/Tankongj/hwpx-proposal-automation.git
cd hwpx-proposal-automation

# 2. (권장) 가상환경 생성
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 3. 필수 패키지 설치
pip install -r requirements.txt
```

> **💡 파이썬이 없다면?** [python.org](https://www.python.org/downloads/)에서 Python 3.9 이상을 설치하세요.

### Step 1: 재료 준비

두 가지 파일을 준비합니다:

```
input/
└── my-presentation.pptx   ← ① PPT 제안서 (내용이 담긴 원본)

templates/
└── my-template.hwpx       ← ② 빈 한글 양식 (서식만 있는 빈 템플릿)
```

> **💡 양식이 없다면?** 한컴 한글에서 `파일 → 새 문서 → 빈 문서`로 만들어 `.hwpx`로 저장하세요.

### Step 2: PPT에서 텍스트 추출

PPT 제안서의 텍스트와 표 구조를 자동으로 추출합니다:

```bash
python scripts/extract_ppt.py input/my-presentation.pptx
```

이렇게 하면 슬라이드별 텍스트가 추출됩니다. 이 추출한 내용을 바탕으로 **AI 에이전트(Gemini, Claude 등)가 마크다운 초안을 자동 생성**합니다.

> **💡 AI 없이도 가능합니다.** 추출된 텍스트를 직접 마크다운으로 정리해도 됩니다.

### Step 3: 마크다운 초안 확인

AI가 생성하거나 직접 정리한 마크다운 초안을 확인합니다. `examples/example-content.md`를 참고하세요.

```markdown
# Ⅰ. 사업 이해

## 1. 추진 배경 및 필요성

□ 사업 추진 배경
- 정부의 귀농귀촌 지원 정책 확대에 따른 교육 수요 급증
  * 2025년 귀농가구 수 전년 대비 12% 증가
  * 귀촌 희망자 대상 사전 교육 매우 중요
- 기존 교육 프로그램의 한계
  * 대면 교육 비중이 22%에 불과

## 2. 사업 목표

□ 핵심 성과 지표 (KPI)
- 교육 수료 인원: 14,000명 이상
- 교육 만족도: 90점 이상

※ 상기 KPI는 RFP에 명시된 필수 달성 목표임
```

**마크다운 기호 규칙:**

| 기호 | 의미 | 예시 |
|------|------|------|
| `# 제목` | 장(Chapter) 제목 | `# Ⅰ. 사업 이해` |
| `## 제목` | 절(Section) 제목 | `## 1. 추진 배경` |
| `### 제목` | 소절 제목 | `### 가. 현황 분석` |
| `□` | 대주제 | `□ 사업 추진 배경` |
| `-` | 중주제 | `- 세부 내용` |
| `*` | 소주제 | `* 더 세부적인 내용` |
| `※` | 참고/주석 | `※ 출처: 통계청 2025` |

### Step 4: 변환 실행 (3줄이면 끝!)

```bash
# 1️⃣ 마크다운 → HWPX 변환
python scripts/md_to_hwpx.py \
  --template templates/my-template.hwpx \
  --md my-draft.md \
  --output output/result.hwpx

# 2️⃣ 네임스페이스 수정 (필수! 이거 안 하면 한글에서 빈 페이지로 보임)
python scripts/fix_namespaces.py output/result.hwpx

# 3️⃣ 결과 검증 (선택, 하지만 강력 권장)
python scripts/verify_hwpx.py output/result.hwpx
```

끝! `output/result.hwpx`를 한컴오피스 한글로 열어보세요. 🎉

---

## 📚 상세 사용법

### 🔍 1단계: 템플릿 분석하기

한글 양식마다 스타일 ID가 다릅니다. 내 양식의 ID를 먼저 알아야 합니다:

```bash
python scripts/analyze_template.py templates/my-template.hwpx
```

출력 예시:
```
📋 Template Analysis: my-template.hwpx
  File size: 45,230 bytes
  Sections: 1

  charPr Table (header.xml):
    ID  0: font=한양신명조  size=10pt
    ID  2: font=휴먼명조    size=15pt  ← 본문용
    ID 19: font=HY견고딕    size=18pt  ← 제목용
    ...
```

### ⚙️ 2단계: 스타일 설정 (선택)

기본값으로도 동작하지만, 양식에 맞는 정확한 스타일을 지정하고 싶다면 YAML 설정 파일을 만듭니다:

```bash
# 예시 파일을 복사해서 커스터마이즈
cp examples/style_config_example.yaml my-config.yaml
```

`my-config.yaml` 수정:
```yaml
styles:
  H1:  {styleIDRef: "10", paraPrIDRef: "3",  charPrIDRef: "19"}  # 장 제목
  H2:  {styleIDRef: "8",  paraPrIDRef: "3",  charPrIDRef: "18"}  # 절 제목
  L1:  {styleIDRef: "1",  paraPrIDRef: "11", charPrIDRef: "2"}   # 본문 항목
  L2:  {styleIDRef: "3",  paraPrIDRef: "13", charPrIDRef: "22"}  # 하위 항목
```

> **💡 ID 값은 어디서 찾나요?** 위의 `analyze_template.py` 출력 결과에서 확인하세요.

변환 시 설정 파일 적용:
```bash
python scripts/md_to_hwpx.py \
  --template templates/my-template.hwpx \
  --md my-draft.md \
  --output output/result.hwpx \
  --config my-config.yaml
```

### 📋 3단계: 레퍼런스 문서에서 표지/목차 가져오기 (선택)

기존 제안서의 표지·목차·조견표를 새 문서에 안전하게 이식할 수 있습니다:

```bash
python scripts/md_to_hwpx.py \
  --template templates/my-template.hwpx \
  --md my-draft.md \
  --output output/result.hwpx \
  --reference input/previous-proposal.hwpx \
  --cover-range 0:20 \
  --toc-range 20:69
```

| 옵션 | 설명 |
|------|------|
| `--reference` | 표지/목차를 가져올 기존 제안서 파일 |
| `--cover-range 0:20` | 표지 영역 (0~19번째 문단) |
| `--toc-range 20:69` | 목차 영역 (20~68번째 문단) |
| `--summary-range 69:163` | 조견표 영역 (69~162번째 문단) |

> **💡 문단 범위는 어떻게 아나요?** `analyze_template.py`를 레퍼런스 문서에 대해 실행하면 각 문단의 텍스트와 인덱스가 출력됩니다.

> **⚠️ 이 기능은 내부적으로 [Style Remapper](docs/knowhow/style-remapper.md)를 사용**합니다. 레퍼런스와 템플릿의 스타일 ID가 달라도 자동으로 충돌 없이 매핑합니다.

### 🔧 4단계: 네임스페이스 수정 (필수)

`md_to_hwpx.py` 실행 후 **반드시** 이 명령을 실행해야 합니다:

```bash
# 기본 수정
python scripts/fix_namespaces.py output/result.hwpx

# 표(Table) 페이지 넘김도 수정하려면:
python scripts/fix_namespaces.py output/result.hwpx --fix-tables
```

> **❓ 왜 필수인가요?** 파이썬의 XML 라이브러리(lxml)가 `<ns0:p>` 같은 이상한 태그를 만들어서 한컴 한글이 읽지 못합니다. 이 스크립트가 정상적인 `<hp:p>` 태그로 복원합니다. ([상세 원인 보기](docs/knowhow/namespace-corruption.md))

### ✅ 5단계: 자동 검증

수십 페이지 제안서의 품질을 5초 만에 검증합니다:

```bash
# 정성제안서 (기호 체계, 문체, 페이지 수 검증)
python scripts/verify_hwpx.py output/result.hwpx --type qualitative

# 정량제안서 (표 채움률, 이력서 섹션, 회사 키워드 검증)
python scripts/verify_hwpx.py output/result.hwpx --type quantitative --company-keywords "우리회사" "대표이름"
```

출력 예시:
```
============================================================
📋 HWPX Self-Verification System
   File: result.hwpx
   Size: 128,450 bytes
   Type: qualitative
============================================================
──────────────────────────────────────────────────────
Item                           Result   Detail
──────────────────────────────────────────────────────
File Structure                    ✅   section=True, header=True, hpf=True
content.hpf Integrity             ✅   sections=1, all referenced
Date Fields                       ✅   Date placeholder: none ✅
Namespace Pollution               ✅   No namespace pollution found ✅
Table treatAsChar                 ✅   treatAsChar=0: 5, treatAsChar=1: 0 ✅
Chapter Structure (Ⅰ~Ⅳ)          ✅   Chapters found: ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ']
Symbol System (□○―※)             ✅   □=45, ○=89, ―=120, ※=15
Writing Style                     ✅   Formal endings: 340, vague expressions: 2

📊 Summary: 8/8 passed (100%)
🏆 Status: Excellent — Ready to submit
```

### 🖼️ 6단계: 이미지/표 삽입 (선택, Windows 전용)

한컴오피스가 설치된 Windows에서만 사용 가능합니다. 차트 이미지나 데이터 표를 자동 삽입합니다:

```bash
# 먼저 pywin32 설치
pip install pywin32

# 삽입할 내용을 JSON으로 정의
# (examples/inserts_example.json 참고)

# 실행
python scripts/enhance_hwpx.py \
  --input output/result.hwpx \
  --output output/enhanced.hwpx \
  --inserts my-inserts.json
```

`my-inserts.json` 예시:
```json
{
  "images": [
    {
      "anchor": "사업추진 조직 체계",
      "path": "charts/org-chart.png",
      "width_mm": 155
    }
  ],
  "tables": [
    {
      "anchor": "주요 KPI",
      "headers": ["지표", "목표", "방법"],
      "rows": [
        ["수료인원", "14,000명", "교육 수료 기준"]
      ]
    }
  ]
}
```

> **⚠️ 이 기능은 한컴오피스 한글이 설치되어 있어야 합니다.** 한글의 COM API를 사용하여 실제 프로그램을 자동 제어합니다.

### 👀 7단계: HTML 미리보기 (선택)

한글 없이도 변환 결과를 브라우저에서 확인할 수 있습니다:

```bash
python scripts/visualize_hwpx.py output/result.hwpx preview.html "내 제안서"
```

`preview.html`을 브라우저로 열면 각 문단의 폰트, 크기, 스타일 ID가 표시됩니다.

---

## 🏗️ 전체 파이프라인 흐름

```
  ╔══════════════════════════════════════════════════════════════╗
  ║              전체 워크플로우 (Data Flow)                     ║
  ╚══════════════════════════════════════════════════════════════╝

  [입력]                       [처리]                      [출력]
  ─────                       ──────                      ──────

  📊 PPT 제안서 ──→ extract_ppt.py ──→ 슬라이드별 텍스트/표
                                          │
  📄 PDF 공고문 ──→ extract_pdf.py ──→ RFP 평가항목 분석
                                          │
                                          ▼
                              🤖 AI 에이전트 (또는 수동)
                              ┌──────────────────────┐
                              │ proposal-analyzer     │ RFP 분석
                              │ proposal-architect    │ 구조 설계
                              │ proposal-writer       │ 콘텐츠 작성
                              │ proposal-reviewer     │ 품질 검토
                              └──────────┬───────────┘
                                         │
                                         ▼
                                  📝 마크다운 초안 (.md)
                                         │
  📋 HWPX 양식 ──→ analyze_template ──→ 스타일 ID 매핑
       │                                  │
       └──────────────┬───────────────────┘
                      ▼
                md_to_hwpx.py ──→ 변환된 HWPX (미완성)
                      │
                      ▼
                fix_namespaces.py ──→ 네임스페이스 수정
                      │
                      ▼
                verify_hwpx.py ──→ 자동 품질 검증
                      │
                      ▼
             (선택) enhance_hwpx.py ──→ 이미지/표 삽입
                      │
                      ▼
                 ✅ 최종 .hwpx 제안서
```

---

## 📁 프로젝트 구조

```
hwpx-proposal-automation/
│
├── 📄 README.md                 ← 지금 읽고 있는 이 문서
├── 📄 AGENTS.md                 ← AI 에이전트 작업 규칙
├── 📄 requirements.txt          ← 파이썬 패키지 목록
├── 📄 .gitignore
│
├── 🔧 scripts/                  ← 핵심 파이썬 스크립트
│   ├── analyze_template.py      ← 양식의 스타일 ID 분석
│   ├── md_to_hwpx.py            ← ★ 마크다운 → HWPX 변환기 (핵심!)
│   ├── fix_namespaces.py        ← XML 네임스페이스 복원 (필수 후처리)
│   ├── verify_hwpx.py           ← 결과물 자동 검증 (11개 검사 항목)
│   ├── enhance_hwpx.py          ← COM API로 이미지/표 삽입 (Windows 전용)
│   ├── visualize_hwpx.py        ← HWPX → HTML 미리보기
│   ├── generate_charts.py       ← matplotlib 차트 자동 생성
│   ├── write_hwpx.py            ← ZIP 레벨 텍스트 치환
│   ├── extract_pdf.py           ← PDF 텍스트 추출
│   ├── extract_ppt.py           ← PPT 슬라이드/표 추출
│   └── hwpx_editor/             ← 고급 HWPX 편집 API
│       ├── _parser.py           ← XML 문자열 파서
│       ├── table_fixer.py       ← 표 구조 자동 보정
│       └── modify_hwpx.py       ← 안전한 텍스트/문단 교체
│
├── 🤖 skills/                   ← AI 에이전트 스킬 정의
│   ├── hwpx-proposal/           ← HWPX 문서 생성 스킬
│   ├── proposal-analyzer/       ← RFP 분석 스킬
│   ├── proposal-architect/      ← 구조 설계 스킬
│   ├── proposal-writer/         ← 콘텐츠 작성 스킬
│   └── proposal-reviewer/       ← 7차원 품질 검토 스킬
│
├── 📖 docs/                     ← 기술 문서
│   ├── architecture.md          ← 시스템 아키텍처
│   ├── hwpx-format-guide.md     ← HWPX 포맷 가이드 (역공학)
│   ├── style-system.md          ← ★ 스타일 ID 매핑 + 절대규칙 8가지
│   ├── table-pagebreak.md       ← ★ 표 페이지 넘김 3조건 해결법
│   ├── knowhow-management-rules.md  ← 지식 기여 가이드라인
│   ├── knowhow/                 ← ★ 역공학 지식 베이스
│   │   ├── style-remapper.md    ← 스타일 ID 충돌 방지 기술
│   │   ├── namespace-corruption.md  ← 빈 페이지 문제 해결
│   │   ├── bullet-dedup.md      ← 글머리표 중복 방지
│   │   └── com-api-pitfalls.md  ← 한글 COM API 주의사항
│   └── troubleshooting.md       ← 문제 해결 가이드
│
├── 📂 examples/                 ← 설정 파일 및 사용 예시
│   ├── style_config_example.yaml  ← YAML 스타일 설정 예시
│   ├── inserts_example.json     ← COM API 삽입 매핑 예시
│   └── example-content.md       ← 마크다운 입력 예시
│
├── 📂 workflows/                ← 워크플로우 문서
│   └── write-proposal.md       ← 전체 프로세스 안내
│
└── 📂 templates/                ← 한글 양식 파일 보관
    └── (여기에 .hwpx 넣기)
```

---

## 🔬 역공학 기술 문서

이 프로젝트에서 발견한 **공식 문서에 없는** 핵심 기술들입니다.
53회 이상의 반복 시행착오와 실측을 통해 검증되었습니다.

### 핵심 발견사항 요약

| 발견 | 핵심 내용 | 상세 문서 |
|------|----------|----------|
| **스타일 ID 충돌** | 레퍼런스 문서의 스타일을 이식하면 글꼴이 깨짐 → `max_id+1` 방식으로 새 ID 할당 | [style-remapper.md](docs/knowhow/style-remapper.md) |
| **빈 페이지 문제** | lxml이 `<ns0:p>` 접두사를 추가 → 한글이 파싱 실패 → 정규식 제거 필수 | [namespace-corruption.md](docs/knowhow/namespace-corruption.md) |
| **글머리표 중복** | `□ □ 대주제` 이중 표시 → 스타일 자동 불릿과 텍스트 기호가 겹침 | [bullet-dedup.md](docs/knowhow/bullet-dedup.md) |
| **표 페이지 넘김** | `pos.treatAsChar="0"`이 핵심 — `tbl.textWrap`만으로는 부족 | [table-pagebreak.md](docs/table-pagebreak.md) |
| **COM API 한계** | `FindWordByWord`는 유효하지 않은 속성, `TreatAsChar`는 pos를 안 바꿈 | [com-api-pitfalls.md](docs/knowhow/com-api-pitfalls.md) |
| **charPrIDRef 실측값** | `63=20pt 휴먼명조`, `64=18pt HY견고딕` 등 — header.xml에서만 확인 가능 | [style-system.md](docs/style-system.md) |

### charPrIDRef 실측값 테이블 (v4 서식 기준)

```
charPrIDRef  크기    폰트        용도
───────────  ────    ────        ────
63           20pt    휴먼명조     장 제목, □ 대주제
64           18pt    HY견고딕    절 제목
65           15pt    휴먼명조     ❍ 중주제
66           15pt    휴먼명조     - 세부, · 상세
67           13pt    한양중고딕   * 참고/주석
```

> ⚠️ 이 값들은 서식(양식)마다 다릅니다! 반드시 `analyze_template.py`로 확인하세요.

---

## 🤖 AI 에이전트와 함께 쓰기

이 저장소의 `skills/` 디렉토리를 AI 코딩 에이전트(Gemini, Claude, ChatGPT 등)에 연결하면,
**제안서 분석 → 구조 설계 → 콘텐츠 작성 → HWPX 변환**까지 전 과정을 자동화할 수 있습니다.

```
AI Skill 체인:
  proposal-analyzer → proposal-architect → proposal-writer → proposal-reviewer → hwpx-proposal
  (RFP 분석)         (구조 설계)          (콘텐츠 작성)      (품질 검토)         (HWPX 변환)
```

자세한 AI 에이전트 규칙은 [AGENTS.md](AGENTS.md)를 참고하세요.

---

## ❓ 자주 묻는 질문

<details>
<summary><b>Q: 한컴오피스 한글이 설치되어 있어야 하나요?</b></summary>

**A: 아닙니다!** 핵심 기능(마크다운→HWPX 변환)은 순수 파이썬으로 동작하므로 Windows, macOS, Linux 어디서든 사용할 수 있습니다. 한컴오피스는 **결과물을 열어볼 때**만 필요합니다.

단, `enhance_hwpx.py`(이미지/표 삽입)는 Windows + 한컴오피스가 필요합니다.
</details>

<details>
<summary><b>Q: 변환 후 한글로 열었는데 빈 페이지만 보입니다</b></summary>

**A: `fix_namespaces.py`를 실행하셨나요?** 이 후처리를 빠뜨리면 한글이 XML을 읽지 못해 빈 페이지가 표시됩니다.

```bash
python scripts/fix_namespaces.py output/result.hwpx
```

원인: [docs/knowhow/namespace-corruption.md](docs/knowhow/namespace-corruption.md)
</details>

<details>
<summary><b>Q: 표가 페이지를 넘어가지 않고 잘립니다</b></summary>

**A: `--fix-tables` 옵션으로 표 속성을 수정하세요:**

```bash
python scripts/fix_namespaces.py output/result.hwpx --fix-tables
```

이 옵션은 `pos.treatAsChar`를 `0`으로 변경합니다.
원인: [docs/table-pagebreak.md](docs/table-pagebreak.md)
</details>

<details>
<summary><b>Q: □가 두 번 표시됩니다 (□ □ 대주제)</b></summary>

**A: 자동 글머리표 중복 문제입니다.** HWPX 스타일이 자동으로 `□`를 삽입하는데, 텍스트에도 `□`가 있으면 중복됩니다.

해결: 마크다운에서 기호를 빼거나, `strip_auto_prefixes()` 기능이 자동으로 처리합니다.
상세: [docs/knowhow/bullet-dedup.md](docs/knowhow/bullet-dedup.md)
</details>

<details>
<summary><b>Q: 내 양식의 스타일 ID를 어떻게 알 수 있나요?</b></summary>

**A: `analyze_template.py`를 사용하세요:**

```bash
python scripts/analyze_template.py templates/my-template.hwpx
```

각 charPrIDRef의 폰트, 크기, 볼드 여부가 출력됩니다.
</details>

<details>
<summary><b>Q: pip install에서 에러가 납니다</b></summary>

**A: Python 버전을 확인하세요:**

```bash
python --version    # 3.9 이상이어야 합니다
pip install --upgrade pip
pip install lxml pdfplumber PyYAML
```

Windows에서 lxml 설치 오류 시:
```bash
pip install lxml --only-binary=:all:
```
</details>

---

## 🤝 기여하기

기여를 환영합니다! 특히 **지식 기여(Knowledge Contribution)**를 매우 환영합니다.

### 코드 기여

1. Fork → 2. Branch 생성 → 3. Commit → 4. Push → 5. Pull Request

### 지식 기여 (역공학 노하우)

HWPX 개발하면서 새로 발견한 동작 원리나 버그 우회법이 있다면, [3-Step Rule](docs/knowhow-management-rules.md) 형식으로 `docs/knowhow/` 폴더에 문서를 추가해 주세요:

1. **현상 분석** (UI에서 뭐가 보이는지)
2. **원인 규명** (XML 구조에서 왜 그런지)
3. **해결 코드** (파이썬으로 어떻게 고치는지)

---

## 📜 라이선스

MIT License — [LICENSE](LICENSE) 파일 참조

---

## 🙏 감사

- **HWPX/OWPML 표준** — KS X 6101 (한국 개방형 문서 표준)
- **python-hwpx** — HWPX 파일 구조 핸들링 라이브러리
- **python-pptx** — PPT 추출 표준 라이브러리
- **hwpilot & hwpxskill** — 외부 HWPX 편집 도구
- **Antigravity** — 이 시스템을 설계하고 반복 개선한 AI 코딩 에이전트

---

<div align="center">

Made with 🌾 for the Korean public sector

**[⬆ 맨 위로](#-hwpx-proposal-automation)**

</div>
