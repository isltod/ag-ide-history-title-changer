"""
안티그래비티 IDE 대화 백업 관리 모듈
"""
import os
import shutil
from datetime import datetime
from config import BRAIN_DIR, CONVERSATIONS_DIR, ANNOTATIONS_DIR, DEFAULT_BACKUP_ROOT


def create_backup(conv_id: str, custom_backup_root: str = None) -> str:
    """
    사용자가 지정한 백업 루트 하위에 <대화ID>_<YYYYMMDD_HHMMSS> 전용 폴더를 생성하고
    해당 대화와 관련된 DB, 로그, 어노테이션 데이터를 모두 백업합니다.
    
    반환값: 생성된 백업 디렉터리 경로
    """
    backup_root = custom_backup_root.strip() if custom_backup_root and custom_backup_root.strip() else DEFAULT_BACKUP_ROOT
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_folder_name = f"{conv_id}_{timestamp}"
    target_dir = os.path.join(backup_root, target_folder_name)
    
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. DB 파일 백업 (conversations/<id>.*)
    conv_backup_dir = os.path.join(target_dir, "conversations")
    os.makedirs(conv_backup_dir, exist_ok=True)
    for ext in [".db", ".db-wal", ".db-shm"]:
        db_file = os.path.join(CONVERSATIONS_DIR, f"{conv_id}{ext}")
        if os.path.exists(db_file):
            shutil.copy2(db_file, os.path.join(conv_backup_dir, f"{conv_id}{ext}"))
            
    # 2. 어노테이션 백업 (annotations/<id>.pbtxt)
    ann_file = os.path.join(ANNOTATIONS_DIR, f"{conv_id}.pbtxt")
    if os.path.exists(ann_file):
        ann_backup_dir = os.path.join(target_dir, "annotations")
        os.makedirs(ann_backup_dir, exist_ok=True)
        shutil.copy2(ann_file, os.path.join(ann_backup_dir, f"{conv_id}.pbtxt"))
        
    # 3. Brain 폴더 백업 (brain/<id> 전체)
    src_brain_dir = os.path.join(BRAIN_DIR, conv_id)
    if os.path.exists(src_brain_dir):
        dst_brain_dir = os.path.join(target_dir, "brain", conv_id)
        shutil.copytree(src_brain_dir, dst_brain_dir, dirs_exist_ok=True)
        
    return target_dir
