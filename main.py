"""
Mini-NPU-Simulator
Python 3.8+
표준 라이브러리만 사용하며 MAC 연산은 중첩 반복문으로 직접 구현합니다.
"""

import json
import math
import time
from pathlib import Path

EPSILON = 1e-9
MIN_REPEAT = 10
DATA_FILE = Path(__file__).with_name("data.json")


def normalize_label(value):
    """입력 라벨을 Cross 또는 X로 통일합니다."""
    if not isinstance(value, str):
        raise ValueError("라벨은 문자열이어야 합니다.")

    value = value.strip().lower()

    if value in ("+", "cross"):
        return "Cross"
    if value == "x":
        return "X"

    raise ValueError("지원하지 않는 라벨입니다: {!r}".format(value))


def extract_size(pattern_key):
    """size_13_2 형식의 키에서 크기 13을 추출합니다."""
    parts = pattern_key.split("_")

    if len(parts) != 3 or parts[0] != "size":
        raise ValueError("잘못된 패턴 키 형식: {}".format(pattern_key))

    if not parts[1].isdigit() or not parts[2].isdigit():
        raise ValueError("패턴 키의 크기와 번호는 숫자여야 합니다.")

    size = int(parts[1])
    if size <= 0:
        raise ValueError("배열 크기는 양수여야 합니다.")

    return size


def validate_matrix(matrix, size, matrix_name="matrix"):
    """정사각형 N×N 숫자 행렬인지 검사합니다."""
    if not isinstance(matrix, list) or len(matrix) != size:
        raise ValueError("{}: 행 개수가 {}이어야 합니다.".format(matrix_name, size))

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(
                "{}: {}번째 행의 열 개수가 {}이어야 합니다.".format(
                    matrix_name, row_index + 1, size
                )
            )

        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    "{}: [{}, {}] 값은 숫자여야 합니다.".format(
                        matrix_name, row_index, col_index
                    )
                )
            if not math.isfinite(value):
                raise ValueError(
                    "{}: [{}, {}] 값은 유한한 숫자여야 합니다.".format(
                        matrix_name, row_index, col_index
                    )
                )

    return True


def mac_operation(pattern, filter_matrix):
    """Multiply-Accumulate: 두 행렬의 같은 위치 원소를 곱해 모두 더합니다."""
    size = len(pattern)
    score = 0.0

    for row in range(size):
        for col in range(size):
            score += pattern[row][col] * filter_matrix[row][col]

    return score

def mac_operation_1d(pattern, filter_array):
    """1차원 배열을 사용한 MAC 연산"""
    score = 0.0

    for i in range(len(pattern)):
        score += pattern[i] * filter_array[i]

    return score

def flatten_matrix(matrix):
    """2차원 행렬을 1차원 배열로 변환"""
    return [value for row in matrix for value in row]

def classify_scores(score_cross, score_x):
    """점수 차이가 epsilon 미만이면 UNDECIDED로 판정합니다."""
    if abs(score_cross - score_x) < EPSILON:
        return "UNDECIDED"
    if score_cross > score_x:
        return "Cross"
    return "X"


def measure_average_ms(pattern, filter_matrix, repeat=MIN_REPEAT):
    """MAC 연산을 반복 측정하고 1회 평균 시간을 ms로 반환합니다."""
    repeat = max(MIN_REPEAT, int(repeat))

    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation(pattern, filter_matrix)
    elapsed = time.perf_counter() - start

    return (elapsed / repeat) * 1000.0


def input_matrix(size, name):
    """사용자에게 N줄의 행렬을 입력받고 올바른 값인지 검사합니다."""
    print("\n[{}: {}×{}]".format(name, size, size))
    matrix = []

    while len(matrix) < size:
        row_number = len(matrix) + 1
        raw = input("{}번째 행 (숫자 {}개, 공백 구분): ".format(row_number, size))

        try:
            values = [float(token) for token in raw.split()]
            if len(values) != size:
                print("입력 오류: 숫자 {}개를 입력하세요.".format(size))
                continue
            if not all(math.isfinite(value) for value in values):
                print("입력 오류: NaN 또는 무한대는 입력할 수 없습니다.")
                continue
            matrix.append(values)
        except ValueError:
            print("입력 오류: 숫자만 입력하세요.")

    return matrix


def run_mode_1():
    """3×3 필터 A/B와 패턴을 입력받아 유사도를 비교합니다."""
    size = 3
    filter_a = input_matrix(size, "필터 A")
    filter_b = input_matrix(size, "필터 B")
    pattern = input_matrix(size, "입력 패턴")

    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    result = classify_scores(score_a, score_b)

    time_a = measure_average_ms(pattern, filter_a)
    time_b = measure_average_ms(pattern, filter_b)

    print("\n========== 모드 1 결과 ==========")
    print("필터 A 점수: {:.6f}".format(score_a))
    print("필터 B 점수: {:.6f}".format(score_b))
    print("판정 결과: {}".format(result))
    print("필터 A 평균 연산 시간: {:.6f} ms".format(time_a))
    print("필터 B 평균 연산 시간: {:.6f} ms".format(time_b))


def load_json_data():
    """data.json을 UTF-8로 읽습니다."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("오류: data.json 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as error:
        print("오류: JSON 형식이 올바르지 않습니다: {}".format(error))
        return None
    except OSError as error:
        print("오류: 파일을 읽을 수 없습니다: {}".format(error))
        return None

    if not isinstance(data, dict):
        print("오류: JSON 최상위 구조는 객체여야 합니다.")
        return None

    return data


def get_normalized_filters(filter_data, size):
    """필터 키를 Cross/X로 정규화하고 행렬 크기를 검증합니다."""
    if not isinstance(filter_data, dict):
        raise ValueError("filters.size_{}는 객체여야 합니다.".format(size))

    normalized = {}
    for raw_label, matrix in filter_data.items():
        label = normalize_label(raw_label)
        if label in normalized:
            raise ValueError("중복된 필터 라벨: {}".format(label))
        validate_matrix(matrix, size, "{} filter".format(label))
        normalized[label] = matrix

    if "Cross" not in normalized or "X" not in normalized:
        raise ValueError("Cross와 X 필터가 모두 필요합니다.")

    return normalized


def analyze_one_case(pattern_key, item, all_filters):
    """JSON의 테스트 케이스 하나를 분석합니다."""
    size = extract_size(pattern_key)

    if not isinstance(item, dict):
        raise ValueError("패턴 데이터는 객체여야 합니다.")
    if "input" not in item or "expected" not in item:
        raise ValueError("input 또는 expected 항목이 없습니다.")
    if not isinstance(all_filters, dict):
        raise ValueError("filters 항목이 올바르지 않습니다.")

    filter_key = "size_{}".format(size)
    if filter_key not in all_filters:
        raise ValueError("{} 필터 데이터가 없습니다.".format(filter_key))

    pattern = item["input"]
    validate_matrix(pattern, size, "pattern")
    filters = get_normalized_filters(all_filters[filter_key], size)
    expected = normalize_label(item["expected"])

    cross_score = mac_operation(pattern, filters["Cross"])
    x_score = mac_operation(pattern, filters["X"])
    predicted = classify_scores(cross_score, x_score)

    passed = predicted == expected
    return {
        "key": pattern_key,
        "size": size,
        "cross_score": cross_score,
        "x_score": x_score,
        "predicted": predicted,
        "expected": expected,
        "status": "PASS" if passed else "FAIL",
        "reason": "점수 동점으로 판정 불가" if predicted == "UNDECIDED" else ""
    }


def make_demo_3x3():
    """3×3 성능 측정 전용 예시 행렬을 생성합니다."""
    pattern = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0]
    ]
    cross_filter = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0]
    ]
    return pattern, cross_filter

def generate_cross_filter(size):
    """N×N 크기의 Cross 필터를 생성합니다."""
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("행렬 크기는 양의 정수여야 합니다.")

    center_rows = {(size - 1) // 2, size // 2}

    return [
        [
            1.0 if row in center_rows or col in center_rows else 0.0
            for col in range(size)
        ]
        for row in range(size)
    ]

def generate_x_filter(size):
    """N×N 크기의 X 필터를 생성합니다."""
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("행렬 크기는 양의 정수여야 합니다.")

    return [
        [
            1.0 if row == col or row + col == size - 1 else 0.0
            for col in range(size)
        ]
        for row in range(size)
    ]

def print_matrix(matrix, title):
    """생성된 행렬을 화면에 출력합니다."""
    print("\n{}".format(title))

    for row in matrix:
        print(" ".join("{:g}".format(value) for value in row))

def run_pattern_generator():
    """사용자가 입력한 크기에 맞춰 Cross와 X 필터를 생성합니다."""

    print("\n========== 패턴 자동 생성 ==========")

    while True:
        raw_size = input("생성할 행렬 크기 N을 입력하세요: ").strip()

        try:
            size = int(raw_size)

            if size <= 0:
                print("입력 오류: 1 이상의 정수를 입력하세요.")
                continue

            break

        except ValueError:
            print("입력 오류: 정수만 입력하세요.")

    cross_filter = generate_cross_filter(size)
    x_filter = generate_x_filter(size)

    print_matrix(cross_filter, "Cross 필터 ({}×{})".format(size, size))
    print_matrix(x_filter, "X 필터 ({}×{})".format(size, size))

    print("\n========== 생성 결과 검증 ==========")
    print("Cross 필터 크기: {}×{}".format(
        len(cross_filter), len(cross_filter)
    ))
    print("X 필터 크기: {}×{}".format(
        len(x_filter), len(x_filter)
    ))

    validate_matrix(cross_filter, size, "Cross filter")
    validate_matrix(x_filter, size, "X filter")

    print("Cross 필터 검증: PASS")
    print("X 필터 검증: PASS")

    pattern = cross_filter

    cross_score = mac_operation(pattern, cross_filter)
    x_score = mac_operation(pattern, x_filter)

    result = classify_scores(cross_score, x_score)

    print("\n========== MAC 연산 확인 ==========")
    print("입력 패턴: 생성된 Cross 필터")
    print("Cross 점수: {}".format(cross_score))
    print("X 점수: {}".format(x_score))
    print("판정 결과: {}".format(result))

def run_mode_2():
    """JSON의 모든 패턴을 케이스별로 분석하고 결과를 집계합니다."""
    data = load_json_data()
    if data is None:
        return

    if "filters" not in data or "patterns" not in data:
        print("오류: JSON에 filters 또는 patterns 항목이 없습니다.")
        return
    if not isinstance(data["patterns"], dict):
        print("오류: patterns는 객체여야 합니다.")
        return

    results = []
    failures = []

    print("\n========== 모드 2: JSON 자동 분석 ==========")

    for key, item in data["patterns"].items():
        try:
            result = analyze_one_case(key, item, data["filters"])
            results.append(result)

            print("\n[{}]".format(key))
            print("크기: {}×{}".format(result["size"], result["size"]))
            print("Cross 점수: {:.6f}".format(result["cross_score"]))
            print("X 점수: {:.6f}".format(result["x_score"]))
            print("판정: {}".format(result["predicted"]))
            print("정답: {}".format(result["expected"]))
            print("결과: {}".format(result["status"]))

            if result["status"] == "FAIL":
                failures.append("{}: {}".format(
                    key, result["reason"] or "예상 라벨과 판정 결과 불일치"
                ))

        except (ValueError, TypeError, KeyError) as error:
            failures.append("{}: {}".format(key, error))
            print("\n[{}] FAIL - {}".format(key, error))

    pass_count = sum(1 for result in results if result["status"] == "PASS")
    fail_count = len(failures)
    total_count = len(data["patterns"])

    print("\n========== 최종 결과 요약 ==========")
    print("전체 케이스: {}".format(total_count))
    print("정상 처리 PASS: {}".format(pass_count))
    print("FAIL: {}".format(fail_count))

    if failures:
        print("\n실패 케이스:")
        for failure in failures:
            print("- {}".format(failure))

    print("\n========== 성능 분석 ==========")
    print("{:<10} {:>18} {:>14}".format("크기", "평균 시간(ms)", "MAC 횟수"))
    print("-" * 46)

    # 3×3은 JSON에 없으므로 별도의 예시 행렬로 측정합니다.
    demo_pattern, demo_filter = make_demo_3x3()
    demo_time = measure_average_ms(demo_pattern, demo_filter)
    print("{:<10} {:>18.6f} {:>14}".format("3×3", demo_time, 9))

    # JSON에 실제로 존재하는 크기별 첫 번째 정상 케이스를 이용해 측정합니다.
    measured_sizes = set()
    for result in results:
        size = result["size"]
        if size in measured_sizes:
            continue

        try:
            item = data["patterns"][result["key"]]
            filters = get_normalized_filters(
                data["filters"]["size_{}".format(size)], size
            )
            elapsed = measure_average_ms(item["input"], filters["Cross"])
            print("{:<10} {:>18.6f} {:>14}".format(
                "{}×{}".format(size, size), elapsed, size * size
            ))
            measured_sizes.add(size)
        except (ValueError, TypeError, KeyError):
            print("{:<10} {:>18} {:>14}".format(
                "{}×{}".format(size, size), "측정 불가", size * size
            ))


def main():
    while True:
        print("\n================================")
        print("       Mini-NPU-Simulator")
        print("================================")
        print("1. 모드 1 - 사용자 입력 (3×3)")
        print("2. 모드 2 - JSON 자동 분석")
        print("3. 보너스 - 패턴 자동 생성")
        print("0. 종료")

        choice = input("메뉴 선택: ").strip()

        if choice == "1":
            run_mode_1()
        elif choice == "2":
            run_mode_2()
        elif choice == "3":
            run_pattern_generator()
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 0, 1, 2, 3 중 입력하세요.")
            


if __name__ == "__main__":
    main()
