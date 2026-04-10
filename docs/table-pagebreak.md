# Table Page-break Solution — 표 페이지 넘김 완벽 가이드

> ⚠️ 이 문서의 내용은 53+ 버전 반복을 통해 **실측 검증**된 결과입니다.
> 공식 한컴 문서(HwpAutomation.pdf, ParameterSetTable_2504.pdf)에는 불완전하게 기술되어 있습니다.

## 결론 (TL;DR)

HWPX에서 표가 페이지를 넘어가려면 **3가지 조건**을 모두 충족해야 합니다:

```
1. <hp:tbl textWrap="SQUARE">         ← "글자처럼 취급" 해제
2. <hp:tbl pageBreak="TABLE">         ← "나눔" 활성화
3. <pos treatAsChar="0">              ← ★ 실제 동작 제어 (가장 중요!)
```

> `tbl.textWrap`과 `tbl.pageBreak`만 바꾸면 소용없다. `pos.treatAsChar`가 `1`이면 무조건 페이지 넘김 불가.

## UI ↔ XML 속성 매핑

| 한컴 UI | COM API (SetItem) | HWPX XML 위치 | 값 (활성화) | 값 (비활성화) |
|---------|-------------------|---------------|-----------|------------|
| 글자처럼 취급 OFF | `TreatAsChar = False` | `pos.treatAsChar` | `1` | `0` |
| 글자처럼 취급 OFF | `TreatAsChar = False` | `tbl.textWrap` | `TOP_AND_BOTTOM` | `SQUARE` |
| 나눔 (셀 단위) | `PageBreak = 1` | `tbl.pageBreak` | `NONE` | `TABLE` |
| 나눔 (텍스트도) | `PageBreak = 2` | `tbl.pageBreak` | — | `CELL` |

> ⚠️ 직관과 반대: "셀 단위로 나눔" UI 선택 시 XML에는 `pageBreak="TABLE"`로 저장됨

## pos.treatAsChar 위치 (XML)

```xml
<hp:tbl textWrap="SQUARE" pageBreak="TABLE" ...>
  <shapeComponent ...>
    <pos treatAsChar="0" affectLSpacing="0" flowWithText="1" 
         allowOverlap="0" holdAnchorAndSO="0" 
         vertRelTo="PARA" horzRelTo="PARA" 
         vertAlign="TOP" horzAlign="LEFT" 
         vertOffset="0" horzOffset="0"/>
    <sz width="47688" height="67668"/>
  </shapeComponent>
  <hp:tr>...</hp:tr>
</hp:tbl>
```

## COM API 한계 (핵심 교훈)

- 공식 문서(p.141): `Table.SetItem "TreatAsChar", True` 가능
- 그러나 **`pset.TreatAsChar = 0`은 `tbl.textWrap`만 변경** — `pos.treatAsChar`는 미변경!
- 수동으로 한컴에서 변경하면 `header.xml`과 `pos.treatAsChar` 모두 자동 업데이트
- **결론: XML 직접 수정이 유일하게 확실한 프로그래밍 방식**

## 해결 방법 — XML 직접 수정 (확정, 권장)

```python
import zipfile
import re
import shutil
import tempfile

def fix_table_pagebreak(hwpx_path: str, output_path: str = None):
    """모든 표의 페이지 넘김을 활성화한다."""
    if output_path is None:
        output_path = hwpx_path  # in-place
    
    tmp = tempfile.mktemp(suffix='.hwpx')
    
    with zipfile.ZipFile(hwpx_path, 'r') as zin:
        with zipfile.ZipFile(tmp, 'w') as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                
                if item.filename.startswith('Contents/section') and item.filename.endswith('.xml'):
                    xml = data.decode('utf-8')
                    
                    # 1. pos.treatAsChar → 0
                    xml = re.sub(r'treatAsChar="1"', 'treatAsChar="0"', xml)
                    
                    # 2. horzRelTo="COLUMN" → "PARA" (정상 패턴)
                    xml = re.sub(r'horzRelTo="COLUMN"', 'horzRelTo="PARA"', xml)
                    
                    # 3. linesegarray의 큰 vertsize 초기화
                    xml = re.sub(r'vertsize="(\d{5,})"', 'vertsize="1200"', xml)
                    
                    data = xml.encode('utf-8')
                
                zout.writestr(item, data)
    
    shutil.move(tmp, output_path)
```

## linesegarray 캐시

- 부모 `<hp:p>`의 `<hp:linesegarray>` 내 `vertsize`가 표의 고정 높이 캐시
- `vertsize=63048` → A4 한 페이지 높이 (고정 — 넘침 방지)
- `vertsize=1200` → 한컴이 재계산 (수동 변경 후 한컴이 자동 설정)
- **제거 시** 한컴이 열 때 자동 재생성 → 안전한 대안

## 검증 스크립트

```python
from lxml import etree
import zipfile

def verify_table_treatAsChar(hwpx_path: str):
    """모든 표의 treatAsChar 값을 확인한다."""
    with zipfile.ZipFile(hwpx_path) as z:
        xml = z.read('Contents/section0.xml')
    
    tree = etree.fromstring(xml)
    NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
    
    for i, tbl in enumerate(tree.iter(f'{{{NS}}}tbl')):
        for elem in tbl.iter():
            if 'treatAsChar' in elem.attrib:
                val = elem.get('treatAsChar')
                status = '✅' if val == '0' else '❌'
                print(f'{status} 표[{i}] pos.treatAsChar = {val}')
```

## 관련 파일

- `scripts/fix_namespaces.py` — `--fix-tables` 옵션으로 통합 적용
- `docs/knowhow/com-api-pitfalls.md` — COM API TreatAsChar 한계 상세
