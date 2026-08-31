import logging
from logging.handlers import RotatingFileHandler
import sys
import os

def setup_logging(
    logger_name: str = "MS_AI_SERVER",
    log_file: str = "MS_AI_SERVER.log",
    level: int = logging.INFO,
    max_bytes: int = 10**6,  # 1MB
    backup_count: int = 2  # 백업 파일 2개 (총 3개 파일 유지)
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.

    :param logger_name: 로거의 이름
    :param log_file: 로그 파일 경로
    :param level: 로그 레벨
    :param max_bytes: 로그 파일의 최대 크기 (바이트 단위)
    :param backup_count: 보관할 백업 파일의 개수 (총 파일 수 = backup_count + 1)
    :return: 설정된 로거 객체
    """
    # log 폴더가 없으면 생성
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # log 폴더 내에 로그 파일 경로 설정
    log_file_path = os.path.join(log_dir, log_file)
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # 루트 로거로의 전파 방지

    if not logger.handlers:
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 파일 핸들러 설정 (회전 로그)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
