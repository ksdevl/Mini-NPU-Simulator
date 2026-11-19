import time
from main import mac_operation, flatten_matrix, mac_operation_1d

# 1. 테스트 데이터 입력
pattern = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
]

filter_matrix = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
]

# 2. 2D 데이터를 1D로 변환
pattern_1d = flatten_matrix(pattern)
filter_1d = flatten_matrix(filter_matrix)

# 3. 계산 결과 확인
score_2d = mac_operation(pattern, filter_matrix)
score_1d = mac_operation_1d(pattern_1d, filter_1d)

# 4. 실행 시간 측정
repeat = 1000

start = time.perf_counter()
for _ in range(repeat):
    mac_operation(pattern, filter_matrix)
time_2d = (time.perf_counter() - start) / repeat * 1000

start = time.perf_counter()
for _ in range(repeat):
    mac_operation_1d(pattern_1d, filter_1d)
time_1d = (time.perf_counter() - start) / repeat * 1000

# 5. 결과 출력
print("===== 2D / 1D 배열 비교 =====")
print(f"2D 계산 결과: {score_2d}")
print(f"1D 계산 결과: {score_1d}")
print(f"2D 평균 실행 시간: {time_2d:.6f} ms")
print(f"1D 평균 실행 시간: {time_1d:.6f} ms")
print(f"계산 결과 일치: {score_2d == score_1d}")