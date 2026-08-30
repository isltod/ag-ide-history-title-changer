"""
안티그래비티 IDE 대화 히스토리 제목 변경기 - 메인 실행 CLI
다국어(i18n) 지원 및 실시간 동기화 지원
"""
import sys
import os
import shutil
import unicodedata
import argparse
from config import DEFAULT_BACKUP_ROOT, DEFAULT_LANG
from backup_manager import create_backup
from local_storage import get_conversation_list, update_local_title
from ls_client import notify_language_server_rename
from i18n import t, set_lang

# 콘솔 UTF-8 출력 보장
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def get_display_width(text: str) -> int:
    """한글 2칸, 영문/기호 1칸 기준 실제 콘솔 출력 너비를 계산합니다."""
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)


def truncate_to_display_width(text: str, max_width: int) -> str:
    """지정된 디스플레이 너비에 맞게 문자열을 자르고 필요시 '...'을 붙입니다."""
    if get_display_width(text) <= max_width:
        return text
    
    cur_w = 0
    res = []
    for c in text:
        w = 2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1
        if cur_w + w > max_width - 3:
            return "".join(res) + "..."
        cur_w += w
        res.append(c)
    return "".join(res)


def pad_to_display_width(text: str, target_width: int) -> str:
    """디스플레이 너비 기준으로 공백을 채워 완벽하게 우측을 맞춥니다."""
    w = get_display_width(text)
    if w < target_width:
        return text + " " * (target_width - w)
    return text


def get_term_width() -> int:
    """현재 터미널 창의 너비(컬럼 수)를 가져옵니다. (최소 60, 기본 80)"""
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        return max(60, cols - 2)
    except Exception:
        return 80


def print_banner(width: int):
    print("\n" + "=" * width)
    print(f"  {t('banner_title')}")
    print("=" * width)


def display_list(convs, limit=15):
    term_width = get_term_width()
    print_banner(term_width)
    
    time_col_width = 13
    prefix_width = 6  # " [ 1] "
    available_title_width = max(20, term_width - prefix_width - time_col_width - 2)
    
    display_items = convs[:limit]
    for idx, c in enumerate(display_items, 1):
        prefix = f" [{idx:2d}] "
        truncated_title = truncate_to_display_width(c["title"], available_title_width)
        padded_title = pad_to_display_width(truncated_title, available_title_width)
        right_time = f"{c['relative_time']:>{time_col_width}}"
        print(f"{prefix}{padded_title}  {right_time}")
        
    print("=" * term_width)
    if len(convs) > limit:
        print(t("more_convs", count=len(convs) - limit))
    print()


def interactive_mode():
    convs = get_conversation_list()
    
    if not convs:
        print(t("no_convs_found"))
        return

    while True:
        display_list(convs)
        choice = input(t("prompt_select_index")).strip()
        
        if choice.lower() in ('q', 'quit', 'exit'):
            print(t("exit_program"))
            break
            
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(convs):
            print(t("err_invalid_index", max_num=len(convs)))
            continue
            
        selected_conv = convs[int(choice) - 1]
        conv_id = selected_conv["id"]
        
        print(t("selected_conv", title=selected_conv['title']))
        new_title = input(t("prompt_new_title")).strip()
        if not new_title:
            print(t("err_empty_title"))
            continue
            
        # 백업 경로 입력 받기
        print(t("backup_path_info", default_path=DEFAULT_BACKUP_ROOT))
        custom_backup = input(t("prompt_backup_path")).strip()
        backup_path = custom_backup if custom_backup else DEFAULT_BACKUP_ROOT
        
        # 1. 백업 실행
        print(t("step_backup", path=backup_path))
        try:
            saved_dir = create_backup(conv_id, backup_path)
            print(t("backup_success", path=saved_dir))
        except Exception as e:
            print(t("backup_failed", err=e))
            confirm = input(t("confirm_continue_without_backup")).strip().lower()
            if confirm != 'y':
                continue
                
        # 2. 로컬 스토리지 갱신
        print(t("step_local_update"))
        update_local_title(conv_id, new_title)
        print(t("local_update_success"))
        
        # 3. Language Server 실시간 동기화
        print(t("step_ls_sync"))
        synced = notify_language_server_rename(conv_id, new_title)
        if synced:
            print(t("ls_sync_success"))
        else:
            print(t("ls_sync_offline"))
            
        print(t("rename_success", old_title=selected_conv['title'], new_title=new_title))
        
        # 목록 갱신
        convs = get_conversation_list()


def main():
    parser = argparse.ArgumentParser(description="Antigravity IDE Conversation Title Changer")
    parser.add_argument("action", nargs="?", default="interactive", choices=["list", "rename", "interactive"],
                        help="Action to perform")
    parser.add_argument("--id", help="Target conversation ID or list index")
    parser.add_argument("--title", help="New title to set")
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_ROOT, help="Backup root path")
    parser.add_argument("--lang", default=DEFAULT_LANG, choices=["auto", "ko", "en"],
                        help="Interface language: 'auto' (system detect), 'ko', or 'en'")
    
    args = parser.parse_args()
    
    # 언어 설정 적용
    set_lang(args.lang)
    
    if args.action == "list":
        convs = get_conversation_list()
        display_list(convs, limit=len(convs))
    elif args.action == "rename":
        if not args.id or not args.title:
            print(t("cli_err_missing_args"))
            sys.exit(1)
        convs = get_conversation_list()
        target_id = args.id
        if target_id.isdigit():
            idx = int(target_id)
            if 1 <= idx <= len(convs):
                target_id = convs[idx - 1]["id"]
            else:
                print(t("cli_err_invalid_index", target_id=target_id))
                sys.exit(1)
                
        backup_dir = create_backup(target_id, args.backup_dir)
        print(t("backup_success", path=backup_dir))
        update_local_title(target_id, args.title)
        print(t("local_update_success"))
        notify_language_server_rename(target_id, args.title)
        print(t("cli_rename_success", conv_id=target_id, title=args.title))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
