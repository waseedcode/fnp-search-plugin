#VERSION: 1.00
# AUTHORS: waseedcode
# LICENSING INFORMATION

from html.parser import HTMLParser
from helpers import download_file, retrieve_url
from novaprinter import prettyPrinter

import base64
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode, unquote_plus
from urllib.error import HTTPError
import os
from time import sleep

HOME_DIR = os.path.expanduser("~")

class HttpClient:
    def __init__(self, api_key=None):
        self.url = "https://fearnopeer.com"
        self.api_key = api_key
        self.num_rate_limit_hit = 0
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key is None:
            with open(f"{HOME_DIR}/.fnp_api_key.txt", "r") as f:
                self.api_key = f.read().strip()
        if self.api_key:
            self.headers["Authorization"] = "Basic " + base64.b64encode(f"apikey:{self.api_key}".encode()).decode()

    def get(self, url, params=None):
        if params:
            params = {k: unquote_plus(v) for k, v in params.items()}
            url += "?" + urlencode(params)
        request = Request(url, headers=self.headers)
        try:
            with urlopen(request) as response:
                try:
                    remaining_rate_limit = int(response.getheader("X-RateLimit-Remaining"))
                except TypeError:
                    remaining_rate_limit = 30
                return self._response_to_json(response), response.status, remaining_rate_limit
        except HTTPError as e:
            return self._response_to_json(response), e.code
    
    def get_all_by_cursor(self, url, params=None):
        def parse_result(result):
            result = result["attributes"]
            link = result.get("download_link", -1)
            name = result.get("name", -1)
            size = result.get("size", -1)
            size = f"{size} B"
            seeds = result.get("seeders", -1)
            leech = result.get("leechers", -1)
            engine_url = "https://fearnopeer.com"
            desc_link = result.get("details_link", -1)
            qbit_result = {
                "link": link,
                "name": name,
                "size": size,
                "seeds": seeds,
                "leech": leech,
                "engine_url": engine_url,
                "desc_link": desc_link
            }
            prettyPrinter(qbit_result)
        response, status_code, remaining_rate_limit = self.get(url, params)
        if status_code == 200:
            if remaining_rate_limit <= 5:
                self.num_rate_limit_hit += 1
                sleep(6)
            if self.num_rate_limit_hit >= 3: # if we hit the rate limit 3 times( i.e. 150x requests)
                return
            for result in response["data"]:
                parse_result(result)

            while response["links"]["next"]:
                response, status_code, remaining_rate_limit = self.get(response["links"]["next"])
                if status_code == 200:
                    if remaining_rate_limit <= 5:
                        self.num_rate_limit_hit += 1
                        sleep(6)
                    if self.num_rate_limit_hit >= 3:
                        return
                    for result in response["data"]:
                        parse_result(result)

    
    def _response_to_json(self, response):
        return json.loads(response.read().decode())

class fnp(object):
    url = 'https://www.fearnopeer.com'
    name = 'Fear No Peer'
    supported_categories = {
        'all': '0',
        'anime': '7',
        'games': '2',
        'movies': '6',
        'music': '1',
        'software': '3',
        'tv': '4'
    }

    def __init__(self):
        self.base_url = "https://fearnopeer.com/api"
        self.client = HttpClient()

    def download_torrent(self, info):
        print(download_file(info))

    def search(self, what, cat='all'):
        self.client.get_all_by_cursor(f"{self.base_url}/torrents/filter", params={"name": what, "category_id": self.supported_categories[cat]})
