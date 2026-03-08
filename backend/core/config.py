import os
from dotenv import load_dotenv

load_dotenv()

# 넥슨 API 설정
NEXON_API_KEY = os.getenv("NEXON_API_KEY")
BASE_URL = "https://open.api.nexon.com/maplestory/v1"
HEADERS = {"x-nxopen-api-key": NEXON_API_KEY}
