#!/usr/bin/env python3
"""
텔레그램 채널별 메시지 수집 누락 체크 스크립트

사용법:
    python etc/check_missing_channels.py --start 20260320 --end 20260331
    python etc/check_missing_channels.py --start 20260331  # 단일 날짜
    python etc/check_missing_channels.py --start 20260325 --end 20260331 --channel-list etc/channel_list.20260331.json
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_DATA_DIR = "/locdisk/telegram_data"


def date_range(start_str: str, end_str: str) -> list:
    start = datetime.strptime(start_str, "%Y%m%d")
    end = datetime.strptime(end_str, "%Y%m%d")
    dates = []
    cur = start
    while cur <= end:
        dates.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return dates


def load_channel_list(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.loads(f.read().strip())
    channels = {}
    for k, v in data.items():
        channels[int(k)] = v.get("channel_name", k)
    return channels


def scan_messages(data_dir: str, dates: list) -> dict:
    """날짜별 파일에서 채널별 수집 메시지 수와 message_id 범위를 집계"""
    # {channel_id: {date: [message_ids]}}
    result = defaultdict(lambda: defaultdict(list))

    for d in dates:
        file_path = os.path.join(data_dir, f"telegram_message.{d}.json")
        if not os.path.exists(file_path):
            print(f"[WARN] 파일 없음: {file_path}")
            continue
        with open(file_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    ch_id = msg.get("channel_id")
                    msg_id = msg.get("message_id")
                    if ch_id is not None:
                        result[int(ch_id)][d].append(msg_id)
                except json.JSONDecodeError:
                    print(f"[WARN] JSON 파싱 실패: {file_path} line {line_no}")
    return result


def main():
    parser = argparse.ArgumentParser(description="텔레그램 채널 수집 누락 체크")
    parser.add_argument("--start", required=True, help="시작 날짜 (yyyymmdd)")
    parser.add_argument("--end", default=None, help="종료 날짜 (yyyymmdd), 미지정 시 start와 동일")
    parser.add_argument("--channel-list", default=None, help="채널 리스트 JSON 경로")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="데이터 디렉토리 경로")
    args = parser.parse_args()

    end_date = args.end or args.start
    dates = date_range(args.start, end_date)

    # 채널 리스트 파일 자동 탐색
    if args.channel_list:
        channel_list_path = args.channel_list
    else:
        # etc/ 디렉토리에서 가장 최신 channel_list 파일 사용
        etc_dir = os.path.join(ROOT_DIR, "etc")
        candidates = sorted(
            [f for f in os.listdir(etc_dir) if f.startswith("channel_list.") and f.endswith(".json")],
            reverse=True
        )
        if not candidates:
            print("[ERROR] etc/ 디렉토리에 channel_list.*.json 파일이 없습니다.")
            sys.exit(1)
        channel_list_path = os.path.join(etc_dir, candidates[0])

    print(f"채널 리스트: {channel_list_path}")
    print(f"조회 기간 : {args.start} ~ {end_date} ({len(dates)}일)")
    print(f"데이터 경로: {args.data_dir}")
    print("=" * 80)

    channels = load_channel_list(channel_list_path)
    collected = scan_messages(args.data_dir, dates)

    # 채널별 수집 현황 분석
    missing_channels = []  # 전체 기간 수집 0건
    partial_channels = []  # 일부 날짜 누락

    for ch_id, ch_name in sorted(channels.items(), key=lambda x: x[1]):
        ch_data = collected.get(ch_id, {})
        collected_dates = set(ch_data.keys())
        missing_dates = [d for d in dates if d not in collected_dates]
        total_msgs = sum(len(ids) for ids in ch_data.values())

        if total_msgs == 0:
            missing_channels.append((ch_id, ch_name))
        elif missing_dates:
            daily_detail = {d: len(ch_data.get(d, [])) for d in dates}
            partial_channels.append((ch_id, ch_name, missing_dates, daily_detail, total_msgs))

    # 결과 출력
    print(f"\n[전체 수집 누락 채널] ({len(missing_channels)}/{len(channels)}개)")
    print("-" * 80)
    if missing_channels:
        for ch_id, ch_name in missing_channels:
            print(f"  {ch_id:>15}  {ch_name}")
    else:
        print("  없음")

    print(f"\n[일부 날짜 누락 채널] ({len(partial_channels)}개)")
    print("-" * 80)
    if partial_channels:
        for ch_id, ch_name, miss_dates, daily, total in partial_channels:
            print(f"  {ch_id:>15}  {ch_name}")
            print(f"                   총 {total}건 수집 / 누락일: {', '.join(miss_dates)}")
            daily_str = " | ".join(f"{d}:{daily[d]}건" for d in dates)
            print(f"                   일별: {daily_str}")
            print()
    else:
        print("  없음")

    # 요약
    collected_channels = [ch_id for ch_id in channels if ch_id in collected and sum(len(v) for v in collected[ch_id].values()) > 0]
    print("=" * 80)
    print(f"[요약]")
    print(f"  모니터링 채널 수  : {len(channels)}")
    print(f"  수집 정상 채널    : {len(collected_channels) - len(partial_channels)}")
    print(f"  일부 누락 채널    : {len(partial_channels)}")
    print(f"  전체 누락 채널    : {len(missing_channels)}")


if __name__ == "__main__":
    main()
