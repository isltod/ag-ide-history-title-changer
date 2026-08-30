"""
안티그래비티 IDE 대화 제목 변경 도구 - 다국어(i18n) 지원 모듈
외부 의존성 없는 초경량 문자열 관리
"""
import os
import locale
from typing import Dict

# 지원하는 언어 코드
SUPPORTED_LANGS = ("ko", "en")

MESSAGES: Dict[str, Dict[str, str]] = {
    "ko": {
        "banner_title": "Antigravity IDE - 대화 히스토리 목록",
        "untitled_conv": "새 대화 (제목 없음)",
        "more_convs": "  ... 외 {count}개 이전 대화가 더 있습니다.",
        "no_convs_found": "\n❌ 저장된 Antigravity IDE 대화 기록을 찾을 수 없습니다.\n",
        "prompt_select_index": "👉 제목을 수정할 대화 번호를 입력하세요 (종료: 'q'): ",
        "exit_program": "\n프로그램을 종료합니다.",
        "err_invalid_index": "❌ 1부터 {max_num} 사이의 번호를 입력해주세요.\n",
        "selected_conv": "\n선택된 대화: {title}",
        "prompt_new_title": "👉 변경할 새 제목을 입력하세요: ",
        "err_empty_title": "❌ 제목이 비어 있습니다. 작업을 취소합니다.\n",
        "backup_path_info": "\n백업 저장 경로 (기본값: {default_path})",
        "prompt_backup_path": "👉 백업 경로 입력 (기본값 사용 시 엔터): ",
        "step_backup": "\n[1/3] 백업 진행 중... -> {path}",
        "backup_success": "  ✅ 백업 완료: {path}",
        "backup_failed": "  ❌ 백업 실패: {err}",
        "confirm_continue_without_backup": "  ⚠️ 백업 없이 계속 진행하시겠습니까? (y/N): ",
        "step_local_update": "[2/3] 로컬 데이터 갱신 중 (DB, 로그, 어노테이션)...",
        "local_update_success": "  ✅ 로컬 데이터 갱신 완료",
        "step_ls_sync": "[3/3] Language Server 실시간 동기화 시도 중...",
        "ls_sync_success": "  ✅ Language Server 실시간 동기화 완료! (IDE에 즉시 반영됨)",
        "ls_sync_offline": "  ℹ️ 로컬 데이터 갱신 완료 (IDE 재시작 또는 창 다시 로드 시 반영)",
        "rename_success": "\n🎉 '{old_title}' -> '{new_title}' 변경 완료!\n",
        "cli_rename_success": "🎉 대화 ID {conv_id} 의 제목이 '{title}'(으)로 변경되었습니다.",
        "cli_err_missing_args": "❌ --id 와 --title 옵션이 필요합니다.",
        "cli_err_invalid_index": "❌ 유효하지 않은 번호입니다: {target_id}",
        "warn_db_update_error": "[경고] SQLite DB 갱신 오류: {err}",
        "warn_log_update_error": "[경고] 로그 갱신 오류: {err}",
        "cli_desc": "Antigravity IDE Conversation Title Changer",
        "arg_action": "실행 모드 (list: 목록 조회, rename: 즉시 변경, interactive: 대화형 메뉴)",
        "arg_id": "대상 대화 ID 또는 목록 번호",
        "arg_title": "새로 설정할 제목",
        "arg_backup_dir": "백업 저장 루트 경로",
        "arg_lang": "표시 언어 (ko, en, auto)",
    },
    "en": {
        "banner_title": "Antigravity IDE - Conversation History List",
        "untitled_conv": "New Conversation (Untitled)",
        "more_convs": "  ... and {count} more older conversations.",
        "no_convs_found": "\n❌ No saved Antigravity IDE conversation history found.\n",
        "prompt_select_index": "👉 Enter conversation number to rename (quit: 'q'): ",
        "exit_program": "\nExiting program.",
        "err_invalid_index": "❌ Please enter a number between 1 and {max_num}.\n",
        "selected_conv": "\nSelected conversation: {title}",
        "prompt_new_title": "👉 Enter new title: ",
        "err_empty_title": "❌ Title cannot be empty. Operation cancelled.\n",
        "backup_path_info": "\nBackup destination (Default: {default_path})",
        "prompt_backup_path": "👉 Enter backup path (Press Enter for default): ",
        "step_backup": "\n[1/3] Creating backup... -> {path}",
        "backup_success": "  ✅ Backup completed: {path}",
        "backup_failed": "  ❌ Backup failed: {err}",
        "confirm_continue_without_backup": "  ⚠️ Continue without backup? (y/N): ",
        "step_local_update": "[2/3] Updating local data (DB, logs, annotations)...",
        "local_update_success": "  ✅ Local data updated successfully",
        "step_ls_sync": "[3/3] Syncing with Language Server in real-time...",
        "ls_sync_success": "  ✅ Language Server synced! (Reflected in IDE immediately)",
        "ls_sync_offline": "  ℹ️ Local data updated (Reflected on next IDE reload/restart)",
        "rename_success": "\n🎉 Successfully renamed '{old_title}' -> '{new_title}'!\n",
        "cli_rename_success": "🎉 Successfully renamed conversation ID {conv_id} to '{title}'.",
        "cli_err_missing_args": "❌ Both --id and --title options are required.",
        "cli_err_invalid_index": "❌ Invalid conversation index or ID: {target_id}",
        "warn_db_update_error": "[Warning] SQLite DB update error: {err}",
        "warn_log_update_error": "[Warning] Log update error: {err}",
        "cli_desc": "Antigravity IDE Conversation Title Changer",
        "arg_action": "Action mode (list: view list, rename: rename directly, interactive: interactive menu)",
        "arg_id": "Target conversation ID or list index",
        "arg_title": "New title to set",
        "arg_backup_dir": "Backup destination root path",
        "arg_lang": "Display language (ko, en, auto)",
    }
}

# 현재 활성화된 언어 (기본값: 'ko')
_current_lang = "ko"


def detect_system_language() -> str:
    """시스템 로케일을 감지하여 'ko' 또는 'en'을 반환합니다."""
    try:
        # 1. 환경 변수 확인
        env_lang = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
        if "ko" in env_lang.lower():
            return "ko"
        
        # 2. 로케일 모듈 확인
        sys_loc = locale.getdefaultlocale()[0] or locale.getlocale()[0] or ""
        if "ko" in sys_loc.lower() or "korean" in sys_loc.lower():
            return "ko"
    except Exception:
        pass
    return "en"


def set_lang(lang: str):
    """표시 언어를 설정합니다. ('auto', 'ko', 'en')"""
    global _current_lang
    if not lang or lang == "auto":
        _current_lang = detect_system_language()
    elif lang.lower() in SUPPORTED_LANGS:
        _current_lang = lang.lower()
    else:
        _current_lang = "en"


def get_lang() -> str:
    """현재 설정된 언어 코드를 반환합니다."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """
    현재 언어에 맞는 번역 문자열을 반환하고 포맷팅 파라미터를 적용합니다.
    해당 언어에 키가 없으면 영어, 그 다음 키 자체를 반환합니다.
    """
    lang_dict = MESSAGES.get(_current_lang, MESSAGES["en"])
    template = lang_dict.get(key)
    
    if template is None:
        template = MESSAGES["en"].get(key, key)
        
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
