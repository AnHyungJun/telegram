#!/bin/bash

PATH+=:/usr/bin
cur_dir=$(cd $(dirname $0) && pwd)
LOG_DIR=$cur_dir/log
#source ~/miniconda3/etc/profile.d/conda.sh
#conda activate py310
#SMS_PATH="/home/mining/sms_dir"
cd $cur_dir
user_key=$2

if [ "$1" == "start" ]; then
    while true
    do
        python3 src/event_handler_multi.py $user_key
        #error_log
        #remove_log "$cur_dir/log/telegram.log.$user_key.*" 30
        #python common/db_client_telegram.py 
        sleep 600
    done
elif [ "$1" == "stop" ]; then
    # stop 인자일 경우 프로그램 종료
    shell_pid=`ps -ef | grep "run_telegram_crawler.sh start $user_key"| grep -v color | awk '{print $2}'`
    echo $shell_pid
    kill -9 $shell_pid
    event_pid=`ps -ef | grep "event_handler_multi.py $user_key" | grep -v color | awk '{print $2}'`
    echo $event_pid
    kill -9 $event_pid
else
    echo "start 또는 stop 인자를 입력하세요."
fi
