"""
안티그래비티 IDE 대화 히스토리 제목 변경기 - 메인 실행 CLI
"""
import sys
import os
import shutil
import unicodedata
import argparse
from config import DEFAULT_BACKUP_ROOT
from backup_manager import create_backup
from local_storage import get_conversation_list, update_local_title
from ls_client import notify_language_server_rename

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
    print("  Antigravity IDE - 대화 히스토리 목록")
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
        print(f"  ... 외 {len(convs) - limit}개 이전 대화가 더 있습니다.")
    print()


def interactive_mode():
    convs = get_conversation_list()
    
    if not convs:
        print("\n❌ 저장된 Antigravity IDE 대화 기록을 찾을 수 없습니다.\n")
        return

    while True:
        display_list(convs)
        choice = input("👉 제목을 수정할 대화 번호를 입력하세요 (종료: 'q'): ").strip()
        
        if choice.lower() in ('q', 'quit', 'exit'):
            print("\n프로그램을 종료합니다.")
            break
            
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(convs):
            print(f"❌ 1부터 {len(convs)} 사이의 번호를 입력해주세요.\n")
            continue
            
        selected_conv = convs[int(choice) - 1]
        conv_id = selected_conv["id"]
        
        print(f"\n선택된 대화: {selected_conv['title']}")
        new_title = input("👉 변경할 새 제목을 입력하세요: ").strip()
        if not new_title:
            print("❌ 제목이 비어 있습니다. 작업을 취소합니다.\n")
            continue
            
        # 백업 경로 입력 받기
        print(f"\n백업 저장 경로 (기본값: {DEFAULT_BACKUP_ROOT})")
        custom_backup = input("👉 백업 경로 입력 (기본값 사용 시 엔터): ").strip()
        backup_path = custom_backup if custom_backup else DEFAULT_BACKUP_ROOT
        
        # 1. 백업 실행
        print(f"\n[1/3] 백업 진행 중... -> {backup_path}")
        try:
            saved_dir = create_backup(conv_id, backup_path)
            print(f"  ✅ 백업 완료: {saved_dir}")
        except Exception as e:
            print(f"  ❌ 백업 실패: {e}")
            confirm = input("  ⚠️ 백업 없이 계속 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                continue
                
        # 2. 로컬 스토리지 갱신
        print("[2/3] 로컬 데이터 갱신 중 (DB, 로그, 어노테이션)...")
        update_local_title(conv_id, new_title)
        print("  ✅ 로컬 데이터 갱신 완료")
        
        # 3. Language Server 실시간 동기화
        print("[3/3] Language Server 실시간 동기화 시도 중...")
        synced = notify_language_server_rename(conv_id, new_title)
        if synced:
            print("  ✅ Language Server 실시간 동기화 완료! (IDE에 즉시 반영됨)")
        else:
            print("  ℹ️ 로컬 데이터 갱신 완료 (IDE 재시작 또는 창 다시 로드 시 반영)")
            
        print(f"\n🎉 '{selected_conv['title']}' -> '{new_title}' 변경 완료!\n")
        
        # 목록 갱신
        convs = get_conversation_list()


def main():
    parser = argparse.ArgumentParser(description="Antigravity IDE Conversation Title Changer")
    parser.add_argument("action", nargs="?", default="interactive", choices=["list", "rename", "interactive"])
    parser.add_argument("--id", help="대상 대화 ID 또는 목록 번호")
    parser.add_argument("--title", help="새로 설정할 제목")
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_ROOT, help="백업 저장 루트 경로")
    
    args = parser.parse_args()
    
    if args.action == "list":
        convs = get_conversation_list()
        display_list(convs, limit=len(convs))
    elif args.action == "rename":
        if not args.id or not args.title:
            print("❌ --id 와 --title 옵션이 필요합니다.")
            sys.exit(1)
        convs = get_conversation_list()
        target_id = args.id
        if target_id.isdigit():
            idx = int(target_id)
            if 1 <= idx <= len(convs):
                target_id = convs[idx - 1]["id"]
            else:
                print(f"❌ 유효하지 않은 번호입니다: {target_id}")
                sys.exit(1)
                
        backup_dir = create_backup(target_id, args.backup_dir)
        print(f"✅ 백업 완료: {backup_dir}")
        update_local_title(target_id, args.title)
        print("✅ 로컬 데이터 갱신 완료")
        notify_language_server_rename(target_id, args.title)
        print(f"🎉 대화 ID {target_id} 의 제목이 '{args.title}'(으)로 변경되었습니다.")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
