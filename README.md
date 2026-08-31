# 🏠 Hermes Workspace

나(Hermes Agent)만의 전용 워크스페이스이자 **지휘 센터(command center)** 입니다.

## 📁 구조

```
C:\hermes\
├── dashboard\    # 개인 대시보드 (index.html + data.js/projects.js live data)
├── tools\        # 유틸리티 도구 (툴킷, 시스템 진단, 프로젝트 트래커, 자동 보고서)
├── scripts\      # hermes CLI 바로가기
├── notes\        # 메모 + 자동 보고서 (reports/)
├── projects\     # 프로젝트 코드 + 트래커 데이터 (projects.json)
└── logs\         # 로그
```

## ⚡ hermes CLI

터미널에서 어디서든 사용 가능:

```bash
hermes                 # 배너 + 실시간 시스템 통계
hermes status          # 워크스페이스 상태
hermes tree            # 디렉토리 트리
hermes info            # 시스템 정보
hermes diag            # 전체 시스템 건강 보고서
hermes watch           # 실시간 시스템 모니터 (5초 갱신)
hermes report          # 오늘의 자동 보고서
hermes refresh         # 대시보드 라이브 데이터 갱신
hermes projects        # 프로젝트 목록
hermes backup          # zip 백업
hermes widget          # SNS 상태 위젯 열기
hermes dash            # 대시보드 열기
hermes help            # 도움말
```

## 🖥️ 대시보드

`C:\hermes\dashboard\index.html` 을 브라우저/미리보기로 열면:

- ⏰ 실시간 KST 시계 + 업타임 카운터
- 🧠 **라이브 시스템 모니터** — CPU/메모리/디스크 사용률 + 상위 메모리 프로세스
- 📁 **프로젝트 보드** — 프로젝트 상태를 카드로 표시
- 📝 퀵 메모 (localStorage 저장)
- 📋 오늘의 할 일 체크리스트 (localStorage 저장)
- 💻 가상 터미널 (`ls`, `pwd`, `date`, `whoami` 등)
- 🎵 기분 선택 기능

**데이터 갱신:** 대시보드는 `dashboard/data.js` 를 읽습니다. 갱신하려면:

```bash
python tools/hermes_toolkit.py refresh
```

## 🛠️ 툴킷

```bash
python tools/hermes_toolkit.py status       # 워크스페이스 상태
python tools/hermes_toolkit.py tree        # 디렉토리 트리
python tools/hermes_toolkit.py info        # 시스템 정보
python tools/hermes_toolkit.py backup      # zip 백업 생성
python tools/hermes_toolkit.py cleanup     # 임시파일 정리
python tools/hermes_toolkit.py count-lines # 코드 라인 수
python tools/hermes_toolkit.py refresh     # 대시보드 라이브 데이터 갱신
python tools/hermes_toolkit.py maintenance # 주간 정리 + 백업 (한 번에)
```

## 🩺 시스템 진단

```bash
python tools/system_diagnostics.py                  # 전체 보고서
python tools/system_diagnostics.py --json           # JSON 출력
python tools/system_diagnostics.py --watch 5        # 5초마다 갱신 (모니터)
python tools/system_diagnostics.py --out dashboard/data.json  # JSON 파일로 저장
```

## 📁 프로젝트 트래커

```bash
python tools/project_tracker.py list                # 프로젝트 목록
python tools/project_tracker.py stats               # 상태별 통계
python tools/project_tracker.py add --name X --status active --desc "..." --path "C:/..."
python tools/project_tracker.py status <name> <status>   # 상태 변경
python tools/project_tracker.py del <name>          # 삭제
```

상태: `active`, `planned`, `paused`, `done`, `archived`

## 📔 일기/메모 (diary)

```bash
python tools/diary.py write            # 오늘 일기 작성 (대화형)
python tools/diary.py write --text "..."   # 빠른 일기
python tools/diary.py read [date]      # 특정 날짜 읽기 (기본 오늘)
python tools/diary.py list             # 목록
python tools/diary.py search <키워드>  # 검색
python tools/diary.py stats            # 통계
```

## 🌐 네트워크 유틸리티 (net_utils)

```bash
python tools/net_utils.py info          # 네트워크 기본 정보
python tools/net_utils.py myip          # 공인 IP 조회
python tools/net_utils.py dns naver.com # DNS 조회
python tools/net_utils.py ping 8.8.8.8  # 핑 테스트
python tools/net_utils.py ports         # 열린 포트 스캔 (--limit N)
python tools/net_utils.py check         # 주요 사이트 연결 확인
```

## 📝 Markdown → HTML 변환기 (md2html)

```bash
python tools/md2html.py post.md --theme dark    # 기본 (다크)
python tools/md2html.py post.md --theme light   # 라이트
python tools/md2html.py post.md --theme sepia   # 세피아
python tools/md2html.py post.md --stdout        # HTML만 출력
python tools/md2html.py post.md --title "제목"  # 헤딩 자동 추출
```

블로그 글/노트를 스타일드 HTML로 변환합니다. 테이블/코드블록/인용구 등 지원.

일기는 `notes/diary/YYYY-MM-DD.md`에 저장됩니다.

## 🗂️ 파일 유틸리티 (file_utils)

```bash
# 이미지 (Pillow 필요)
python tools/file_utils.py img-resize <file> --width 800
python tools/file_utils.py img-convert <file> --to png
python tools/file_utils.py img-compress <file> --quality 70

# 일괄 이름 변경
python tools/file_utils.py rename <dir> --prefix img_ --num 1
python tools/file_utils.py rename <dir> --suffix _bak

# 분석
python tools/file_utils.py dup <dir>            # 중복 파일 탐지
python tools/file_utils.py size <dir>           # 폴더 크기
python tools/file_utils.py large <dir> --top 10 # 최대 파일

# 정리
python tools/file_utils.py clean <dir> --ext .tmp --dry-run
```

## 🎨 시각화 위젯 (SNS 공유용)

`projects/` 아래 각각 독립 HTML 위젯으로, 브라우저에서 바로 열어 공유할 수 있습니다.

| 위젯 | 경로 | 특징 |
|------|------|------|
| 📺 SNS 상태 위젯 | `projects/sns_showcase/status_widget.html` | 6테마, 게이지, PNG저장, X공유, QR |
| 📔 일기 히트맵 | `projects/diary_heatmap/index.html` | GitHub 잔디 스타일 일기 달력 |
| ⚡ 인터넷 속도계 | `projects/speedometer/index.html` | Cloudflare 실측 다운/업로드 속도 |
| 🗂️ 폴더 트리맵 | `projects/treemap/index.html` | 폴더 크기 트리맵 (slice-and-dice) |
| 🏅 상태 뱃지 | `projects/badge/index.html` | flat.svg + card.svg 상태 배지 |

```bash
# 데이터 갱신 후 위젯 열기
hermes treemap       # 트리맵 스캔 + 열기
hermes badge         # 상태 뱃지 재생성
python tools/treemap.py C:/hermes   # 트리맵 데이터 스캔
python tools/diary.py export        # 일기 히트맵 JSON
```

## 🖥️ hermes CLI 단축

```bash
hermes freedom      # 워크스페이스 전체 도구 요약
hermes diary        # 일기 목록
hermes fsize        # 워크스페이스 폴더 크기
```

## 🤖 자동화 (cron)

등록된 Hermes cron 작업들:

| 작업 | 일정 | 내용 |
|------|------|------|
| **Hermes Daily Auto-Report** | 매일 09:00 | 시스템 상태 + 프로젝트 보고서를 `notes/reports/`에 생성 |
| **Hermes Weekly Maintenance** | 매주 금요일 19:00 | 임시파일 정리 + zip 백업 |

> ⚠️ cron 작업은 **Hermes 게이트웨이가 실행 중일 때**만 발화합니다.
> 시작하려면: `hermes gateway start`

## 📁 projects/

| 프로젝트 | 상태 | 설명 |
|----------|------|------|
| `sns_showcase/status_widget.html` | 🚀 active | 실시간 시스템 상태 위젯 — PNG로 저장해 SNS 공유 가능 |
| `dashboard/` | 🚀 active | 개인 지휘 센터 대시보드 |

프로젝트는 `python tools/project_tracker.py`로 관리합니다.
