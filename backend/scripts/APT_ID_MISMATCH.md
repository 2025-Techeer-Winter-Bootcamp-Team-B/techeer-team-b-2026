# apartments ↔ apart_details apt_id 불일치

## 현상

- `apart_details.apt_id`(FK)가 가리키는 `apartments.apt_id`와, **상세 정보 내용**(주소 등)이 서로 다른 아파트를 가리킴.
- 예: 힐스테이트 상세(FK 5419) ↔ 실제 힐스테이트(ID 5421) — **차이 -2**
- 처음 **몇백 개**는 맞다가 **중간부터** 어긋남.

## 어느 쪽 문제인가?

**`apart_details` 쪽 문제**로 보는 것이 타당합니다.

- 상세 정보 **내용**(도로명/지번 주소 등)은 국토부 API `kapt_code` 기준으로 수집.
- 수집 시 `apt_id`는 `get_multi_missing_details`로 잡은 **아파트**와 1:1로 매칭해 저장.
- 따라서 **같은** `apt_id`를 쓰는데 **다른** 아파트 내용이 들어갔다면,  
  → 상세 수집 과정에서 **어떤 아파트와 묶어서 저장했는지**가 잘못된 것(즉 `apart_details` 쪽 매칭 오류).

`apartments` 테이블의 `apt_id` 자체가 잘못됐다기보다는,  
**상세 수집 루프/배치**에서 “이 상세 = 이 아파트” 매핑이 틀어졌다고 보는 게 맞습니다.

## 가능한 원인

1. **`get_multi_missing_details` 정렬 없음 (가장 유력)**  
   - `ORDER BY` 없이 “상세 없는 아파트” 목록을 조회.
   - DB/인덱스/동시성에 따라 **배치마다 순서가 달라질 수 있음**.
   - 상세 수집은 이 순서대로 아파트를 처리하므로, 순서가 어긋나면 **apt_id ↔ 상세 내용** 매칭이 밀릴 수 있음.  
   - 특히 **apt_id 기준 -2**처럼 일정한 오프셋이 나오는 것은 “순서가 일정하게 밀린다”는 가설과 잘 맞음.

2. **apartments 쪽 apt_id 간격 (삭제/롤백)**  
   - `apartments`에서 일부 행이 삭제되거나 롤백되면 `apt_id`에 간격이 생김.
   - 상세 수집이 “순서/인덱스”에 의존하는 로직이 있었다면, 이 간격과 결합해 매칭이 틀어질 여지가 있음.  
   - 다만 **현재 코드**는 아파트 **객체의 `apt_id`**를 그대로 쓰므로, 순서만 고정되면 이 영향은 제한적.

3. **Docker/다중 세션**  
   - 메인 세션으로 `get_multi_missing_details`, 워커 세션으로 상세 저장.
   - 세션/트랜잭션 격리로 “누락 목록”이 배치마다 달라지거나, 타이밍에 따라 순서가 바뀌면 1번과 같은 효과.

## 적용한 수정 사항

### 1. `get_multi_missing_details`에 `ORDER BY apt_id`

- **파일**: `app/crud/apartment.py`
- **내용**: “상세 없는 아파트” 조회 시 `ORDER BY Apartment.apt_id` 추가.
- **목적**: 배치·재실행에 상관없이 **항상 같은 순서**로 아파트를 가져와, 상세 수집 시 apt_id ↔ 상세 매칭이 꼬이지 않도록 함.

### 2. `fix_data_mismatch` 스크립트

- **기존**: `apt_id`를 **음수**로 바꾸는 2단계 수정 → `apartments.apt_id` FK 제약으로 인해 **오류 발생**.
- **변경**:  
  - `correct_apt_id` **내림차순**으로 정렬 후,  
  - **직접** `UPDATE apart_details SET apt_id = correct_apt_id` 수행.  
- **목적**: FK를 위반하지 않으면서, Unique 등 제약과 충돌 없이 잘못된 `apt_id`만 수정.

## 사용 방법

1. **불일치 분석**  
   ```bash
   python backend/scripts/analyze_apt_id_mismatch.py
   ```
2. **자동 수정** (분석 결과 확인 후)  
   ```bash
   python backend/scripts/fix_data_mismatch.py
   ```

이후에는 `get_multi_missing_details` 순서 고정으로 **재수집 시** 동일한 apt_id 꼬임이 다시 발생할 가능성을 줄였습니다.
