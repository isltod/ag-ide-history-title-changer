"""
Antigravity Language Server 실시간 Connect-RPC 클라이언트
HTTPS 통신 및 x-codeium-csrf-token 인증 헤더를 지원합니다.
"""
import subprocess
import json
import re
import requests
import psutil
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_all_active_language_servers():
    """
    현재 실행 중인 모든 Language Server 프로세스의 (PID, Port, CSRF Token, AppDataDir) 정보를 추출합니다.
    """
    servers = []
    
    # 1. WMI를 통해 전체 커맨드라인 및 CSRF 토큰 추출
    ps_cmd = 'Get-CimInstance Win32_Process -Filter "name like \'%language_server%\'" | Select-Object ProcessId, CommandLine | ConvertTo-Json'
    try:
        p = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
        if p.stdout.strip():
            data = json.loads(p.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                pid = item["ProcessId"]
                cmd = item["CommandLine"] or ""
                m = re.search(r'--csrf_token\s+([0-9a-f\-]+)', cmd)
                csrf = m.group(1) if m else None
                
                # 리스닝 포트 확인
                try:
                    proc = psutil.Process(pid)
                    for conn in proc.net_connections(kind='inet'):
                        if conn.status == psutil.CONN_LISTEN and conn.laddr.ip in ('127.0.0.1', '0.0.0.0'):
                            servers.append({
                                "pid": pid,
                                "port": conn.laddr.port,
                                "csrf": csrf,
                                "cmd": cmd
                            })
                except Exception:
                    pass
    except Exception:
        pass
        
    return servers


def notify_language_server_rename(conv_id: str, new_title: str) -> bool:
    """
    실행 중인 모든 Antigravity Language Server에 UpdateConversationAnnotations API를 전송하여
    클라우드 및 IDE 세션 캐시를 실시간으로 갱신합니다.
    """
    servers = get_all_active_language_servers()
    if not servers:
        return False
        
    success = False
    payload = {
        "cascadeId": conv_id,
        "annotations": {
            "title": new_title
        },
        "mergeAnnotations": True
    }
    
    for s in servers:
        port = s["port"]
        csrf = s["csrf"]
        
        headers = {
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1"
        }
        if csrf:
            headers["x-codeium-csrf-token"] = csrf
            
        for proto in ["https", "http"]:
            url = f"{proto}://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/UpdateConversationAnnotations"
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=2.0, verify=False)
                if r.status_code == 200:
                    success = True
                    break
            except Exception:
                pass
                
    return success
