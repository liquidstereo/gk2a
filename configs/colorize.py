# Gemini 수정: 2025-07-15
# 이 스크립트는 명확성, 일관성, 안정성을 위해 검토 및 수정되었습니다.
#
# 변경 사항 요약:
# 1. 버그 수정 (Msg.Blink): 'stop_event'가 제공되지 않았을 때 바쁜 대기(busy-wait) 루프로 인해 높은 CPU 사용량을 유발하는 심각한 버그를 수정했습니다.
# 2. 버그 수정 (Msg.Blink): 이벤트에 의해 중지된 경우에도 정리 코드(줄 지우기 또는 최종 메시지 인쇄)가 항상 실행되도록 루프 종료 로직을 수정했습니다.
# 3. 리팩토링 (Msg.Blink): docstring과 로직에서 'interval' 매개변수의 명확성을 개선했습니다. 이제 전체 켜짐/꺼짐 주기의 지속 시간을 나타냅니다.
# 4. 일관성 (Msg.Critical): 메서드 이름과 일치하도록 출력 접두사를 "ERROR:"에서 "CRITICAL:"로 변경했습니다.
# 5. 리팩토링 (Msg.Black): 공통 _get_colored_message 헬퍼를 사용하도록 리팩토링하여 코드 일관성을 개선했습니다.
# 6. 정리 (전체): 색상 초기화 시퀀스를 단순화했습니다. Style.RESET_ALL을 사용하는 것이 여러 초기화 코드를 결합하는 것보다 충분하고 더 안정적입니다.

import time, sys
import logging
from threading import Event
from typing import Optional
from colorama import Fore, Back, Style, init
init(autoreset=True)

# COLORAMA: 사용 가능한 서식 상수는 다음과 같습니다:
# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL


class ColorizeLogger:
    # Gemini 수정: 2025-07-15
    # ColorizeLogger 클래스 설명 및 사용법 추가
    #
    # [설명]
    # ColorizeLogger는 Python의 내장 `logging` 모듈과 함께 사용되는
    # 클래스입니다. 로그 레벨(예: DEBUG, INFO, WARNING, ERROR, CRITICAL)에
    # 따라 로그 메시지에 다른 색상을 적용하여, 터미널이나 콘솔에서 로그의
    # 가독성을 높이는 역할을 합니다.
    #
    # 이 클래스는 직접 인스턴스화하여 사용하는 것이 아니라, `logging.Formatter`를
    # 상속받는 사용자 정의 포매터 클래스 내에서 정적 메서드 `format`을 호출하는
    # 방식으로 사용됩니다.
    #
    # [사용법]
    # 1. `logging.Formatter`를 상속받는 사용자 정의 포매터 클래스를 만듭니다.
    # 2. `format` 메서드를 오버라이드(재정의)합니다.
    # 3. 부모 클래스(`logging.Formatter`)의 `format`을 호출하여 기본 로그
    #    메시지를 생성합니다.
    # 4. `ColorizeLogger.format`을 호출하여 생성된 메시지에 색상을 적용합니다.
    # 5. 생성한 사용자 정의 포매터를 로거의 핸들러에 설정합니다.
    #
    # [예시 코드]
    #
    # import logging
    #
    # # 1. 사용자 정의 포매터 클래스 정의
    # class MyCustomFormatter(logging.Formatter):
    #     def __init__(self, fmt=None, datefmt=None, style='%'):
    #         super().__init__(fmt, datefmt, style)
    #
    #     def format(self, record):
    #         # 2. 부모 클래스의 format을 호출하여 기본 포맷팅된 메시지 생성
    #         formatted_message = super().format(record)
    #
    #         # 3. ColorizeLogger를 사용하여 메시지에 색상 적용
    #         return ColorizeLogger.format(record, formatted_message)
    #
    # # 4. 로거 설정
    # logger = logging.getLogger('my_app')
    # logger.setLevel(logging.DEBUG)
    #
    # # 5. 핸들러 및 포매터 생성/설정
    # handler = logging.StreamHandler()
    # # MyCustomFormatter 사용
    # formatter = MyCustomFormatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    # handler.setFormatter(formatter)
    #
    # # 6. 핸들러를 로거에 추가 (중복 추가 방지)
    # if not logger.handlers:
    #     logger.addHandler(handler)
    #
    # # 7. 로그 메시지 출력 테스트
    # # logger.debug("이것은 디버그 메시지입니다.")
    # # logger.info("이것은 정보 메시지입니다.")
    # # logger.warning("이것은 경고 메시지입니다.")
    # # logger.error("이것은 에러 메시지입니다.")
    # # logger.critical("이것은 심각한 오류 메시지입니다.")
    '''
    ◦ 로그 레벨에 따라 로그 색상을 적용합니다.

    Args:
        record (logging.LogRecord): 로그 레코드.
        message (str): 로그 메시지.

    Returns:
        str
    '''""

    LEVEL_COLORS={
        'DEBUG':Style.DIM,
        'INFO':Fore.WHITE,
        'WARNING':Fore.YELLOW,
        'ERROR':Fore.RED,
        'CRITICAL':Fore.MAGENTA,
    }

    @staticmethod
    def format(record:logging.LogRecord, message:str) -> str:
        """ 로그 레벨에 따라 로그 색상을 적용합니다. """
        color=ColorizeLogger.LEVEL_COLORS.get(record.levelname, '')
        return f"{color}{message}{Style.RESET_ALL}"



class Msg:
    '''
    ◦ COLORAMA를 사용하여 출력 문자열의 색상을 설정합니다.
    '''

    # =========================================================================== #

    @staticmethod
    def Debug(message: str, divide: bool = False):
        m = f'{Style.DIM}DEBUG:{message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    @staticmethod
    def Info(message: str, divide: bool = False):
        m = f'{Fore.GREEN}{Style.BRIGHT}INFO:{message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    @staticmethod
    def Warning(message: str, divide: bool = True):
        m = f'{Back.YELLOW}{Fore.BLACK}WARNING:{message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    @staticmethod
    def Confirm(message: str, divide: bool = True):
        m = f'{Back.CYAN}{Fore.BLACK}CONFIRM:{message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    @staticmethod
    def Error(message: str, divide: bool = True):
        # 수정됨: 초기화 시퀀스를 단순화했습니다.
        m = f'{Back.RED}{Fore.WHITE}ERROR: {message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    @staticmethod
    def Critical(message: str, divide: bool = True):
        # 수정됨: "ERROR:"를 "CRITICAL:"로 변경하고 초기화를 단순화했습니다.
        m = f'{Back.RED}{Fore.BLACK}CRITICAL:{message}{Style.RESET_ALL}'
        if divide:
            m = f'-\n{m}\n-'
        print(m)

    # =========================================================================== #

    @staticmethod
    def Dim(
        message: str, verbose: bool = False, flush: bool = False,
        divide: bool = False
    ):
        res = f'{Style.DIM}{message}{Style.RESET_ALL}'
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res

        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Alert(message: str, verbose: bool = False, divide: bool = True):
        res = f'{Fore.RED}{Style.BRIGHT}{message}{Style.RESET_ALL}'
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        print(res)
        return None

    @staticmethod
    def Result(message: str, divide: bool = True, verbose: bool = False):
        # 수정됨: 초기화 시퀀스를 단순화했습니다.
        m = (
            f'{Back.YELLOW}'
            f'{Fore.BLACK}'
            f'{message}'
            f'{Style.RESET_ALL}'
        )
        if divide:
            m = f'-\n{m}\n-'
        return m if verbose else print(m)

    @staticmethod
    def _get_colored_message(
        message: str, fore_color: str, back_color: str = '',
        verbose: bool = False, plain: bool = True,
        flush: bool = False,
        default_color: str = Fore.WHITE
    ) -> str | None:
        '''
        ◦ 메시지에 색상과 스타일을 적용하고 반환하거나 인쇄합니다.
        '''
        # 수정됨: 초기화 시퀀스를 단순화했습니다. Style.RESET_ALL로 충분합니다.
        if plain:
            res = f'{fore_color}{message}{Style.RESET_ALL}'
        else:
            back_start = back_color if back_color else ''
            res = (f'{back_start}{default_color}{Style.BRIGHT}{message}'
                   f'{Style.RESET_ALL}')

        if verbose:
            return res

        print(res, end='\r' if flush else '\n', flush=flush)
        return None

    @staticmethod
    def Red(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.RED, Back.RED, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Yellow(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.YELLOW, Back.YELLOW, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Green(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.GREEN, Back.GREEN, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Blue(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.BLUE, Back.BLUE, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Cyan(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.CYAN, Back.CYAN, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Magenta(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.MAGENTA, Back.MAGENTA, True, plain, flush
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def White(
        message: str, verbose: bool = False, plain: bool = False,
        flush: bool = False, divide: bool = False
    ):
        res = Msg._get_colored_message(
            message, Fore.WHITE, Back.WHITE, True, plain, flush,
            default_color=Fore.BLACK
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    @staticmethod
    def Black(
        message: str, verbose: bool = False, plain: bool = True,
        flush: bool = False, divide: bool = False
    ):
        # 리팩토링됨: 일관성을 위해 공통 _get_colored_message 헬퍼를 사용합니다.
        res = Msg._get_colored_message(
            message, Fore.BLACK, Back.WHITE, True, plain, flush,
            default_color=Fore.BLACK
        )
        if divide:
            res = f'-\n{res}\n-'
        if verbose:
            return res
        use_flush = flush and not divide
        print(res, end='\r' if use_flush else '\n', flush=use_flush)
        return None

    # ========================= 깜박임 ========================= #

    @staticmethod
    def Blink(message: str, duration:float=30.0, interval:float=0.5,
              color:str='red', verbose:bool=False, clear_on_finish:bool=True,
              stop_event: Optional[Event] = None) -> None:
        '''
        ◦ 터미널에서 메시지를 깜박입니다.

        Args:
            message (str): 깜박일 메시지.
            duration (float): stop_event가 제공되지 않은 경우 깜박임을 유지할 총 시간(초).
            interval (float): 리팩토링됨: 한 번의 전체 켜짐/꺼짐 주기에 대한 총 시간(초).
            color (str): 사용할 colorama.Fore 색상 이름 (예: "RED", "YELLOW").
            verbose (bool): True이면 색상이 적용된 문자열을 반환하고, 그렇지 않으면 콘솔에서 깜박입니다.
            clear_on_finish (bool): True이면 깜박임이 멈춘 후 메시지를 지웁니다.
            stop_event (Optional[threading.Event]): 외부에서 깜박임을 중지시키는 이벤트.
        '''
        # 버그 수정: 이 전체 메서드는 주요 버그를 수정하기 위해 다시 작성되었습니다:
        # 1. `stop_event`가 None일 때 높은 CPU 사용량을 유발하는 바쁜 대기(busy-wait) 루프.
        # 2. 최종 정리 로직을 건너뛰는 루프 `break` 문.
        # 3. `interval`의 의미가 모호하여 명확히 했습니다.
        try:
            actual_fore_color = getattr(Fore, color.upper())
        except AttributeError:
            actual_fore_color = Fore.RESET

        if verbose:
            return f"{actual_fore_color}{message}{Style.RESET_ALL}"

        end_time = time.time() + duration
        half_interval = interval / 2.0
        if half_interval <= 0: # 0으로 나누거나 음수 시간 동안 대기하는 것을 방지합니다.
            half_interval = 0.25

        # 중지 조건이 충족될 때까지 반복합니다.
        while True:
            if stop_event and stop_event.is_set():
                break
            if not stop_event and time.time() >= end_time:
                break

            # 메시지 표시
            sys.stdout.write(f"{actual_fore_color}{message}\r")
            sys.stdout.flush()

            # 주기적으로 이벤트를 확인하며 절반의 간격 동안 대기합니다.
            if stop_event:
                if stop_event.wait(half_interval): break
            else:
                time.sleep(half_interval)

            # 공백으로 덮어써서 메시지를 숨깁니다.
            sys.stdout.write(f"\r{' ' * len(message)}\r")
            sys.stdout.flush()

            # 나머지 절반의 간격 동안 대기합니다.
            if stop_event:
                if stop_event.wait(half_interval): break
            else:
                time.sleep(half_interval)

        # 최종 정리 작업
        if clear_on_finish:
            sys.stdout.write(f"\r{' ' * len(message)}\r")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"{actual_fore_color}{message}{Style.RESET_ALL}\n")
            sys.stdout.flush()
