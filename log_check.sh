#!/bin/bash

PATH+=:/usr/bin
cur_dir=$(cd $(dirname $0) && pwd)
LOG_DIR=$cur_dir/log
#source ~/miniconda3/etc/profile.d/conda.sh
#conda activate py310
#SMS_PATH="/home/mining/sms_dir"
cd $cur_dir
user_key=$1

remove_file()
{
    local file_ext=$1
    local delete_cnt=$2
    echo $delete_cnt
    # 파일 수 확인
    local file_count=($(ls -1 $file_ext 2>/dev/null | wc -l))
    echo $file_count
    echo $delete_cnt
    # 파일 수가 14개 이상이면 삭제
    if [ $file_count -gt $delete_cnt ]; then
        echo "ls -1tr $file_ext 2>/dev/null | head -n $(expr $file_count - $delete_cnt) | xargs rm -f"
        cd $file_ext
	ls -1tr $file_ext 2>/dev/null | head -n $(expr $file_count - $delete_cnt) | xargs rm -f
    fi
}

remove_dir() {
    # 폴더 경로
    local dir_path=$1

    # 폴더 리스트 생성 (가장 오래된 것부터)
    local dir_list=$(ls -t "$dir_path")

    # 폴더 개수
    local dir_count=$(echo "$dir_list" | wc -l)

    # 유지할 폴더 개수 (30개로 설정)
    local keep_count=$2

    # 폴더 개수가 유지할 폴더 개수보다 많으면 가장 오래된 폴더부터 삭제
    if [ $dir_count -gt $keep_count ]; then
        remove_count=$((dir_count - keep_count))
        remove_list=$(echo "$dir_list" | tail -$remove_count)

        for dir_name in $remove_list; do
            rm -rf "${dir_path}/${dir_name}"
        done
    fi

}


error_log()
{
    path=$1
    python3 $cur_dir/log_check.py $1
}


remove_dir "/locdisk/telegram_data/etc_file" 14
remove_file "$cur_dir/log/telegram.log.$user_key.*" 7
remove_file "$cur_dir/etc/channel_list.*.json" 7
remove_file "/locdisk/telegram_data/telegram_message.*.json" 14
#remove_file $cur_dir/out 14
#error_log $cur_dir/log/telegram.log
