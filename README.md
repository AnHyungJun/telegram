# 목차

- [목차](#목차)
- [수집 방법 목록](#수집-방법-목록)
- [방법 별 검토 사항](#방법-별-검토-사항)
- [수집 필수 데이터](#수집-필수-데이터)
  - [(참고) 텔레그램 메시지 데이터 구조](#참고-텔레그램-메시지-데이터-구조)
- [테스트 방법](#테스트-방법)
- [계정 차단 관련 리서치](#계정-차단-관련-리서치)
- [미팅 노트](#미팅-노트)

# 수집 방법 목록

1. Telegram API
   1. [telethon](./doc/telethon.md)
   2. [pyrogram](./doc/pyrogram.md)
2. Telegram Bot API
   1. [python-telegram-bot](./doc/telegram-bot.md)

# 방법 별 검토 사항

- 개요
- 리서치 환경
- 필수 데이터 수집 가능 여부
- 그 외 데이터 수집 가능 여부
- 장점, 단점, 참고사항

# 수집 필수 데이터

```
channel_id                      : int     // 수집한 채널 id
channel_title                   : string  // 수집한 채널명
message_id                      : int     // 메시지 id
message                         : string  // 메시지 내용
is_forwarded                    : bool    // 전달된 메시지 여부
forward_from_channel_id         : int     // 원 채널 id
forward_from_channel_title      : string  // 원 채널명
is_reply                        : bool    // 답글 여부
reply_to_message_id             : int     // 답글의 원메시지 id
reply_to_message                : string  // 답글의 원메시지 내용
message_link                    : string  // 해당 메시지의 link
photo_file                      : string  // 이미지 파일 다운로드 가능여부
document_file                   : string  // 문서 파일 다운로드 가능여부
datetime                        : int     // 시간/날짜, timestamp
```

## (참고) 텔레그램 메시지 데이터 구조

<img src="./doc/images/message_structure.png" width="350px" alt="Message object structure">

# 테스트 방법

1. 테스트용 채널(`@kspark123`) 및 봇(`@kspark123_bot`) 생성. 봇을 채널 관리자로 추가.
2. 메시지 타입별 데이터 셋 준비 (4종류 : Text, Photo, File, WebPage)
3. 데이터 수집 코드를 작성하며 응답 값 확인
4. [메시지 타입별 예시 데이터](./doc/data_set.md) 참고

# 계정 차단 관련 리서치

[제약 사항 & 계정 차단 관련 리서치](./doc/restrictions.md)

# 미팅 노트

- [2024-02-29(목) 10:00 @online](./doc/2024-02-29.md)
