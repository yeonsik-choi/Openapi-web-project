from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.character import router as character_router

app = FastAPI(title="메이플스토리 캐릭터 검색 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(character_router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "메이플 캐릭터 검색 서버 정상 작동 중"}
