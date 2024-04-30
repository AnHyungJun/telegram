#!/bin/bash

export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cur_dir=$(cd $(dirname $0) && pwd)
LOG_DIR=$cur_dir/log
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py310
SMS_PATH="/home/mining/sms_dir"
cd $cur_dir

remove_log() {
    path=$1
    delete_cnt=$2
    for file in $(ls $path | sort -r | tail -n +$delete_cnt); do
        echo "rm $file"
        rm $file
    done
}

error_log() {
    python $SMS_PATH/telegram_call.py "ERROR" "[telegram program END]" "CHECK PLZ"
}

if [ "$1" == "start" ]; then
    while true
    do
        python src/event_handler.py
        error_log
        remove_log "$cur_dir/log/telegram.log.*" 30
        python common/db_client_telegram.py 
        sleep 600
    done
elif [ "$1" == "stop" ]; then
    # stop 인자일 경우 프로그램 종료
    shell_pid=`ps -ef | grep run_telegram_crawler.sh | grep -v color | awk '{print $2}'`
    echo $shell_pid
    #kill -9 $shell_pid
else
    echo "start 또는 stop 인자를 입력하세요."
fi
