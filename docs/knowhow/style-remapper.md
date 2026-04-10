# Style Remapper — 레퍼런스 문서 스타일을 템플릿에 안전하게 이식

## 1. 결론 (TL;DR)

- 레퍼런스 HWPX의 스타일 정의(charPr/paraPr/borderFill)를 템플릿에 이식할 때, **기존 ID를 덮어쓰면 안 된다**.
- 레퍼런스 스타일 ID → 템플릿의 `max_id + 1`부터 **새 ID를 할당**하고, section XML의 모든 참조를 리매핑해야 한다.
- 폰트는 **이름(face) 기반**으로 매핑: 템플릿에 같은 이름이 있으면 재사용, 없으면 새 fontface 생성.

## 2. 문제 및 현상 (UI 분석)

레퍼런스 제안서의 표지·목차·조견표를 템플릿에 그대로 복사하면:

- **본문 폰트가 깨짐**: 레퍼런스의 `charPrIDRef=2`가 "휴먼명조 15pt"인데, 템플릿의 `charPrIDRef=2`는 "한양신명조 10pt"일 수 있음
- **표 테두리/배경 이상**: `borderFillIDRef` 충돌
- **들여쓰기 오류**: `paraPrIDRef` 충돌
- 4페이지 이후 본문 전체가 잘못된 스타일로 렌더링됨 (v010→v012 디버깅에서 발견)

## 3. 원인 분석 (XML 구조)

### header.xml의 ID 체계

```xml
<!-- 레퍼런스 header.xml -->
<charPr id="2" ...>  <!-- 휴먼명조 15pt -->
  <fontRef hangul="7" />
  <charSz val="1500" />
</charPr>

<!-- 템플릿 header.xml -->
<charPr id="2" ...>  <!-- 한양신명조 10pt -->
  <fontRef hangul="14" />
  <charSz val="1000" />
</charPr>
```

**문제의 근본 원인**: charPr/paraPr/borderFill의 `id`는 문서별로 독립적이며, 같은 숫자라도 전혀 다른 서식을 가리킬 수 있다.

### fontface도 동일한 문제

```xml
<!-- 레퍼런스: fontRef hangul="7" → 휴먼명조 -->
<!-- 템플릿:   fontRef hangul="7" → HY견고딕 (!) -->
```

## 4. 해결 방안 (코드 스니펫)

### Style Remapper 알고리즘

```python
from lxml import etree
from copy import deepcopy

def style_remap(tmpl_hdr_root, ref_hdr_root, needed_ids):
    """레퍼런스 스타일을 템플릿에 충돌 없이 머지한다.
    
    Returns:
        style_id_maps: {'charPr': {old→new}, 'paraPr': {old→new}, 'borderFill': {old→new}}
    """
    style_id_maps = {'borderFill': {}, 'charPr': {}, 'paraPr': {}}
    container_map = {
        'borderFill': 'borderFills',
        'charPr': 'charProperties',
        'paraPr': 'paraProperties',
    }
    
    for tag_name, ids_needed in needed_ids.items():
        # 1. 템플릿에서 현재 최대 ID 찾기
        max_id = 0
        container = None
        for elem in tmpl_hdr_root.iter():
            t = etree.QName(elem.tag).localname
            if t == tag_name:
                idx = int(elem.get('id', '0'))
                if idx > max_id: max_id = idx
            elif t == container_map[tag_name]:
                container = elem
        
        if container is None:
            continue
        
        # 2. 레퍼런스에서 필요한 요소 추출
        ref_map = {}
        for elem in ref_hdr_root.iter():
            t = etree.QName(elem.tag).localname
            if t == tag_name and elem.get('id', '') in ids_needed:
                ref_map[elem.get('id', '')] = elem
        
        # 3. 새 ID 할당 + 추가
        for old_id in ids_needed:
            ref_elem = ref_map.get(old_id)
            if ref_elem is None:
                continue
            
            max_id += 1
            new_id = str(max_id)
            style_id_maps[tag_name][old_id] = new_id
            
            new_elem = deepcopy(ref_elem)
            new_elem.set('id', new_id)
            
            # charPr 내부의 fontRef도 리매핑 필요!
            if tag_name == 'charPr':
                remap_fonts_in_charpr(new_elem, font_remap_table)
            
            container.append(new_elem)
    
    return style_id_maps
```

### Font Remapper (이름 기반)

```python
def build_font_remap(tmpl_hdr_root, ref_hdr_root):
    """폰트를 이름(face)으로 매핑. 없으면 새 ID 할당."""
    tmpl_fonts = {}  # name → id
    max_id = 0
    
    for elem in tmpl_hdr_root.iter():
        if etree.QName(elem.tag).localname == 'fontface':
            name = elem.get('name')
            fid = int(elem.get('id', '0'))
            tmpl_fonts[name] = str(fid)
            max_id = max(max_id, fid)
    
    ref_fonts = {}
    for elem in ref_hdr_root.iter():
        if etree.QName(elem.tag).localname == 'fontface':
            ref_fonts[elem.get('id')] = elem
    
    remap = {}
    for ref_id, ref_elem in ref_fonts.items():
        name = ref_elem.get('name')
        if name in tmpl_fonts:
            remap[ref_id] = tmpl_fonts[name]  # 기존 ID 재사용
        else:
            max_id += 1
            remap[ref_id] = str(max_id)
            # 새 fontface를 template에 추가
    
    return remap
```

### Section XML에서 ID 리라이트

```python
import re

def rewrite_ids(section_xml_str, style_id_maps):
    """section XML의 모든 *IDRef 속성을 새 ID로 치환."""
    for attr, map_dict in [
        ('paraPrIDRef', style_id_maps['paraPr']),
        ('charPrIDRef', style_id_maps['charPr']),
        ('borderFillIDRef', style_id_maps['borderFill']),
    ]:
        def replacer(match):
            old = match.group(2)
            new = map_dict.get(old, old)
            return f'{match.group(1)}{new}{match.group(3)}'
        section_xml_str = re.sub(f'({attr}=")([^"]+)(")', replacer, section_xml_str)
    return section_xml_str
```

## 5. 주의사항

- **순서 중요**: `borderFill` → `charPr` → `paraPr` 순으로 리매핑해야 한다 (paraPr이 borderFillIDRef를 참조하므로).
- `itemCnt` / `count` 속성도 업데이트해야 한다.
- 레퍼런스의 secPr(편집용지)은 가져오지 **않는다** — 템플릿의 페이지 설정을 유지.
