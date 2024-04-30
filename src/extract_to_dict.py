from datetime import datetime
import pytz
import logging


async def extract_from(message) -> dict:
  message_dict = {}
    
  # 수집한 채널 id
  message_dict['channel_id'] = message.chat.id
  
  # 수집한 채널명
  message_dict['channel_title'] = message.chat.title
  
  # 수집한 username
  message_dict['channel_username'] = message.chat.username
  
  # 메시지 id
  message_dict['message_id'] = message.id
  
  ## 전달된 메시지
  is_forwarded = message.forward is not None
  # 전달된 메시지 여부
  message_dict['is_forwarded'] = is_forwarded
  
  # 전달된 메시지 여부
  # 전달된 메시지임에도 message.forward.chat이 None 인 경우가 있어 조건 추가함
  #   ex) channel_id=1500265128, message_id=59598
  if is_forwarded and message.forward.chat is not None:
    # 원 채널 id
    message_dict['forward_from_channel_id'] = message.forward.chat.id
    # 원 채널명
    message_dict['forward_from_channel_title'] = message.forward.chat.title
    # 원 채널 username
    message_dict['forward_from_channel_username'] = message.forward.chat.username
  
  # 메시지 링크
  # https://core.telegram.org/api/links#message-links
  message_dict['message_link'] = f't.me/{message.chat.username}/{message.id}'
  
  ## 답글 메시지
  is_reply = message.is_reply
  # 답글 여부
  message_dict['is_reply'] = is_reply
  
  # 답글 여부
  if is_reply:
    # 답글의 원메시지 id
    message_dict['reply_to_message_id'] = message.reply_to.reply_to_msg_id
    # 답글의 원메시지 내용
    reply_message = await message.get_reply_message()
    try:
      message_dict['reply_to_message'] = reply_message.text
    except:
      logging.error(f"REPLY ERROR :: {message_dict['message_link']}")
      message_dict['reply_to_message'] = ''
  
  # for private channel, you should be a member of the channel.
  # f't.me/c/{channel_id}/{message_id}'
  
  # 사진/파일/웹피잊
  has_photo = message.photo is not None
  has_document = message.document is not None
  message_dict['has_photo'] = has_photo
  message_dict['has_document'] = has_document
  message_dict['has_webpage'] = message.web_preview is not None
  
  # 시간/날짜
  date_utc = datetime.utcfromtimestamp(round(message.date.timestamp()))
  seoul_tz = pytz.timezone('Asia/Seoul')
  date_seoul = date_utc.replace(tzinfo=pytz.utc).astimezone(seoul_tz)
  # datetime 객체를 문자열로 변환 (예: '2022-03-13 15:26:29')
  date_str = date_seoul.strftime('%Y-%m-%d %H:%M:%S')
  message_dict['write_time'] = date_str
  
  
  # 메시지 내용
  message_dict['message'] = message.text.replace('\n','\\n')
  return message_dict
