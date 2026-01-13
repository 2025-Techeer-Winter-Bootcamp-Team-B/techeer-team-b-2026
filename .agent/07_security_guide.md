# 보안 가이드 (Security Guide)

## ⚠️ 중요: 인증키 및 민감 정보 보호

이 문서는 프로젝트의 모든 개발자가 반드시 준수해야 하는 보안 규칙을 정의합니다.

---

## 1. 인증키 하드코딩 금지

### ❌ 절대 하지 말아야 할 것

```python
# ❌ 나쁜 예: 하드코딩
MOLIT_API_KEY = "your_actual_api_key_here_never_put_real_key"  # ⚠️ 실제 키를 절대 넣지 마세요!
CLERK_SECRET_KEY = "sk_test_xxxxx..."  # ⚠️ 실제 키를 절대 넣지 마세요!
DATABASE_URL = "postgresql://postgres:password@localhost:5432/realestate"  # ⚠️ 실제 비밀번호를 절대 넣지 마세요!

# ❌ 나쁜 예: 코드에 직접 작성
api_key = "your_actual_key_here"
password = "my_password"
```

### ✅ 올바른 방법

```python
# ✅ 좋은 예: 환경변수 사용
from app.core.config import settings

api_key = settings.MOLIT_API_KEY  # .env 파일에서 로드
secret_key = settings.CLERK_SECRET_KEY  # .env 파일에서 로드
database_url = settings.DATABASE_URL  # .env 파일에서 로드
```

---

## 2. `.env` 파일 보호 규칙

### 2.1 `.env` 파일은 절대 Git에 커밋하지 않음

- `.env` 파일은 `.gitignore`에 포함되어 있습니다.
- **절대** `git add .env` 또는 `git commit`에 포함시키지 마세요.
- `.env.example` 파일만 Git에 추적됩니다 (예시 값만 포함).

### 2.2 `.env` 파일 변경 금지

#### ⚠️ 중요: `.env` 파일은 다음 경우를 제외하고 절대 수정하지 마세요

1. **최초 프로젝트 설정 시**: 프로젝트를 처음 클론받았을 때 `.env.example`을 복사하여 `.env` 생성
2. **환경변수 추가 시**: 새로운 API 키나 설정이 필요할 때만 추가
3. **보안 문제 발생 시**: 키가 유출되었을 때만 변경

#### ❌ 금지 사항

- **임의로 `.env` 파일의 값을 변경하지 마세요**
- **다른 개발자의 `.env` 파일을 복사하지 마세요**
- **`.env` 파일을 다른 사람과 공유하지 마세요**
- **`.env` 파일의 내용을 채팅, 이메일, 문서에 붙여넣지 마세요**

### 2.3 `.env` 파일 확인 방법

PR(Pull Request) 전에 반드시 확인:

```bash
# .env 파일이 Git에 추적되지 않는지 확인
git status --short | grep ".env"

# .env 파일이 Git에 포함되지 않는지 확인
git ls-files | grep "\.env$"
```

**결과가 없어야 합니다!** `.env` 파일이 나오면 즉시 제거하세요.

---

## 3. 로그에 인증키 노출 방지

### ❌ 나쁜 예

```python
# ❌ 전체 키를 로그에 출력
logger.info(f"API Key: {self.api_key}")
logger.debug(f"Service Key: {settings.MOLIT_API_KEY}")
```

### ✅ 좋은 예

```python
# ✅ 키의 일부만 표시 (마스킹)
key_preview = self.api_key[:10] + "..." + self.api_key[-10:] if len(self.api_key) > 20 else "***"
logger.info(f"🔑 MOLIT_API_KEY 로드 완료: {key_preview} (전체 길이: {len(self.api_key)})")

# ✅ 디버그 로그에도 일부만 표시
logger.debug(f"   🔍 요청 파라미터: serviceKey={self.api_key[:10]}...")
```

---

## 4. 코드 검토 체크리스트

PR(Pull Request) 전에 반다시 확인:

### 4.1 하드코딩된 키 검색

```bash
# 프로젝트 루트에서 실행
# 1. MOLIT API 키 검색
grep -r "MOLIT_API_KEY\s*=\s*['\"][^'\"]{20,}" backend/

# 2. 일반적인 API 키 패턴 검색
grep -ri "api[_-]?key\s*[:=]\s*['\"][^'\"]{10,}" backend/

# 3. 비밀번호 검색
grep -ri "password\s*[:=]\s*['\"][^'\"]{5,}" backend/

# 4. 실제 키 값 검색 (실제 키를 여기에 넣어서 검색)
# grep -r "your_actual_api_key_here" .  # ⚠️ 실제 키로 검색할 때만 사용
```

**모든 검색 결과가 비어있어야 합니다!**

### 4.2 `.env` 파일 확인

```bash
# .env 파일이 Git에 추적되지 않는지 확인
git ls-files | grep "\.env$"

# .env 파일이 변경 목록에 없는지 확인
git status --short | grep "\.env"
```

### 4.3 로그 파일 확인

```bash
# 로그 파일에 키가 포함되어 있는지 확인
# grep -r "your_actual_api_key_here" *.log *.txt 2>/dev/null  # ⚠️ 실제 키로 검색할 때만 사용
```

**로그 파일은 `.gitignore`에 포함되어 있어야 합니다!**

---

## 5. 인증키 유출 시 대응 절차

### 5.1 즉시 조치

1. **유출된 키 즉시 재발급**
   - 공공데이터포털에서 MOLIT API 키 재발급
   - Clerk에서 Secret Key 재발급
   - 기타 유출된 모든 키 재발급

2. **`.env` 파일 업데이트**
   - 새로운 키로 `.env` 파일 업데이트
   - **주의**: `.env` 파일은 Git에 커밋하지 않음!

3. **Git 히스토리 확인**
   - 유출된 키가 Git 히스토리에 있는지 확인
   - 있다면 `git filter-branch` 또는 `git filter-repo`로 제거

### 5.2 예방 조치

- PR 전에 반드시 보안 체크리스트 확인
- 코드 리뷰 시 인증키 하드코딩 여부 확인
- 로그 파일은 `.gitignore`에 포함

---

## 6. 환경변수 사용 가이드

### 6.1 환경변수 추가 방법

1. **`.env.example` 파일에 예시 추가**
   ```bash
   # .env.example
   NEW_API_KEY=your_api_key_here
   ```

2. **`backend/app/core/config.py`에 설정 추가**
   ```python
   class Settings(BaseSettings):
       # 기존 설정...
       NEW_API_KEY: Optional[str] = None  # 새로운 API 키
   ```

3. **코드에서 사용**
   ```python
   from app.core.config import settings
   
   if not settings.NEW_API_KEY:
       raise ValueError("NEW_API_KEY가 설정되지 않았습니다.")
   
   api_key = settings.NEW_API_KEY
   ```

4. **개인 `.env` 파일에 실제 값 추가**
   ```bash
   # .env (Git에 커밋하지 않음!)
   NEW_API_KEY=actual_key_value_here
   ```

### 6.2 필수 환경변수

프로젝트 실행에 필요한 최소 환경변수:

```bash
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/realestate

# Redis
REDIS_URL=redis://redis:6379/0

# Clerk 인증
CLERK_SECRET_KEY=sk_test_...
SECRET_KEY=your_secret_key_here

# 외부 API (선택사항)
MOLIT_API_KEY=your_molit_api_key_here
```

---

## 7. Git Hooks를 통한 보호 (선택사항)

### 7.1 Pre-commit Hook 설정

`.git/hooks/pre-commit` 파일 생성:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# .env 파일이 커밋되는지 확인
if git diff --cached --name-only | grep -q "\.env$"; then
    echo "❌ 오류: .env 파일은 커밋할 수 없습니다!"
    echo "   .env 파일을 스테이징에서 제거하세요: git reset HEAD .env"
    exit 1
fi

# 하드코딩된 API 키 검색
if git diff --cached | grep -E "MOLIT_API_KEY\s*=\s*['\"][^'\"]{20,}"; then
    echo "❌ 오류: 하드코딩된 MOLIT_API_KEY가 발견되었습니다!"
    echo "   환경변수를 사용하세요: settings.MOLIT_API_KEY"
    exit 1
fi

echo "✅ 보안 검사 통과"
exit 0
```

**Windows에서 사용하려면 Git Bash를 사용하거나 PowerShell 스크립트로 변환해야 합니다.**

---

## 8. 팀원 공유 규칙

### 8.1 새 팀원 온보딩

1. `.env.example` 파일을 복사하여 `.env` 생성
2. 각자 필요한 API 키를 발급받아 `.env`에 추가
3. **절대** 다른 팀원의 `.env` 파일을 복사하지 않음

### 8.2 API 키 발급

- 각 개발자는 자신의 API 키를 발급받아 사용
- 공용 키가 필요한 경우 별도로 관리 (예: 팀 슬랙 채널)

---

## 9. 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub 보안 모범 사례](https://docs.github.com/en/code-security)
- [FastAPI 보안 가이드](https://fastapi.tiangolo.com/tutorial/security/)

---

## 10. 문의

보안 관련 문의사항이 있으면 팀 리더에게 연락하세요.

**기억하세요: 한 번 유출된 키는 되돌릴 수 없습니다. 항상 주의하세요!** 🔒
