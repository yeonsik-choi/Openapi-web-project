from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException

from core.config import BASE_URL, HEADERS, NEXON_API_KEY

KST = ZoneInfo("Asia/Seoul")


def get_yesterday() -> str:
    """넥슨 조회일: KST 기준 전날, 새벽 2시 전에는 전전날."""
    now = datetime.now(KST)
    days_ago = 2 if now.hour < 2 else 1
    target = now.date() - timedelta(days=days_ago)
    return target.strftime("%Y-%m-%d")


def _explicit_query_date(date: str | None) -> str | None:
    """호출부에서 날짜를 넘긴 경우에만 사용. None/빈 문자열이면 None."""
    if date is None:
        return None
    s = str(date).strip()[:10]
    return s or None


def _needs_date_retry_after_omit(subpath: str, data: dict) -> bool:
    """date 생략 첫 응답에서 특정 필드가 비었으면 get_yesterday()로 한 번 더 조회."""
    if subpath == "character/popularity":
        return data.get("popularity") is None
    if subpath == "user/union":
        return data.get("union_level") is None and data.get("unionLevel") is None
    return False


def require_nexon_api_key() -> None:
    if not NEXON_API_KEY:
        raise HTTPException(status_code=500, detail="API 키가 설정되지 않았습니다.")


def raise_nexon_request_error(exc: httpx.RequestError) -> None:
    raise HTTPException(
        status_code=502,
        detail=(
            "넥슨 오픈 API에 연결하지 못했습니다. "
            f"({type(exc).__name__}: {exc}) "
            "VPN·회사 프록시·HTTP_PROXY 환경이면 비활성화 후 다시 시도하거나, "
            "방화벽에서 open.api.nexon.com 허용을 확인하세요."
        ),
    ) from exc


# 재시도 가능한 일시적 에러 (서버 측 문제 또는 rate limit)
NEXON_TRANSIENT_CODES = frozenset({429, 500, 502, 503, 504})

# 영구 에러 (재시도해도 같은 결과)
NEXON_PERMANENT_CODES = frozenset({400, 401, 403, 404})


def _raise_for_failed_nexon(response: httpx.Response, error_detail: str) -> None:
    code = response.status_code
    body_preview = ((response.text or "").strip())[:300]
    detail = f"{error_detail} (nexon HTTP {code})"
    if body_preview:
        detail = f"{detail}: {body_preview}"

    # 일시 에러: 원본 코드 유지하여 호출부에서 재시도 판단 가능
    if code in NEXON_TRANSIENT_CODES:
        raise HTTPException(status_code=code, detail=detail)

    # 영구 에러: 사용자 잘못이거나 영구적 차단 — 재시도 무의미
    if code in NEXON_PERMANENT_CODES:
        raise HTTPException(status_code=code, detail=detail)

    # 그 외 알 수 없는 코드 → 502로 통합
    raise HTTPException(status_code=502, detail=detail)


async def _get_json(
    client: httpx.AsyncClient,
    path: str,
    params: dict[str, str],
    error_detail: str,
    *,
    not_found_detail: str | None = None,
) -> dict:
    response = await client.get(
        f"{BASE_URL}/{path}",
        headers=HEADERS,
        params=params,
    )
    if response.status_code != 200:
        if not_found_detail is not None and response.status_code == 404:
            raise HTTPException(status_code=404, detail=not_found_detail)
        _raise_for_failed_nexon(response, error_detail)
    return response.json()


async def get_ocid(client: httpx.AsyncClient, nickname: str) -> str:
    data = await _get_json(
        client,
        "id",
        {"character_name": nickname},
        "캐릭터 ID 조회 실패",
        not_found_detail=f"'{nickname}' 캐릭터를 찾을 수 없습니다.",
    )
    ocid = data.get("ocid")
    if not ocid:
        raise HTTPException(status_code=502, detail="넥슨 ID 응답에 ocid가 없습니다.")
    return ocid


async def _fetch_ocid_date(
    client: httpx.AsyncClient,
    subpath: str,
    ocid: str,
    error_detail: str,
    date: str | None = None,
) -> dict:
    d = _explicit_query_date(date)
    if d is not None:
        return await _get_json(
            client, subpath, {"ocid": ocid, "date": d}, error_detail
        )

    params: dict[str, str] = {"ocid": ocid}
    data = await _get_json(client, subpath, params, error_detail)
    if isinstance(data, dict) and _needs_date_retry_after_omit(subpath, data):
        data = await _get_json(
            client,
            subpath,
            {**params, "date": get_yesterday()},
            error_detail,
        )
    return data


async def fetch_character_skill(
    client: httpx.AsyncClient,
    ocid: str,
    character_skill_grade: str,
    date: str | None = None,
) -> dict:
    d = _explicit_query_date(date)
    base: dict[str, str] = {
        "ocid": ocid,
        "character_skill_grade": character_skill_grade,
    }
    if d is not None:
        return await _get_json(
            client,
            "character/skill",
            {**base, "date": d},
            f"캐릭터 스킬 조회 실패 (grade={character_skill_grade})",
        )

    data = await _get_json(
        client,
        "character/skill",
        base,
        f"캐릭터 스킬 조회 실패 (grade={character_skill_grade})",
    )
    if isinstance(data, dict):
        for k in ("character_skill", "characterSkill"):
            if k in data and data[k] is None:
                data = await _get_json(
                    client,
                    "character/skill",
                    {**base, "date": get_yesterday()},
                    f"캐릭터 스킬 조회 실패 (grade={character_skill_grade})",
                )
                break
    return data


async def fetch_character_basic(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/basic", ocid, "캐릭터 기본 정보 조회 실패", date
    )


async def fetch_character_stat(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/stat", ocid, "캐릭터 스탯 조회 실패", date
    )


async def fetch_character_hexamatrix_stat(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client,
        "character/hexamatrix-stat",
        ocid,
        "캐릭터 HEXA 매트릭스 스탯 조회 실패",
        date,
    )


async def fetch_character_hexamatrix(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client,
        "character/hexamatrix",
        ocid,
        "캐릭터 HEXA 매트릭스 조회 실패",
        date,
    )


async def fetch_character_vmatrix(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client,
        "character/vmatrix",
        ocid,
        "캐릭터 V매트릭스 조회 실패",
        date,
    )


async def fetch_character_link_skill(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client,
        "character/link-skill",
        ocid,
        "캐릭터 링크 스킬 조회 실패",
        date,
    )


async def fetch_character_ability(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/ability", ocid, "어빌리티 조회 실패", date
    )


async def fetch_character_popularity(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/popularity", ocid, "캐릭터 인기도 조회 실패", date
    )


async def fetch_union(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "user/union", ocid, "유니온 정보 조회 실패", date
    )


async def fetch_union_raider(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "user/union-raider", ocid, "유니온 공격대 정보 조회 실패", date
    )


async def fetch_union_artifact(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "user/union-artifact", ocid, "유니온 아티팩트 정보 조회 실패", date
    )


async def fetch_union_champion(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "user/union-champion", ocid, "유니온 챔피언 정보 조회 실패", date
    )


async def fetch_overall_ranking(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    """종합 랭킹만 넥슨 조회일이 필요해, date 미지정 시 항상 get_yesterday()를 쿼리에 넣음."""
    d = _explicit_query_date(date) or get_yesterday()
    return await _get_json(
        client,
        "ranking/overall",
        {"ocid": ocid, "date": d},
        "종합 랭킹 조회 실패",
    )


async def fetch_item_equipment(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/item-equipment", ocid, "장비 정보 조회 실패", date
    )


async def fetch_set_effect(
    client: httpx.AsyncClient, ocid: str, date: str | None = None
) -> dict:
    return await _fetch_ocid_date(
        client, "character/set-effect", ocid, "세트효과 조회 실패", date
    )


async def fetch_notice_list(client: httpx.AsyncClient) -> dict:
    return await _get_json(client, "notice", {}, "공지 목록 조회 실패")


async def fetch_notice_update_list(client: httpx.AsyncClient) -> dict:
    return await _get_json(client, "notice-update", {}, "업데이트 공지 목록 조회 실패")


async def fetch_notice_event_list(client: httpx.AsyncClient) -> dict:
    return await _get_json(client, "notice-event", {}, "이벤트 공지 목록 조회 실패")


async def fetch_notice_cashshop_list(client: httpx.AsyncClient) -> dict:
    return await _get_json(client, "notice-cashshop", {}, "캐시샵 공지 목록 조회 실패")