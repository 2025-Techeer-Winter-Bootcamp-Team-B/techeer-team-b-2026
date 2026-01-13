# 데이터베이스 스키마 분석 보고서

## 📋 개요
`.agent/data.sql` 파일을 기반으로 한 데이터베이스 스키마의 설계 및 관계 문제점 분석 보고서입니다.

---

## ✅ 잘 설계된 부분

1. **테이블 분리**: 아파트 기본 정보(`APARTMENTS`)와 상세 정보(`APART_DETAILS`)를 분리하여 정규화가 잘 되어 있습니다.
2. **거래 정보 분리**: 매매(`SALES`)와 전월세(`RENTS`)를 별도 테이블로 분리하여 각 거래 유형의 특성을 반영했습니다.
3. **소프트 삭제**: 모든 테이블에 `is_deleted` 필드를 포함하여 소프트 삭제 패턴을 일관되게 적용했습니다.
4. **타임스탬프**: `created_at`, `updated_at` 필드를 포함하여 감사 추적이 가능합니다.

---

## ⚠️ 발견된 문제점

### 1. **ACCOUNTS 테이블 - PRIMARY KEY 문제**

**문제점:**
```sql
CREATE TABLE `ACCOUNTS` (
    `account_id` int NULL COMMENT 'PK',  -- ❌ NULL이면 안 됨!
    ...
);
```

**문제:**
- PRIMARY KEY는 `NOT NULL`이어야 합니다.
- `NULL`로 정의되면 AUTO_INCREMENT가 제대로 작동하지 않을 수 있습니다.

**해결방안:**
```sql
`account_id` int NOT NULL AUTO_INCREMENT COMMENT 'PK',
```

**현재 구현 상태:**
✅ `init_db.sql`에서 `SERIAL PRIMARY KEY`로 올바르게 수정됨

---

### 2. **ACCOUNTS 테이블 - 필수 필드 누락**

**문제점:**
- `clerk_user_id`와 `email`이 모두 `NULL` 허용
- 인증 시스템에서 사용자 식별이 어려울 수 있음

**권장사항:**
- `clerk_user_id`는 `NOT NULL`로 설정하는 것을 고려
- 또는 `clerk_user_id`와 `email` 중 하나는 반드시 존재하도록 제약조건 추가

**현재 구현 상태:**
⚠️ `init_db.sql`에서도 nullable로 유지 (비즈니스 요구사항에 따라 결정 필요)

---

### 3. **MY_PROPERTIES 테이블 - 주석 오류**

**문제점:**
```sql
CREATE TABLE `MY_PROPERTIES` (
    `property_id` int NOT NULL COMMENT 'PK',
    `account_id` int NOT NULL COMMENT 'PK',  -- ❌ 실제로는 FK
    `apt_id` int NOT NULL COMMENT 'PK',       -- ❌ 실제로는 FK
    ...
);
```

**문제:**
- `account_id`와 `apt_id`는 FOREIGN KEY인데 주석에 'PK'로 표기됨
- 실제 PRIMARY KEY는 `property_id`만 해당

**해결방안:**
- 주석 수정: `'FK'`로 변경
- 복합키가 필요한지 검토 (한 사용자가 같은 아파트를 여러 번 등록할 수 있는지)

**현재 구현 상태:**
✅ 모델 파일에서 올바르게 FK로 정의됨

---

### 4. **APART_DETAILS 테이블 - 주석 오류**

**문제점:**
```sql
CREATE TABLE `APART_DETAILS` (
    `apt_detail_id` int NOT NULL COMMENT 'PK',
    `apt_id` int NOT NULL COMMENT 'PK',  -- ❌ 실제로는 FK
    ...
);
```

**문제:**
- `apt_id`는 FOREIGN KEY인데 주석에 'PK'로 표기됨
- 실제 PRIMARY KEY는 `apt_detail_id`만 해당

**해결방안:**
- 주석 수정: `'FK'`로 변경
- `apt_id`에 UNIQUE 제약조건 추가 고려 (1:1 관계 보장)

**현재 구현 상태:**
✅ 모델 파일에서 올바르게 FK로 정의됨
⚠️ `init_db.sql`에 UNIQUE 제약조건 미추가 (1:1 관계 보장 필요)

---

### 5. **외래키 제약조건 누락**

**문제점:**
- `data.sql`에는 PRIMARY KEY만 정의되어 있고, FOREIGN KEY 제약조건이 없음
- 데이터 무결성을 보장할 수 없음

**영향:**
- 존재하지 않는 `account_id`, `apt_id`, `region_id` 등을 참조할 수 있음
- 데이터 일관성 문제 발생 가능

**해결방안:**
- 모든 외래키에 FOREIGN KEY 제약조건 추가
- CASCADE 옵션 고려 (삭제 시 관련 데이터 처리)

**현재 구현 상태:**
✅ `init_db.sql`에서 모든 외래키 제약조건 추가됨

---

### 6. **SALES 테이블 - deal_date 누락**

**문제점:**
- `SALES` 테이블에는 `contract_date`만 있고 `deal_date`가 없음
- `RENTS` 테이블에는 `deal_date`가 있음
- 일관성 문제

**비교:**
```sql
-- SALES
`contract_date` date NULL,

-- RENTS
`deal_date` date NOT NULL,
`contract_date` date NULL,
```

**권장사항:**
- `SALES` 테이블에도 `deal_date` 추가 고려
- 또는 두 테이블의 날짜 필드 의미를 명확히 정의

**현재 구현 상태:**
⚠️ `init_db.sql`에서도 동일하게 유지 (비즈니스 요구사항 확인 필요)

---

### 7. **RENTS 테이블 - contract_type 타입 문제**

**문제점:**
```sql
`contract_type` tinyint(1) NULL COMMENT '신규 or 갱신',
```

**문제:**
- `tinyint(1)`은 BOOLEAN으로 해석되지만, "신규 or 갱신"은 두 가지 값이 필요
- BOOLEAN으로는 표현하기 어려움

**권장사항:**
- `VARCHAR(10)` 또는 `ENUM` 타입 사용
- 또는 별도의 코드 테이블 참조

**현재 구현 상태:**
⚠️ `init_db.sql`에서 `BOOLEAN`으로 유지 (비즈니스 로직에서 처리 필요)

---

### 8. **인덱스 누락**

**문제점:**
- `data.sql`에는 인덱스 정의가 없음
- 자주 조회되는 필드에 인덱스가 없으면 성능 저하

**권장 인덱스:**
- `accounts.clerk_user_id` (유니크 인덱스)
- `accounts.email` (유니크 인덱스)
- `apartments.region_id` (FK 인덱스)
- `apartments.kapt_code` (유니크 인덱스)
- `sales.apt_id`, `sales.contract_date` (FK 및 조회 인덱스)
- `rents.apt_id`, `rents.deal_date` (FK 및 조회 인덱스)
- `house_scores.region_id`, `house_scores.base_ym` (FK 및 조회 인덱스)

**현재 구현 상태:**
✅ `init_db.sql`에서 주요 인덱스 추가됨

---

### 9. **APART_DETAILS와 APARTMENTS 관계**

**문제점:**
- `APART_DETAILS`의 `apt_id`에 UNIQUE 제약조건이 없음
- 하나의 아파트에 여러 상세 정보가 저장될 수 있음 (1:N 관계)
- 하지만 비즈니스 로직상 1:1 관계가 맞을 수 있음

**권장사항:**
- 1:1 관계가 맞다면 `apt_id`에 UNIQUE 제약조건 추가
- 1:N 관계가 맞다면 현재 구조 유지

**현재 구현 상태:**
⚠️ `init_db.sql`에 UNIQUE 제약조건 미추가 (1:1 관계 보장 필요)

---

### 10. **FAVORITE_APARTMENTS 테이블 - account_id NULL 허용**

**문제점:**
```sql
`account_id` int NULL COMMENT 'FK',
```

**문제:**
- 즐겨찾기인데 `account_id`가 NULL이면 누구의 즐겨찾기인지 알 수 없음
- 비즈니스 로직상 NULL이 필요한 경우인지 확인 필요

**권장사항:**
- NULL이 필요 없다면 `NOT NULL`로 변경
- NULL이 필요하다면 비즈니스 요구사항 문서화

**현재 구현 상태:**
⚠️ `init_db.sql`에서도 nullable로 유지 (비즈니스 요구사항 확인 필요)

---

## 📊 요약

### 심각도별 분류

| 심각도 | 문제 | 상태 |
|--------|------|------|
| 🔴 높음 | ACCOUNTS.account_id NULL | ✅ 수정됨 |
| 🔴 높음 | 외래키 제약조건 누락 | ✅ 수정됨 |
| 🟡 중간 | 인덱스 누락 | ✅ 수정됨 |
| 🟡 중간 | APART_DETAILS UNIQUE 제약조건 | ⚠️ 검토 필요 |
| 🟢 낮음 | 주석 오류 (PK/FK) | ✅ 모델에서 수정됨 |
| 🟢 낮음 | SALES deal_date 누락 | ⚠️ 비즈니스 요구사항 확인 |
| 🟢 낮음 | RENTS contract_type 타입 | ⚠️ 비즈니스 요구사항 확인 |

---

## ✅ 수정 완료 사항

1. ✅ `init_db.sql` 통합 및 스키마 반영
2. ✅ 모든 모델 파일 생성/수정
3. ✅ 외래키 제약조건 추가
4. ✅ 인덱스 추가
5. ✅ PRIMARY KEY 문제 수정

---

## ⚠️ 추가 검토 필요 사항

1. **APART_DETAILS와 APARTMENTS 관계**: 1:1인지 1:N인지 확인 후 UNIQUE 제약조건 추가 여부 결정
2. **SALES deal_date**: 매매 거래에도 거래일 필드가 필요한지 확인
3. **RENTS contract_type**: BOOLEAN 타입으로 충분한지, ENUM이나 VARCHAR로 변경 필요 여부 확인
4. **FAVORITE_APARTMENTS account_id**: NULL 허용이 필요한 비즈니스 요구사항인지 확인
5. **ACCOUNTS 필수 필드**: `clerk_user_id`나 `email` 중 하나를 필수로 만들지 검토

---

## 📝 권장 사항

1. **데이터 무결성 강화**: 모든 외래키에 CASCADE 옵션 검토
2. **성능 최적화**: 자주 조회되는 필드에 인덱스 추가 (이미 추가됨)
3. **비즈니스 규칙 문서화**: NULL 허용, UNIQUE 제약조건 등의 비즈니스 요구사항 문서화
4. **마이그레이션 전략**: 기존 데이터베이스가 있다면 마이그레이션 스크립트 작성 필요
