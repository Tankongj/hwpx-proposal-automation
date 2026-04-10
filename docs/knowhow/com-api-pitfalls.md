# 한글 COM API (HWPFrame.HwpObject) — 검증된 기능과 주의사항

## 1. 결론 (TL;DR)

- 한글 COM API는 표·이미지 삽입, 텍스트 검색·삽입에 유용하지만 **XML 속성 제어에 한계**가 있다.
- `TreatAsChar = False`는 `tbl.textWrap`만 변경하고 **`pos.treatAsChar`는 미변경** — 표 페이지 넘김은 XML 직접 수정이 유일한 해결책.
- `HFindReplace.FindWordByWord`는 **유효하지 않은 속성**으로 `AttributeError` 발생.
- 이미지 크기 단위: **1mm = 283.46 HWP units**.

## 2. 환경 요건

```
- Windows 10/11
- 한컴오피스 한글 정품 설치 (2024+)
- Python 3.9+ + pywin32 (`pip install pywin32`)
```

## 3. ✅ 검증 완료된 기능

### 3.1 COM 객체 연결

```python
import win32com.client

hwp = win32com.client.gencache.EnsureDispatch('HWPFrame.HwpObject')
hwp.XHwpWindows.Item(0).Visible = True  # 화면 표시

# 보안 모듈 (일부 환경에서 필요)
try:
    hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
except:
    pass  # 최신 한글에서는 불필요
```

### 3.2 표 삽입 (InsertTable) ✅

```python
hwp.HAction.GetDefault('InsertTable', hwp.HParameterSet.HTableCreation.HSet)
hwp.HParameterSet.HTableCreation.Rows = 3
hwp.HParameterSet.HTableCreation.Cols = 4
hwp.HParameterSet.HTableCreation.WidthType = 2  # 페이지 기준
hwp.HAction.Execute('InsertTable', hwp.HParameterSet.HTableCreation.HSet)
```

### 3.3 이미지 삽입 (InsertPicture) ✅

```python
import os

hwp.HAction.GetDefault('InsertPicture', hwp.HParameterSet.HInsertPicture.HSet)
hwp.HParameterSet.HInsertPicture.FileName = os.path.abspath('chart.png')
hwp.HParameterSet.HInsertPicture.Width = int(150 * 283.46)  # 150mm
hwp.HParameterSet.HInsertPicture.Height = 0          # 비율 유지
hwp.HParameterSet.HInsertPicture.SizeConstraint = 1   # 가로 기준
hwp.HAction.Execute('InsertPicture', hwp.HParameterSet.HInsertPicture.HSet)
```

> **크기 단위**: 1mm = 283.46 HWP units (HWPUNIT)

### 3.4 텍스트 검색 (RepeatFind) ✅

```python
hwp.HAction.GetDefault('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)
hwp.HParameterSet.HFindReplace.FindString = '검색할 텍스트'
hwp.HParameterSet.HFindReplace.FindRegExp = 0
hwp.HParameterSet.HFindReplace.Direction = 0  # Forward
found = hwp.HAction.Execute('RepeatFind', hwp.HParameterSet.HFindReplace.HSet)
```

### 3.5 커서 이동/텍스트 삽입 ✅

```python
hwp.HAction.Run('MoveDocBegin')    # 문서 처음
hwp.HAction.Run('MoveLineEnd')     # 줄 끝
hwp.HAction.Run('BreakPara')       # Enter (새 문단)
hwp.HAction.Run('TableRightCell')  # 표 다음 셀
hwp.HAction.Run('CloseEx')         # 표 밖으로

# 텍스트 삽입
hwp.HAction.GetDefault('InsertText', hwp.HParameterSet.HInsertText.HSet)
hwp.HParameterSet.HInsertText.Text = '삽입할 텍스트'
hwp.HAction.Execute('InsertText', hwp.HParameterSet.HInsertText.HSet)
```

## 4. ❌ 실패 사례 및 주의사항

### 4.1 FindWordByWord — 유효하지 않은 속성

```python
# ❌ 실패: AttributeError 발생
hwp.HParameterSet.HFindReplace.FindWordByWord = 0

# ✅ 해결: FindWordByWord는 사용하지 않는다 (FindString만 사용)
hwp.HParameterSet.HFindReplace.FindString = '검색어'
```

> 공식 문서에 있지만 실제 COM 인터페이스에서 지원하지 않는 속성으로 확인됨.

### 4.2 TreatAsChar — tbl vs pos 불일치

```python
# ❌ 의도: 표의 "글자처럼 취급"을 해제하여 페이지 넘김 허용
pset = hwp.HParameterSet.HShapeObject
pset.TreatAsChar = 0

# 실제 동작: tbl.textWrap만 변경됨 ("TOP_AND_BOTTOM" → "SQUARE")
# pos.treatAsChar는 여전히 "1" → 페이지 넘김 불가!
```

**해결**: XML 직접 수정이 유일한 방법

```python
import re

# HWPX ZIP 내 section0.xml에서:
xml = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', xml)
```

### 4.3 SaveAs 시 header.xml 미변경

- COM API로 파일을 열고 저장(`SaveAs`)해도 **header.xml은 변경되지 않음**
- 수동으로 한컴에서 속성을 변경하면 header.xml도 자동 업데이트됨
- 결론: **프로그래밍 방식의 header.xml 수정은 ZIP-level에서만 가능**

## 5. 권장 파이프라인

```
[기본 파이프라인 — 순수 Python, 모든 OS]
  MD → md_to_hwpx.py → fix_namespaces.py → verify_hwpx.py → HWPX

[COM API 확장 — Windows + 한글 설치 필수]
  HWPX → 한글 COM API 열기
       → RepeatFind (텍스트 앵커 검색)
       → InsertPicture / InsertTable (비주얼 삽입)
       → SaveAs → 최종 HWPX + PDF
```

> COM API 확장은 **선택적 후처리** 단계이며, 기본 파이프라인만으로도 완전한 제안서 생성 가능.
