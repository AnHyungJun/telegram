import os
import json
import logging
import traceback

from typing import *
from datetime import datetime, timedelta

import requests
from urlextract import URLExtract        # 추가 설치 필요
from expiringdict import ExpiringDict    # 추가 설치 필요
from bs4 import BeautifulSoup            # 추가 설치 필요
from time import sleep

class TelegramUrlProcessor():

    def __init__(self):

        self.url_extractor = URLExtract()
        self.data_cache = ExpiringDict(max_len=10000, max_age_seconds=60*60*24*7)

        # self.proxies = {
        #     "http": "http://proxypool2.daumsoft.com:7168",
        #     "https": "http://proxypool2.daumsoft.com:7168"
        # }

        self.headers = { # url shorter 서비스 redirect 거부 우회용 gin.gl, han.gl
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        ####################################
        # 2025-08-13 텔레그램 데이터에서 embedded link 수집 오류시 RETRY 횟수를 3회에서 1회로 축소 (마켓보이스 데이터 업데이트 지연 최소화)
        ####################################
        self.max_retry = 1
        self.retry_interval = 5 # 5초 sleep
        self.timeout = 5        # 응답대기 5초

    def crawl_html(self, url: str) -> str:

        conn_url = url
        if "http://" not in url and "https://" not in url:
            conn_url = "https://"+url

        for retry in range(self.max_retry):
            try:
                #response = requests.get(conn_url, headers=self.headers, proxies=self.proxies, allow_redirects=True, timeout=self.timeout)
                response = requests.get(conn_url, headers=self.headers, allow_redirects=True, timeout=self.timeout)
                sleep(1)
                content_type = response.headers['content-type']
                if not 'charset' in content_type:
                    response.encoding = response.apparent_encoding
                return response.text
            except Exception as e:
                if retry < self.max_retry-1:
                    sleep(self.retry_interval)
                else:
                    logging.warning(f"""Can`t connect {conn_url}""")

        return ""

    def extract_metadata(self, url, html: str) -> Tuple[str, str, str]:

        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logging.warn(f"""BeautifulSoup parsing error ::: {url}""")
            return "", "", ""

        title = ""
        if soup.find("meta", {"property": "og:title"}):
            title = soup.find("meta", {"property": "og:title"}).get("content", '')
        elif soup.find("meta", {"name": "twitter:title"}):
            title = soup.find("meta", {"name": "twitter:title"}).get("content", '')
        elif soup.title:
            title = soup.title.string

        description = ""
        if soup.find("meta", {"property": "og:description"}):
            description = soup.find("meta", {"property": "og:description"}).get("content", '')
        elif soup.find("meta", {"name": "twitter:description"}):
            description = soup.find("meta", {"name": "twitter:description"}).get("content", '')
        elif soup.find("meta", {"name": "description"}):
            description = soup.find("meta", {"name": "description"}).get("content", '')

        image = ""
        if soup.find("meta", {"property": "og:image"}):
            image = soup.find("meta", {"property": "og:image"}).get("content", '')
        elif soup.find("meta", {"name": "twitter:image"}):
            image = soup.find("meta", {"name": "twitter:image"}).get("content", '')
        elif soup.find("meta", {"name": "image"}):
            image = soup.find("meta", {"name": "image"}).get("content", '')

        return title, description, image

    def extract_urls_and_metadata(self, input_text: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        r""" 텔레그램 본문에서 URL을 추출한 뒤, 각 URL의 HTML 메타데이터를 추출하여 본문을 치환하는 메소드

        Args:
            input_text: 텔레그램 본문

        Returns:
            1. embedded_urls: 본문에서 추출된 URL 목록
            2. url_to_metadata: [{"url": "...", "title": "...", "description": "..."}, ...] 리스트
        """

        input_text = input_text.replace("\\n", "\n").replace("\\r", "").replace("nhttp", "n http")

        embedded_urls = [_url for _url in self.url_extractor.find_urls(input_text) if "t.me/" not in _url]
        logging.debug(f"""{embedded_urls=}""")

        url_to_metadata = []

        for url in embedded_urls:
            if url in self.data_cache:
                title = self.data_cache[url]["title"]
                description = self.data_cache[url]["description"]
                image = self.data_cache[url]["image"] if "image" in self.data_cache[url] else "" # image가 나중에 추가된거라, 시간이 충분히 지나면 if 체크는 없어도 됨
            else:
                html = self.crawl_html(url)
                if not html:
                    continue
                title, description, image = self.extract_metadata(url, html)

            if not title and not description and not image:
                continue

            metadata = {
                "url": url,
                "title": title if title else None,
                "description": description if description else None,
                "image": image if image else None
            }
            url_to_metadata.append(metadata)

            if url not in self.data_cache:
                self.data_cache[url] = metadata

        return embedded_urls, url_to_metadata

    def postprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        r"""텔레그램 메세지에서 embedded url 들에 대한 메타데이터(제목,요약,이미지)들을 추가 수집"""

        if not data["message"]: data["message"] = ""

        embedded_urls, url_metadata = self.extract_urls_and_metadata(data["message"])

        data["embedded_urls"] = embedded_urls
        data["url_metadata"] = url_metadata
        return data


# test1.
# 샘플 수집 테스트
def crawl_test():

    input_text = """🔶11월 26일 시장 주도주 \\n\\n▶️재건\\n건설기계업계, 우크라이나 재건 시장 진출 본격화\\n(https://buly.kr/AljTKHf)\\n-재건: 에스와이스틸텍, 대동기어, 대동, SG, 전진건설로봇, 한미글로벌\\n\\n▶️정치\\n이재명 '위증교사' 1심 무죄…\"위증 하도록 할 고의 없어\"\\n(https://buly.kr/2fccClM)\\n-이재명: 동신건설, 에이텍, 에이텍모빌리티, 일성건설, 이스타코\\n-김동연: PN풍년, SG글로벌, 윈하이텍, 보해양조, 대창 \\n\\n▶️AI\\n애플 이어 삼성도?…갤럭시 AI에 '챗GPT' 이식되나\\n(https://buly.kr/5UGjq9M)\\n-AI: 에스피소프트, 마음AI, 솔트룩스, 이스트소프트  \\n-의료AI: 루닛, 쓰리빌리언, 셀바스AI, 딥노이드, 뷰노 \\n\\n▶️STO\\n증권사 '조각투자 시대' 성큼…'법제화' 훈풍\\n(https://buly.kr/9iEvRQD)\\n-STO: 핑거, 서울옥션, 케이옥션, 갤럭시아머니트리, 아톤\\n\\n▶️전력\\n전선·케이블株 강세‥美의 중국산 제한 움직임 ‘반사이익’ 기대\\n(https://buly.kr/DEY53zr)\\n-전력: LS ELECTRIC, LS마린솔루션, 가온전선, 제룡전기\\n\\n▶️엔터\\n한한령 해제 기대감에 엔터株↑\\n(https://buly.kr/2qXNBbz)\\n-엔터: YG PLUS, 하이브, 에스엠, JYP Ent, 와이지엔터\\n\\n▶️대왕고래\\n“대왕고래 잡자”…전 세계서 도착하는 시추 자재들, 부산신항에 빼곡\\n(https://buly.kr/FWRvoMx)\\n-대왕고래: 화성밸브, 넥스틸,  한국가스공사 \\n\\n▶️조선\\n10조 대어 놓친 韓조선, ‘원팀’ 물꼬 튼 한화오션·현대重\\n(https://buly.kr/2UhrE0J)\\n-조선: 성광벤드, 한화오션, HD현대중공업, 삼성중공업, 일승, 태광"""
    #input_text = """테스트1 https://zrr.kr/BWgNom"""

    url_postprocessor = TelegramUrlProcessor()
    embedded_urls, url_metadata = url_postprocessor.extract_urls_and_metadata(input_text)
    print(json.dumps(embedded_urls, ensure_ascii=False, indent=4))
    print(json.dumps(url_metadata, ensure_ascii=False, indent=4))


# test2.
# 샘플 후처리 테스트
def telegram_post_process_test(input_file, output_file):

    url_postprocessor = TelegramUrlProcessor()

    with open(input_file) as f:
        data_list = [json.loads(line) for line in f]

    new_data_list = [url_postprocessor.postprocess(data) for data in data_list]
    file_path = os.path.expanduser('~/telegram/out/test/a')
    with open(file_path, 'w') as f:
        for data in new_data_list:
            f.write(json.dumps(data, ensure_ascii=False)+'\n')


# test3.
# 변경된 수집단 input에 대해 기존 코드 동작 테스트 (수집단에서는 신경쓸 필요 없음)
def dip_preprocess_test(input_file, output_file):
    r""" 전처리 메소드
    """

    url_postprocessor = TelegramUrlProcessor()

    with open(input_file) as f:
        data_list = [json.loads(line) for line in f]

    return_list = []
    for data in data_list:
        try:
            if not data["message"]: data["message"] = ""

            ####################################
            # 2025-08-08 텔레그램 데이터는 더이상 채널 필터링을 하지 않음 (수집된 데이터 모두를 사용)
            ####################################
            #if data["channel_username"] not in self.target_channel: continue

            article_id = adjust_some_fields(data)

            # 본문에 embedded url은 한개 이상 있지만 metadata를 하나도 수집하지 못한 경우, 스킵
            if data["embedded_urls"] and not data["url_metadata"]:
                logging.warning(f"""FAIL: gathering telegram {article_id} HTML meta data""")
                continue

            # 본문 텍스트의 embedded url을 title, description으로 치환
            modified_text = data["message"].replace("\\n", "\n").replace("\\r", "").replace("nhttp", "n http")
            for metadata in data["url_metadata"]:
                title = metadata["title"] if metadata["title"] else ""
                description = metadata["description"] if metadata["description"] else ""
                modified_text = modified_text.replace(metadata["url"], f"""{title} {description}""")

            doc = {
                "article_id": article_id,
                "write_dt_hms": data["write_time"],
                "group_id": None, # it filled after clustering
                "document_url": data["message_link"],
                "image_url": None,
                "file_path": data["file_path"],
                "file_name": data["file_name"],
                "source": {
                    "name": "텔레그램",
                    "author": data["channel_title"],
                    "id": str(data["channel_id"]),
                },
                "title": None,
                "contents": data["message"],
                "summary_vaiv": None,
                #"keyword": self.tag_all_keywords(modified_text),
                "keyword": [],
                #"url_metadata": url_metadata,
                "url_metadata": data["url_metadata"],
                "doc": modified_text, # for clustering, delete after clustering
            }

            return_list.append(doc)

        except:
            logging.error(f"""telegram preprocessing error {traceback.format_exc()}""")

    with open(output_file, 'w') as f:
        for data in return_list:
            f.write(json.dumps(data, ensure_ascii=False)+'\n')


def adjust_some_fields(data):

    # reply, forwarded 등에 따른 article_id 포맷 보정
    if data["is_reply"]:
        article_id = f"{data['channel_id']}##{data['message_id']}##{data['channel_id']}##{data['reply_to_message_id']}"
    elif data["is_forwarded"]:
        article_id = f"{data['channel_id']}##{data['message_id']}##{data['forward_from_channel_id']}##{data['forward_from_message_id']}"
    else:
        article_id = f"{data['channel_id']}##{data['message_id']}##{data['channel_id']}##{data['message_id']}"

    # reply_to_message 보정
    data["reply_to_message"] = data["reply_to_message"] if  ("reply_to_message" in data and data["reply_to_message"]) in data else ""

    # message_link 보정
    if ("http://" not in data["message_link"]) and ("https://" not in data["message_link"]):
        data["message_link"] = "https://" + data["message_link"]

    return article_id


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(levelname)s (%(filename)s %(lineno)d) ::: %(message)s',level=logging.DEBUG)

    #crawl_test()
    telegram_post_process_test('/locdisk/telegram_data/telegram_message.20250808.json', '~/telegram/out/test/a')
    #dip_preprocess_test('postprocessed.json', 'dip_preprocessed.json')
    # import os
    # file_path = os.path.expanduser('~/telegram/out/test/a')
    # with open(file_path,'w') as f:
    #     f.write('@@@@')