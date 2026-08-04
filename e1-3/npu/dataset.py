"""data.json 로드 및 스키마 검증/판정.

키 규칙(size_{N}_{idx})을 해석해 해당 필터를 고르고, 스키마·크기·라벨 문제가
있어도 예외를 밖으로 던지지 않고 케이스 단위 FAIL 로 처리한다.
"""

import json
import os

from .core import (
    LABEL_CROSS,
    LABEL_X,
    LABEL_UNDECIDED,
    normalize_label,
    matrix_size,
    mac_2d,
    judge,
)

# data.json 위치: 이 파일은 <프로젝트루트>/npu/dataset.py 이므로 한 단계 위가 루트.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.json")


def load_data(path):
    """data.json 을 읽어 파이썬 딕셔너리로 반환한다.

    파일이 없거나 JSON 파싱에 실패하면 예외를 그대로 올려 상위에서 안내한다.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_size_from_key(key):
    """'size_5_1' 형태의 패턴 키에서 크기 N(정수)을 추출한다."""
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise ValueError("패턴 키 형식 오류: {!r}".format(key))
    return int(parts[1])


def pattern_sort_key(key):
    """패턴 키를 (N, idx) 기준으로 자연 정렬하기 위한 보조 키."""
    parts = key.split("_")
    try:
        return (int(parts[1]), int(parts[2]))
    except (IndexError, ValueError):
        return (0, key)


def normalize_filters(raw_filters):
    """filters 원본을 {N: {'Cross': matrix, 'X': matrix}} 구조로 정규화한다.

    필터 키('cross'/'x')를 표준 라벨로 정규화한다.
    """
    normalized = {}
    for size_key, filt_pair in raw_filters.items():
        n = parse_size_from_key(size_key)
        std_pair = {}
        for label_key, matrix in filt_pair.items():
            std_pair[normalize_label(label_key)] = matrix
        normalized[n] = std_pair
    return normalized


def analyze_pattern(pattern_id, entry, filters):
    """패턴 1건을 분석해 결과 딕셔너리를 반환한다.

    스키마/크기 문제나 라벨 문제가 있어도 예외를 밖으로 던지지 않고
    status='FAIL' 과 reason 을 담아 반환한다(프로그램 비정상 종료 방지).
    """
    result = {
        "id": pattern_id,
        "cross": None,
        "x": None,
        "verdict": None,
        "expected": None,
        "status": "FAIL",
        "reason": "",
    }
    try:
        n = parse_size_from_key(pattern_id)
        pattern = entry["input"]
        expected = normalize_label(entry["expected"])
        result["expected"] = expected

        if n not in filters:
            result["reason"] = "size_{0} 필터가 없습니다".format(n)
            return result

        pair = filters[n]
        # 패턴이 정사각인지, 필터와 크기가 일치하는지 검증.
        p_size = matrix_size(pattern)
        if p_size != n:
            result["reason"] = (
                "크기 불일치: 키의 N={0} vs 패턴 {1}x{1}".format(n, p_size)
            )
            return result

        score_cross = mac_2d(pattern, pair[LABEL_CROSS])
        score_x = mac_2d(pattern, pair[LABEL_X])
        result["cross"] = score_cross
        result["x"] = score_x

        verdict = judge(score_cross, score_x)
        result["verdict"] = verdict

        if verdict == LABEL_UNDECIDED:
            result["reason"] = "동점(UNDECIDED) 규칙에 따라 FAIL"
        elif verdict == expected:
            result["status"] = "PASS"
        else:
            result["reason"] = "판정({0}) != expected({1})".format(
                verdict, expected
            )
    except (KeyError, ValueError, TypeError) as exc:
        result["reason"] = "스키마/데이터 오류: {0}".format(exc)
    return result
