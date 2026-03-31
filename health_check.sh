#!/bin/bash

# --- 설정 변수 ---
# 1. 모니터링할 로그 파일 경로를 설정하세요.
LOG_FILE=$1

# 2. 프로그램이 멈췄다고 간주할 최대 미 업데이트 시간 (초 단위)
# 300초 = 5분
MAX_INACTIVITY_TIME=3600

# 3. 로그 파일 업데이트 체크 주기 (초 단위)
# 60초 = 1분
CHECK_INTERVAL=600

# --- 함수 정의 ---

# 로그 파일 업데이트 상태 확인
check_log_update() {
    # 로그 파일이 존재하는지 확인
    if [ ! -f "$LOG_FILE" ]; then
        echo "🚨 ERROR: Log file not found at $LOG_FILE. Exiting."
        exit 1
    fi

    # 현재 시간을 Unix 타임스탬프로 저장
    CURRENT_TIME=$(date +%s)

    # 로그 파일의 최종 수정 시간을 Unix 타임스탬프로 저장
    # Linux에서는 'stat -c %Y'를, macOS/BSD에서는 'stat -f %m'을 사용할 수 있습니다.
    # 여기서는 호환성을 위해 `ls`를 사용하거나, 시스템에 맞는 `stat` 명령어를 사용해야 합니다.
    # 범용적인 `ls`를 사용합니다. (최종 수정 시간을 초 단위로 정확히 가져오기 어려울 수 있습니다.)
    # 더 정확한 방법:
    # (리눅스) FILE_MOD_TIME=$(stat -c %Y "$LOG_FILE")
    # (맥/BSD) FILE_MOD_TIME=$(stat -f %m "$LOG_FILE")
    
    # 여기서는 리눅스 환경을 가정하고 stat 사용.
    FILE_MOD_TIME=$(stat -c %Y "$LOG_FILE")


    # 미 업데이트 시간 계산 (현재 시간 - 파일 수정 시간)
    INACTIVITY_TIME=$((CURRENT_TIME - FILE_MOD_TIME))

    # 미 업데이트 시간이 설정된 최대 시간을 초과했는지 확인
    if [ "$INACTIVITY_TIME" -gt "$MAX_INACTIVITY_TIME" ]; then
        python log_check.py timecheck
    else
        echo "Status: Running smoothly (Log is updating)."
    fi

    echo "-------------------------------------"
}

# --- 메인 루프 ---

echo "Starting log update monitor for $LOG_FILE..."
echo "Checking every $((CHECK_INTERVAL)) seconds. Max inactivity before alert: $((MAX_INACTIVITY_TIME / 60)) minutes."

# 무한 루프
while true; do
    check_log_update
    sleep "$CHECK_INTERVAL"
done