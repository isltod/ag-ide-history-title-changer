# Antigravity IDE Conversation History Title Changer

[한국어](#한국어-korean) | [English](#english)

---

<a name="한국어-korean"></a>
## 🇰🇷 한국어 (Korean)

안티그래비티 IDE(Antigravity IDE)의 대화 히스토리 목록을 조회하고, 대화 제목을 직관적으로 수정 및 안전하게 백업할 수 있는 독립 실행형 CLI 도구입니다.

### 📌 주요 기능
1. **대화 목록 조회**: 최근 대화 제목과 마지막 활동 상대 시간(`1 hr ago`, `1 day ago` 등)을 콘솔 너비에 맞춰 정렬 출력
2. **다국어 지원 (i18n)**: 외부 의존성 없는 초경량 아키텍처로 한국어 및 영어 지원 (OS 로케일 자동 감지 또는 `--lang` 옵션)
3. **안전한 자동 백업**: 대화 제목 수정 전, 대상 대화의 DB 파일, 세션 로그, 어노테이션 데이터를 `<대화ID>_<YYYYMMDD_HHMMSS>` 전용 폴더에 자동 백업 (기본값: 프로그램 실행 폴더 내 `backups/`)
4. **실시간 동기화 (Language Server 연동)**:
   - 로컬 어노테이션 파일 (`~/.gemini/antigravity-ide/annotations/<대화ID>.pbtxt`) 생성
   - 로컬 SQLite 세션 DB (`conversations/<대화ID>.db`) 프로토버프 바이트 정합성 갱신
   - 트랜스크립트 세션 로그 (`transcript.jsonl`) 갱신
   - 실행 중인 Language Server 프로세스를 자동 감지하고 보안 CSRF 토큰을 포함한 HTTPS API를 호출하여 **IDE 화면(`Search all convos...`)에 실시간 반영**

---

### 🧪 검증된 테스트 환경
* **대상 애플리케이션**: **Antigravity IDE `v2.5.5`** (VSCode OSS `1.107.0` 기반)
* **운영체제 (OS)**: Windows 10 (Build 19045, 64-bit) / Windows 11 호환
* **파이썬 버전**: Python `3.10.11` (Python 3.10 이상 호환)
* **셸 환경**: PowerShell 5.1+, PowerShell 7+, Windows Terminal

---

### 🚀 설치 및 환경 설정

```powershell
# 1. 프로젝트 폴더로 이동
cd <프로젝트_디렉터리_경로>

# 2. 가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 의존성 패키지 설치
pip install -r requirements.txt
```

---

### 💻 사용 방법

#### 1. 대화형 인터랙티브 모드 (권장 ⭐)
대화 목록을 확인하고 번호를 선택하여 새 제목과 백업 경로를 입력할 수 있습니다.

```powershell
python main.py

# 영문 인터페이스로 실행
python main.py --lang en
```

* **수정할 번호 선택**: 목록에서 변경하고자 하는 대화 번호 입력 (예: `1`)
* **새 제목 입력**: `<새로운_대화_제목>` 입력
* **백업 경로 지정**: 기본 경로(`./backups/`) 사용 시 엔터 키, 또는 `<사용자_지정_백업_경로>` 입력

#### 2. 단일 명령어 모드 (CLI)

```powershell
# 전체 대화 목록만 출력 (기본: 시스템 로케일 자동 감지)
python main.py list

# 영어로 목록 출력
python main.py list --lang en

# 특정 번호의 대화 제목 즉시 변경 (기본 백업 경로 사용)
python main.py rename --id <대화번호_또는_ID> --title "<새로운_대화_제목>"

# 특정 백업 경로를 지정하여 제목 변경
python main.py rename --id <대화번호_또는_ID> --title "<새로운_대화_제목>" --backup-dir "<사용자_지정_백업_경로>"
```

---

<a name="english"></a>
## 🇺🇸 English

A standalone CLI tool for Antigravity IDE to view conversation history, rename conversation titles, and safely create backups with real-time IDE synchronization.

### 📌 Key Features
1. **Clean Conversation Listing**: Displays recent conversations with titles and relative last active times (e.g., `1 hr ago`, `1 day ago`) aligned dynamically to your terminal width.
2. **Multilingual Support (i18n)**: Lightweight zero-dependency localization supporting Korean & English (auto-detects system locale or explicit `--lang` flag).
3. **Safe Automated Backups**: Automatically backs up database files, session transcripts, and annotations into a dedicated `<conversation_id>_<YYYYMMDD_HHMMSS>` folder before making changes (default: `./backups/`).
4. **Real-time Live Sync (Language Server RPC)**:
   - Generates local annotation overrides (`~/.gemini/antigravity-ide/annotations/<id>.pbtxt`)
   - Updates Protobuf wire-format payloads within SQLite DB (`conversations/<id>.db`)
   - Updates session transcript logs (`transcript.jsonl`)
   - Auto-detects running Language Server processes, extracts the security CSRF token, and calls the HTTPS Connect-RPC API to **update the IDE UI (`Search all convos...`) in real time**.

---

### 🧪 Tested Environment
* **Target Application**: **Antigravity IDE `v2.5.5`** (Based on VSCode OSS `1.107.0`)
* **Operating System (OS)**: Windows 10 (Build 19045, 64-bit) / Windows 11 Compatible
* **Python Version**: Python `3.10.11` (Compatible with Python 3.10+)
* **Shell Environment**: PowerShell 5.1+, PowerShell 7+, Windows Terminal

---

### 🚀 Installation & Setup

```bash
# 1. Navigate to the project directory
cd <your_project_directory_path>

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
```

---

### 💻 Usage

#### 1. Interactive Mode (Recommended ⭐)
Browse the conversation history list and select an index to rename and back up interactively.

```bash
python main.py

# Run in English interface explicitly
python main.py --lang en
```

* **Select Index**: Enter the number from the list (e.g., `1`)
* **Enter New Title**: Enter `<new_conversation_title>`
* **Backup Destination**: Press Enter to use the default (`./backups/`), or enter `<custom_backup_path>`

#### 2. Command Line Interface (CLI)

```bash
# List all conversations
python main.py list

# List in English
python main.py list --lang en

# Rename a conversation with default backup path
python main.py rename --id <index_or_id> --title "<new_conversation_title>"

# Rename with a custom backup directory
python main.py rename --id <index_or_id> --title "<new_conversation_title>" --backup-dir "<custom_backup_path>"
```

---

### 📂 File Structure

```text
├── config.py             # Configuration & path / default language settings
├── i18n.py               # Lightweight zero-dependency i18n module
├── backup_manager.py     # Automated backup logic (<id>_<timestamp>)
├── local_storage.py      # SQLite / Protobuf parser & transcript updater
├── ls_client.py          # Language Server HTTPS + CSRF client
├── main.py               # Main CLI & interactive UI entry point
├── requirements.txt      # Dependencies (requests, tabulate, psutil)
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```
