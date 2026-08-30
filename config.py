"""
안티그래비티 IDE 대화 제목 변경 도구 - 환경 설정 모듈
"""
import os
import psutil

# 기본 디렉터리 경로 설정
HOME_DIR = os.path.expanduser("~")
GEMINI_IDE_DIR = os.path.join(HOME_DIR, ".gemini", "antigravity-ide")

BRAIN_DIR = os.path.join(GEMINI_IDE_DIR, "brain")
CONVERSATIONS_DIR = os.path.join(GEMINI_IDE_DIR, "conversations")
ANNOTATIONS_DIR = os.path.join(GEMINI_IDE_DIR, "annotations")

# 기본 백업 루트 디렉터리: 프로그램이 위치한 디렉터리 하위 'backups' 폴더
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BACKUP_ROOT = os.path.join(BASE_DIR, "backups")

# 기본 언어 설정: 'auto' (시스템 감지), 'ko', 'en'
DEFAULT_LANG = "auto"


def get_active_language_server_port() -> int:
    """
    현재 실행 중인 Antigravity Language Server의 로컬 통신 포트를 자동 탐지합니다.
    기본값은 8868입니다.
    """
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            name = (proc.info['name'] or "").lower()
            if "language_server" in name:
                connections = proc.net_connections(kind='inet')
                for conn in connections:
                    if conn.status == psutil.CONN_LISTEN and conn.laddr.ip in ('127.0.0.1', '0.0.0.0'):
                        return conn.laddr.port
        except Exception:
            pass
            
    return 8868
