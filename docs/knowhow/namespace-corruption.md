# lxml 네임스페이스 오염 — 한글 Viewer 빈 페이지 문제

## 1. 결론 (TL;DR)

- `lxml`의 `etree.tostring()`은 XML 직렬화 시 `ns0:`, `ns1:` 등의 접두사를 자동 부여한다.
- 한컴오피스는 이런 접두사를 인식하지 못하여 **빈 페이지**를 표시한다.
- **정규식 후처리로 접두사를 제거**하는 것이 유일한 해결책이다 (`fix_namespaces.py`).

## 2. 문제 및 현상 (UI 분석)

- 마크다운 → HWPX 변환 후, 한글 Viewer에서 파일을 열면 **빈 페이지만 표시**
- 파일 크기는 정상 (50KB+), ZIP 구조도 정상
- 다른 HWPX 편집기(python-hwpx 등)에서는 내용이 보임
- **한컴오피스에서만** 문제 발생

## 3. 원인 분석 (XML 구조)

### lxml 직렬화 출력 (문제)

```xml
<!-- lxml이 생성하는 잘못된 형식 -->
<ns0:p ns0:paraPrIDRef="8" xmlns:ns0="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <ns0:run ns0:charPrIDRef="63">
    <ns0:t>텍스트</ns0:t>
  </ns0:run>
</ns0:p>
```

### 한컴이 기대하는 형식 (정상)

```xml
<!-- 한컴이 파싱할 수 있는 올바른 형식 -->
<hp:p paraPrIDRef="8" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <hp:run charPrIDRef="63">
    <hp:t>텍스트</hp:t>
  </hp:run>
</hp:p>
```

**핵심**: 한컴오피스는 `hp:`, `hs:` 등 특정 접두사만 인식한다. `ns0:`, `ns1:` 등 lxml이 자동 생성하는 접두사는 파싱 실패.

### 추가 오염 패턴

- `&` → `&amp;` 이중 이스케이핑 (`&amp;amp;`)
- XML 선언 누락 (`<?xml ...?>`)
- 속성값 내 `xmlns:ns0=` 중첩 선언

## 4. 해결 방안 (코드 스니펫)

### 핵심 정규식 (3단계)

```python
import re

def fix_namespace_prefixes(xml_text: str) -> str:
    """lxml이 생성한 ns0:/ns1: 접두사를 제거한다."""
    
    # 1단계: ns0:, ns1: 등 여는 태그 접두사 제거
    #   <ns0:p ...> → <p ...>
    xml_text = re.sub(r'<ns\d+:', '<', xml_text)
    
    # 2단계: </ns0:p> 등 닫는 태그 접두사 제거
    #   </ns0:p> → </p>
    xml_text = re.sub(r'</ns\d+:', '</', xml_text)
    
    # 3단계: 속성의 ns0: 접두사 제거
    #   ns0:paraPrIDRef → paraPrIDRef
    xml_text = re.sub(r'\bns\d+:', '', xml_text)
    
    # 4단계: xmlns:ns0="..." 선언 자체 제거
    xml_text = re.sub(r'\s+xmlns:ns\d+="[^"]*"', '', xml_text)
    
    return xml_text


def fix_entity_corruption(xml_text: str) -> str:
    """이중 이스케이핑된 엔티티 복원."""
    xml_text = xml_text.replace('&amp;amp;', '&amp;')
    xml_text = xml_text.replace('&amp;lt;', '&lt;')
    xml_text = xml_text.replace('&amp;gt;', '&gt;')
    xml_text = xml_text.replace('&amp;quot;', '&quot;')
    xml_text = xml_text.replace('&amp;apos;', '&apos;')
    return xml_text


def fix_xml_declaration(xml_text: str) -> str:
    """XML 선언이 없으면 추가."""
    if not xml_text.strip().startswith('<?xml'):
        xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_text
    return xml_text
```

### 전체 후처리 파이프라인

```python
def fix_hwpx_file(hwpx_path: str):
    """HWPX 파일 내 모든 XML에 네임스페이스 수정 적용."""
    import zipfile, tempfile, shutil
    
    tmp = tempfile.mktemp(suffix='.hwpx')
    with zipfile.ZipFile(hwpx_path, 'r') as zin:
        with zipfile.ZipFile(tmp, 'w') as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith('.xml'):
                    text = data.decode('utf-8')
                    text = fix_xml_declaration(text)
                    text = fix_namespace_prefixes(text)
                    text = fix_entity_corruption(text)
                    data = text.encode('utf-8')
                zout.writestr(item, data)
    shutil.move(tmp, hwpx_path)
```

## 5. 주의사항

- **`exec()` 방식은 오동작할 수 있다** — 반드시 `subprocess.run()` 또는 직접 함수 호출을 사용.
- `etree.tostring(root, encoding='UTF-8', xml_declaration=True)` 사용 시에도 접두사 문제가 발생하며, `nsmap` 인자로는 해결 불가.
- 이 후처리는 **모든 ZIP-level/DOM 조작 후 반드시 실행**해야 한다.
- 2018 네임스페이스(`urn:hancom:hwpml:2018:*`)를 사용하는 최신 문서에서도 동일한 문제 발생.
