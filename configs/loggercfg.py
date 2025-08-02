# Gemini 수정: 2025-07-21
# - CustomFileFormatter의 로그 형식을 '시간 | 레벨 | 파일명 > 함수명 | 메시지'로 변경
# - Logger 클래스의 로그 메서드(info, error 등)에 stacklevel=2를 추가하여 정확한 호출 위치 기록

import os
import queue
import logging
import atexit
from logging.handlers import (RotatingFileHandler, QueueHandler, QueueListener)
from typing import Optional

# 컬러 로깅을 위해 colorize 모듈에서 ColorizeLogger를 가져옵니다.
try:
    from .colorize import ColorizeLogger
except ImportError:
    class ColorizeLogger:
        @staticmethod
        def format(record, message): return message

class CustomFileFormatter(logging.Formatter):
    """파일 로그를 위한 사용자 정의 포맷을 적용하는 포매터"""
    def __init__(self, fmt=None, datefmt=None, style='%'):
        # fmt = '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(filename)s > %(funcName)s | %(message)s'     # ← 파일명 > 함수명으로 기록됨
        fmt = '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s > %(funcName)s | %(message)s'    # ← 모듈명 > 함수명으로 기록됨
        datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt, style)

class CustomConsoleFormatter(logging.Formatter):
    """콘솔 출력을 위해 ColorizeLogger를 사용하는 포매터"""
    def __init__(self, fmt=None, datefmt=None, style='%'):
        fmt = '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        formatted_message = super().format(record)
        return ColorizeLogger.format(record, formatted_message)

class Logger:
    """
    스레드에 안전한 큐 기반 파일 및 콘솔 로거입니다.
    로거 이름을 기준으로 싱글톤으로 동작합니다.
    """
    _loggers = {}

    def __new__(cls, name: str, log_fpath: str = None, show: bool=False):
        if name not in cls._loggers:
            instance = super().__new__(cls)
            cls._loggers[name] = instance
            instance._initialized = False
        return cls._loggers[name]

    def __init__(self, name: str, log_path: str = None, show: bool=False):
        if self._initialized:
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if show:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(CustomConsoleFormatter())
            self.logger.addHandler(console_handler)

        # # 기존 코드의 listener 부분을 다음과 같이 수정
        # if log_path:
        #     log_dir = os.path.dirname(log_path)
        #     if log_dir:
        #         os.makedirs(log_dir, exist_ok=True)

        #     log_queue = queue.Queue(-1)
        #     file_handler = RotatingFileHandler(
        #         log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        #     )
        #     file_handler.setFormatter(CustomFileFormatter())

        #     queue_handler = QueueHandler(log_queue)
        #     self.listener = QueueListener(log_queue, file_handler)

        #     # listener가 제대로 시작되었는지 확인
        #     try:
        #         self.listener.start()
        #         self.logger.addHandler(queue_handler)
        #         atexit.register(self.shutdown)
        #     except Exception as e:
        #         # listener 시작에 실패하면 직접 파일 핸들러 사용
        #         self.listener = None
        #         self.logger.addHandler(file_handler)
        # else:
        #     self.listener = None  # log_path가 없으면 listener도 None으로 설정




        if log_path:
            log_dir = os.path.dirname(log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            log_queue = queue.Queue(-1)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(CustomFileFormatter())

            queue_handler = QueueHandler(log_queue)
            self.listener = QueueListener(log_queue, file_handler)
            self.logger.addHandler(queue_handler)
            self.listener.start()

            atexit.register(self.shutdown)




        # if log_path:
        #     log_dir = os.path.dirname(log_path)
        #     if log_dir:
        #         os.makedirs(log_dir, exist_ok=True)

        #     file_handler = RotatingFileHandler(
        #         log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        #     )
        #     file_handler.setFormatter(CustomFileFormatter())
        #     self.logger.addHandler(file_handler)





        self._initialized = True

    def shutdown(self):
        """안전하게 QueueListener를 종료합니다."""
        if hasattr(self, 'listener') and self.listener is not None:
            try:
                # QueueListener의 스레드가 있는지 확인
                if hasattr(self.listener, '_thread') and self.listener._thread is not None:
                    self.listener.stop()
                    self.listener = None  # 중복 호출 방지
            except Exception as e:
                # 오류가 발생해도 무시하고 계속 진행
                pass

    def path(self) -> Optional[str]:
        if hasattr(self, 'listener') and self.listener.handlers:
            handler = self.listener.handlers[0]
            if isinstance(handler, RotatingFileHandler):
                return os.path.abspath(handler.baseFilename)
        return None

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs, stacklevel=2)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs, stacklevel=2)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs, stacklevel=2)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs, stacklevel=2)

    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs, stacklevel=2)
