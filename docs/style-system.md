# Style System — HWPX 스타일 ID 매핑 가이드

> ⚠️ `charPrIDRef`는 header.xml의 실제 폰트/크기 정의를 참조하므로
> **반드시 `analyze_template.py`로 실측값을 확인**한 후 사용해야 합니다.
>
> 아래 값들은 **v4 서식** 기준입니다. 다른 서식에서는 값이 다를 수 있습니다.

## 1. charPrIDRef 실측값 (v4 style header.xml)

| charPrIDRef | height (pt) | fontRef hangul | 폰트명 | 용도 |
|---|---|---|---|---|
| 13 | 10pt | 14 | 한양신명조 | 기본 (**사용 금지 — 잘못된 폰트**) |
| 30 | 10pt | 14 | 한양신명조 | 바탕글 기본 (**❌ L0에 사용 금지**) |
| 48 | 12pt | 7 | 휴먼명조 | 표지 |
| 57 | 20pt | 14 | 한양신명조 | — |
| **63** | **20pt** | **7** | **휴먼명조** | **장 제목, □ L0** |
| **64** | **18pt** | **8** | **HY견고딕** | **절 제목** |
| **65** | **15pt** | **7** | **휴먼명조** | **❍ L1** |
| **66** | **15pt** | **7** | **휴먼명조** | **- L2, · L3** |
| **67** | **13pt** | **15** | **한양중고딕** | **\* L4** |

## 2. 11단계 스타일 체계 (v4 서식)

| 레벨 | 설명 | styleIDRef | paraPrIDRef | charPrIDRef | 폰트 | 크기 | 단축키 |
|---|---|---|---|---|---|---|---|
| chapter | 장 제목 (Ⅰ~Ⅴ) | 16 | 66 | **63** | 휴먼명조 | 20pt | — |
| section | 절 제목 (1~9) | 153 | 67 | **64** | HY견고딕 | 18pt | — |
| L0 | □ 대주제 | 0 (바탕글) | 9 | **63** | 휴먼명조 | 20pt\* | Ctrl+1 |
| L1 | ❍ 중주제 | 1 (본문) | 68 | **65** | 휴먼명조 | 15pt | Ctrl+2 |
| L2 | - 세부 | 2 (개요 1) | 69 | **66** | 휴먼명조 | 15pt | Ctrl+3 |
| L3 | · 상세 | 3 (개요 2) | 70 | **66** | 휴먼명조 | 15pt | Ctrl+4 |
| L4 | \* 참고 | 4 (개요 3) | 71 | **67** | 한양중고딕 | 13pt | Ctrl+5 |

> \*L0의 charPr[63]은 20pt이나, styleIDRef=0 (바탕글)이 실제 크기를 18pt로 override함

## 3. 폰트 테이블 (hangul fontRef → face)

| fontRef ID | face | 용도 |
|---|---|---|
| 7 | 휴먼명조 | 본문, 장제목 |
| 8 | HY견고딕 | 절 제목 |
| 10 | HY중고딕 | — |
| 14 | 한양신명조 | 기본값 (사용 금지) |
| 15 | 한양중고딕 | 참고/주석 |

## 4. 절 제목 번호 박스 구조

절 제목은 `<hp:tbl>` (3셀 1행 테이블)로 구현됨:

```xml
<hp:tbl treatAsChar="1" ...>
  <hp:tr>
    <hp:tc borderFillIDRef="14">  <!-- 셀0: 번호 (파란 배경) -->
      <hp:subList><hp:p><hp:run><hp:t>1</hp:t></hp:run></hp:p></hp:subList>
    </hp:tc>
    <hp:tc borderFillIDRef="15">  <!-- 셀1: 구분선 (빈 셀) -->
      <hp:subList><hp:p><hp:run><hp:t/></hp:run></hp:p></hp:subList>
    </hp:tc>
    <hp:tc borderFillIDRef="16">  <!-- 셀2: 제목 텍스트 -->
      <hp:subList><hp:p><hp:run><hp:t> 추진배경 및 필요성</hp:t></hp:run></hp:p></hp:subList>
    </hp:tc>
  </hp:tr>
</hp:tbl>
```

생성 방법: 템플릿의 section0.xml에서 해당 paragraph를 `deepcopy`하고, 셀0(번호)과 셀2(제목)의 `<hp:t>` 텍스트만 교체.

## 5. 절대 규칙 8가지

1. **서식 파라 deepcopy 방식만 사용** — styleIDRef 직접 지정으로 새 파라를 만들면 불완전한 구조가 됨
2. **deepcopy 직후 linesegarray 전부 제거** — 장평/자간 캐시가 남아 글자 깨짐 유발
3. **deepcopy 직후 fix_style()로 charPrIDRef 교정** — 템플릿 기본값(13)은 잘못된 폰트(한양신명조 10pt)
4. **pageBreak는 chapter만 =1** — 나머지는 반드시 =0 (의도치 않은 페이지 분리 방지)
5. **절 제목은 3셀 테이블** — 번호/텍스트만 교체 (구조 변경 금지)
6. **XML 직렬화 후 ns접두사 정규식 제거** — `<ns0:` → `<` (한컴 파싱 실패 방지)
7. **기존 paras 전부 제거** 후 새 콘텐츠 주입 — 잔여 paragraph 혼재 방지
8. **글머리표 중복 금지** — 스타일 불릿(❍/-/·/\*)이 자동 삽입되므로 텍스트에 기호 직접 입력 금지. □만 직접 입력

## 6. 실패 사례 (반복 금지)

### 6.1 charPrIDRef=30 사용 → □ 글꼴/크기 오류

```python
# ❌ 실패: charPr[30] = 10pt 한양신명조 → □가 작게 표시
run.set('charPrIDRef', '30')

# ✅ 성공: charPr[63] = 20pt 휴먼명조
run.set('charPrIDRef', '63')
```

### 6.2 네이티브 표(`<hp:tbl>`) 직접 생성 → 파싱 실패

```python
# ❌ 실패: <hp:tc> 안에 <hp:subList> 없이 <hp:p>를 직접 넣으면 한컴 파싱 실패
# 필수 구조: tc → subList → p → run → t
# 안전 대안: 표 내용을 L1/L2 리스트 형태로 변환
```

### 6.3 이미지(`<hp:pic>`) 삽입 시 header.xml binData 미등록

```
# ❌: BinData에 이미지 파일만 추가하고 header.xml에 binDataItem 미등록
# → 한컴이 이미지를 인식하지 못함
# 안전 대안: [IMG] 참조 텍스트로 위치만 표시, COM API로 수동 삽입
```

### 6.4 linesegarray 미제거 → 글자 장평/자간 이상

```python
# deepcopy 직후 즉시:
for ls in list(elem.iter('{ns}linesegarray')):
    ls.getparent().remove(ls)
```

## 7. 스타일 분석 방법

```bash
# 템플릿의 모든 charPr 정의 확인
python scripts/analyze_template.py my-template.hwpx

# 시각적 스타일 확인 (HTML 렌더링)
python scripts/visualize_hwpx.py my-template.hwpx preview.html
```
