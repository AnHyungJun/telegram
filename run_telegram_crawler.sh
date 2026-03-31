#!/bin/bash

PATH+=:/usr/bin
cur_dir=$(cd $(dirname $0) && pwd)
LOG_DIR=$cur_dir/log
PID_DIR=$cur_dir/pid
cd $cur_dir
user_key=$2
rm nohup.out
SHELL_PID_FILE="$PID_DIR/shell.${user_key}.pid"
EVENT_PID_FILE="$PID_DIR/event.${user_key}.pid"

mkdir -p "$PID_DIR"

is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

do_start() {
    if is_running "$SHELL_PID_FILE"; then
        echo "[WARN] 이미 실행 중입니다. (shell pid: $(cat $SHELL_PID_FILE))"
        exit 1
    fi

    echo $$ > "$SHELL_PID_FILE"
    echo "[INFO] start (user_key=$user_key, shell_pid=$$)"

    while true
    do
        python3 src/event_handler_multi.py $user_key &
        event_pid=$!
        echo $event_pid > "$EVENT_PID_FILE"
        echo "[INFO] event_handler started (pid=$event_pid)"
        wait $event_pid
        echo "[WARN] event_handler 종료됨. 60초 후 재시작..."
        sleep 60
    done
}

do_stop() {
    local stopped=0

    if is_running "$EVENT_PID_FILE"; then
        local pid=$(cat "$EVENT_PID_FILE")
        echo "[INFO] event_handler 종료 (pid=$pid)"
        kill "$pid" 2>/dev/null
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
        stopped=1
    fi
    rm -f "$EVENT_PID_FILE"

    if is_running "$SHELL_PID_FILE"; then
        local pid=$(cat "$SHELL_PID_FILE")
        echo "[INFO] shell 종료 (pid=$pid)"
        kill "$pid" 2>/dev/null
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
        stopped=1
    fi
    rm -f "$SHELL_PID_FILE"

    if [ $stopped -eq 0 ]; then
        echo "[WARN] 실행 중인 프로세스가 없습니다."
    else
        echo "[INFO] 종료 완료"
    fi
}

do_status() {
    echo "=== user_key: $user_key ==="
    if is_running "$SHELL_PID_FILE"; then
        echo "  shell  : running (pid=$(cat $SHELL_PID_FILE))"
    else
        echo "  shell  : stopped"
    fi
    if is_running "$EVENT_PID_FILE"; then
        echo "  event  : running (pid=$(cat $EVENT_PID_FILE))"
    else
        echo "  event  : stopped"
    fi
}

if [ -z "$user_key" ]; then
    echo "사용법: $0 {start|stop|restart|status} <user_key>"
    exit 1
fi

case "$1" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart)
        do_stop
        sleep 2
        do_start
        ;;
    status)
        do_status
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status} <user_key>"
        exit 1
        ;;
esac
