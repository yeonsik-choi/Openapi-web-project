"""'역대 썬데이메이플 정리' 텍스트를 대시보드용 JSON으로 변환한다.

사용법:
    python tools/build_sunday_cycles.py [원본.txt] [출력.json]

기본 경로는 아래 SRC / OUT 이며, 원본 글이 갱신될 때마다 다시 실행하면 된다.
"""

import json
import re
import sys
from pathlib import Path

SRC = Path.home() / "Desktop" / "역대 썬데이 메이플 정리.txt"
# .json이 아니라 .js로 내보낸다. fetch는 file://에서 막히지만 <script src>는 열리므로,
# 로컬에서 HTML을 그냥 더블클릭해도 대시보드가 뜬다.
OUT = Path(__file__).resolve().parent.parent / "frontend" / "data" / "sunday-cycles.js"

# 종류별: "(+84일)2024.10.13(샤이닝 스타포스 타임)" / "2024.07.21"
TYPE_DATE_RE = re.compile(r"^(?:\(\+(\d+)일\))?(\d{4}\.\d{2}\.\d{2})(.*)$")
# 날짜별: "2018.04.01 (헤이스트)" / "2024.04.01(월) (메이플 운영자의 특별한 선물 받기!)" / "2017.03.19"
DAY_HEAD_RE = re.compile(r"^(\d{4}\.\d{2}\.\d{2})(?:\(([월화수목금토일])\))?(?:\s+(.*))?$")
# 날짜별 특수 주간: "2023.01.12~2023.01.18 <요정 웡키의 웡스토랑 - 마이크의 파워업 위크>"
DAY_RANGE_RE = re.compile(r"^(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})(?:\s+(.*))?$")
# 특수 주간에 속한 하루: "2023.01.14(토) - 스타포스 5, 10, 15성에서 ..."
RANGE_DAY_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\([월화수목금토일]\)\s*-\s*\S")

NO_EVENT = {"없음", "아예 없음"}


def parse_season(label):
    """'(헤이스트)' -> ('헤이스트', False), '<검은마법사>' -> ('검은마법사', True)"""
    if not label:
        return None, False
    label = label.strip()
    if label.startswith("<") and label.endswith(">"):
        return label[1:-1], True
    if label.startswith("(") and label.endswith(")"):
        inner = label[1:-1]
        return (None, False) if inner == "-" else (inner, False)
    return label, False


def parse_types(lines):
    types = []
    cur = None
    for raw in lines:
        line = raw.rstrip()
        if not line or line.lstrip().startswith("->"):  # 빈 줄 / 명칭 변경 안내 줄
            continue
        if line.startswith("- "):
            name = line[2:].strip()
            active = not name.startswith("(단종)")
            if not active:
                name = name[len("(단종)"):]
            cur = {"name": name, "active": active, "dates": [], "notes": {}}
            types.append(cur)
            continue
        m = TYPE_DATE_RE.match(line)
        if not m or cur is None:
            raise ValueError(f"종류별 파싱 실패: {line!r}")
        date, suffix = m.group(2), m.group(3).strip()
        cur["dates"].append(date)
        if suffix:
            cur["notes"][date] = suffix
    for t in types:
        if not t["notes"]:
            del t["notes"]
    return types


def parse_days(lines):
    days = []
    cur = None
    for raw in lines:
        line = raw.rstrip()
        if not line:
            continue
        m = DAY_RANGE_RE.match(line)
        if m:
            season, big = parse_season(m.group(3))
            cur = {"date": m.group(1), "until": m.group(2), "season": season,
                   "big": big, "count": 0}
            days.append(cur)
            continue
        # 특수 주간 안의 하루는 새 항목이 아니라 그 주간의 혜택 1건으로 센다
        if cur is not None and "until" in cur and RANGE_DAY_RE.match(line):
            cur["count"] += 1
            continue
        m = DAY_HEAD_RE.match(line)
        if m:
            season, big = parse_season(m.group(3))
            cur = {"date": m.group(1), "season": season, "big": big, "count": 0}
            if m.group(2):
                cur["weekday"] = m.group(2)
            days.append(cur)
            continue
        if cur is None:
            raise ValueError(f"날짜별 파싱 실패: {line!r}")
        if line not in NO_EVENT:
            cur["count"] += 1
    for d in days:
        if not d["big"]:
            del d["big"]
        if d["season"] is None:
            del d["season"]
    return days


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT

    lines = src.read_text(encoding="utf-8").splitlines()
    i_types = next(i for i, l in enumerate(lines) if l.strip() == "종류별(가나다순)")
    i_days = next(i for i, l in enumerate(lines) if l.strip() == "날짜별")

    head = "\n".join(lines[:i_types])
    m = re.search(r"최신 갱신일\s*:\s*(\d{4}\.\d{2}\.\d{2})", head)
    source_updated = m.group(1) if m else None
    m = re.search(r"기준일\s*:\s*(\d{4}\.\d{2}\.\d{2})", head)
    base_date = m.group(1) if m else None

    data = {
        "sourceUpdated": source_updated,
        "baseDate": base_date,
        "types": parse_types(lines[i_types + 1:i_days]),
        "sundays": parse_days(lines[i_days + 1:]),
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text(f"window.SUNDAY_CYCLES = {body};\n", encoding="utf-8")

    n_dates = sum(len(t["dates"]) for t in data["types"])
    n_active = sum(1 for t in data["types"] if t["active"])
    print(f"{out} 생성 완료")
    print(f"  혜택 {len(data['types'])}종 (현역 {n_active} / 단종 {len(data['types']) - n_active})")
    print(f"  등장 기록 {n_dates}건, 썬데이 {len(data['sundays'])}회")
    print(f"  원본 갱신일 {source_updated} / 기준일 {base_date}")


if __name__ == "__main__":
    main()
