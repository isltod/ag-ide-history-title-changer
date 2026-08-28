"""
로컬 세션 데이터 파싱 및 제목 변경 모듈
"""
import os
import sqlite3
import re
from datetime import datetime
from typing import List, Dict
from config import BRAIN_DIR, CONVERSATIONS_DIR, ANNOTATIONS_DIR

def encode_varint(v: int) -> bytes:
    res = []
    while v > 127:
        res.append((v & 0x7F) | 0x80)
        v >>= 7
    res.append(v & 0x7F)
    return bytes(res)

def decode_varint(buf: bytes, pos: int):
    v = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        v |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return v, pos

def format_relative_time(timestamp: float) -> str:
    now = datetime.now().timestamp()
    diff = max(0, int(now - timestamp))
    if diff < 60:
        return "just now"
    elif diff < 3600:
        mins = diff // 60
        return f"{mins} min ago" if mins == 1 else f"{mins} mins ago"
    elif diff < 86400:
        hrs = diff // 3600
        return f"{hrs} hr ago" if hrs == 1 else f"{hrs} hrs ago"
    elif diff < 86400 * 30:
        days = diff // 86400
        return f"{days} day ago" if days == 1 else f"{days} days ago"
    elif diff < 86400 * 365:
        months = diff // (86400 * 30)
        return f"{months} mo ago" if months == 1 else f"{months} mos ago"
    else:
        years = diff // (86400 * 365)
        return f"{years} yr ago" if years == 1 else f"{years} yrs ago"

def get_conversation_list() -> List[Dict]:
    if not os.path.exists(CONVERSATIONS_DIR):
        return []
    dbs = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith(".db")]
    results = []
    for db_name in dbs:
        conv_id = db_name[:-3]
        db_path = os.path.join(CONVERSATIONS_DIR, db_name)
        mtime = os.path.getmtime(db_path)
        rel_time = format_relative_time(mtime)
        title = ""
        # 1. 어노테이션 파일 확인 (우선순위 1)
        ann_path = os.path.join(ANNOTATIONS_DIR, f"{conv_id}.pbtxt")
        if os.path.exists(ann_path):
            try:
                with open(ann_path, "r", encoding="utf-8") as af:
                    content = af.read()
                    m = re.search(r'title:\s*"([^"]+)"', content)
                    if m:
                        title = m.group(1).strip()
            except Exception:
                pass
        # 2. SQLite DB에서 체크포인트(step_type=23) 제목 추출
        if not title:
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT step_payload FROM steps WHERE step_type=23 ORDER BY idx ASC")
                for row in cur.fetchall():
                    payload = row[0]
                    if payload:
                        f30_pos = payload.find(b"\xf2\x01")
                        if f30_pos != -1:
                            f30_len, f30_start = decode_varint(payload, f30_pos + 2)
                            f30_data = payload[f30_start:f30_start+f30_len]
                            if f30_data.startswith(b"\x22"):
                                f4_len, f4_start = decode_varint(f30_data, 1)
                                raw_t = f30_data[f4_start:f4_start+f4_len].decode("utf-8", errors="ignore").strip()
                                if raw_t:
                                    title = raw_t.split("\n")[0].strip()
                                    break
                conn.close()
            except Exception:
                pass
        # 3. 트랜스크립트 로그에서 제목/질문 추출
        if not title:
            log_path = os.path.join(BRAIN_DIR, conv_id, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(log_path):
                try:
                    import json
                    with open(log_path, "r", encoding="utf-8") as lf:
                        for line in lf:
                            if "# USER Objective:" in line:
                                obj_m = re.search(r"# USER Objective:\s*\n([^\n]+)", line)
                                if obj_m:
                                    title = obj_m.group(1).strip().split("\n")[0].strip()
                                    break
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT" and data.get("content"):
                                cleaned = re.sub(r"<[^>]+>", "", data["content"]).strip()
                                title = (cleaned.replace("\r", "").replace("\n", " "))[:45]
                                break
                except Exception:
                    pass
        if not title:
            title = "새 대화 (제목 없음)"
        results.append({
            "id": conv_id,
            "mtime": mtime,
            "relative_time": rel_time,
            "title": title
        })
    results.sort(key=lambda x: x["mtime"], reverse=True)
    return results

def update_local_title(conv_id: str, new_title: str) -> bool:
    new_bytes = new_title.encode("utf-8")
    os.makedirs(ANNOTATIONS_DIR, exist_ok=True)
    ann_path = os.path.join(ANNOTATIONS_DIR, f"{conv_id}.pbtxt")
    with open(ann_path, "w", encoding="utf-8") as af:
        af.write(f'title:"{new_title}"\n')
    db_path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT rowid, step_payload FROM steps WHERE step_type=23")
            for row in cur.fetchall():
                rowid, payload = row[0], row[1]
                if payload:
                    f30_pos = payload.find(b"\xf2\x01")
                    if f30_pos != -1:
                        f30_len, f30_start = decode_varint(payload, f30_pos + 2)
                        f30_data = payload[f30_start:f30_start+f30_len]
                        if f30_data.startswith(b"\x22"):
                            f4_len, f4_start = decode_varint(f30_data, 1)
                            new_f4 = b"\x22" + encode_varint(len(new_bytes)) + new_bytes
                            rest_f30 = f30_data[f4_start + f4_len:]
                            new_f30_data = new_f4 + rest_f30
                            prefix = payload[:f30_pos + 2]
                            suffix = payload[f30_start + f30_len:]
                            new_payload = prefix + encode_varint(len(new_f30_data)) + new_f30_data + suffix
                            cur.execute("UPDATE steps SET step_payload=? WHERE rowid=?", (new_payload, rowid))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[경고] SQLite DB 갱신 오류: {e}")
    logs_dir = os.path.join(BRAIN_DIR, conv_id, ".system_generated", "logs")
    for log_name in ["transcript.jsonl", "transcript_full.jsonl"]:
        log_file = os.path.join(logs_dir, log_name)
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as lf:
                    l_content = lf.read()
                if "# USER Objective:" in l_content:
                    l_content = re.sub(r"(# USER Objective:\s*\n)([^\n]+)", rf"\g<1>{new_title}", l_content)
                with open(log_file, "w", encoding="utf-8") as lf:
                    lf.write(l_content)
            except Exception as e:
                print(f"[경고] 로그 갱신 오류: {e}")
    return True
