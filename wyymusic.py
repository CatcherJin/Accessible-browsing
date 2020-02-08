import requests
import json
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

BASE_URL = 'http://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s=%s&type=1&offset=0&total=true&limit=1'

PLAY_URL = 'http://link.hhtjim.com/163/%s.mp3'

headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}

class Music:
    def __init__(self, KEYWORD):
        self.url = BASE_URL % (KEYWORD)

    def get_ID(self):
        response = requests.post(self.url, headers=headers).text
        response = json.loads(response)
        self.id = response.get('result').get('songs')[0].get('id')
        self.name = response.get('result').get('songs')[0].get('name')
        print(self.id, self.name, sep='\n')

    def play(self):
        self.get_ID()
        play_url = PLAY_URL % (self.id)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.wait = WebDriverWait(self.browser, 10)
        self.browser.get(play_url)




