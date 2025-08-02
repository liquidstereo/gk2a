import time
from datetime import timedelta
from typing import Optional


class Etimer:
    """간단하고 강력한 타이머 클래스"""

    def __init__(self, auto_start: bool=True):
        self.start_t: Optional[float]=None
        if auto_start:
            self.start()

    def start(self) -> 'Etimer':
        """타이머 시작"""
        self.start_t=time.perf_counter()
        return self

    def elapsed_sec(self, p: int=4, plain: bool=True) -> str:   # ← elapsed (seconds)
        """경과 시간 반환"""
        if self.start_t is None:
            return "(TIMER NOT STARTED)"

        t=time.perf_counter() - self.start_t
        return f'{t:.{p}f}' if plain else f'(ELAPSED TIME: {t:.{p}f} ms)'

    def elapsed_ms(self, p: int=2, plain: bool=True) -> str:    # ← elapsed (miliseconds)
        """경과 시간을 밀리초로 반환"""
        if self.start_t is None:
            return "(TIMER NOT STARTED)"

        t=(time.perf_counter() - self.start_t) * 1000
        return f'{t:.{p}f}' if plain else f'(ELAPSED TIME: {t:.{p}f} ms)'

    def elapsed(self, p: int=3, plain: bool=True) -> str:    # ← elapsed (timecode)
        """경과 시간을 시:분:초.밀리초 형식으로 반환"""
        if self.start_t is None:
            return "(TIMER NOT STARTED)"

        t=time.perf_counter() - self.start_t
        s=str(timedelta(seconds=t))

        # 소수점 정밀도 조정
        if '.' in s:
            base, dec=s.split('.')
            s=f"{base}.{dec[:p]}"

        # return f'(ELAPSED TIME: {s})'
        return s if plain else f'(ELAPSED TIME: {s})'

    def reset(self) -> 'Etimer':
        """타이머 리셋"""
        self.start_t=time.perf_counter()
        return self

    def get_seconds(self) -> float:
        """순수한 초 값만 반환"""
        if self.start_t is None:
            return 0.0
        return time.perf_counter() - self.start_t


# 사용 예시
if __name__ == "__main__":
    # 기본 사용법
    timer=Etimer()
    time.sleep(0.1)
    print(timer.elapsed_sec())      # (ELAPSED TIME: 0.1001 Sec.)
    print(timer.elapsed_ms())   # (ELAPSED TIME: 100.12 ms)
    print(timer.elapsed())  # (ELAPSED TIME: 0:00:00.100)

    # 메서드 체이닝
    another_timer=Etimer().start()
    time.sleep(0.05)
    print(another_timer.elapsed(2))  # (ELAPSED TIME: 0.05 Sec.)

    # 순수한 숫자 값
    print(f"순수 시간: {timer.get_seconds():.6f}초")