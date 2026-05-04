# 메이플 썬데이

메이플스토리 캐릭터 정보 조회부터 썬데이 메이플 예측까지 빠르고 직관적으로 제공하는 서비스입니다.

## 주요 기능

- **캐릭터 검색** — 닉네임으로 캐릭터 스탯, 장비, 유니온, 스킬 등 상세 정보 조회
- **썬데이 메이플 예측** — 과거 이력 기반 다음 썬데이 메이플 이벤트 예측
- **썬데이 캘린더** — 전체 썬데이 메이플 이력 및 방송 일정 확인
- **공지 게시판** — 메이플스토리 공지·업데이트·이벤트·캐시샵 공지 통합 제공

## 기술 스택

| 구분 | 스택 |
|------|------|
| Frontend | HTML / CSS / Vue 3 (CDN) |
| Backend | Python / FastAPI |
| DB | Supabase |
| 외부 API | 넥슨 오픈 API |
| 배포 | Vercel (프론트) / Render (백엔드) |

## 로컬 실행

### 백엔드

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

`.env` 파일에 아래 환경변수 설정 필요:

```
NEXON_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
```

### 프론트엔드

빌드 없이 정적 파일을 그대로 서빙합니다.

```bash
cd frontend
npx serve .
```
