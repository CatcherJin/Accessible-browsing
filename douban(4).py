import requests
from bs4 import BeautifulSoup
import re
from aip import AipSpeech
from pyaudio import PyAudio,paInt16
import wave
import os
import pymysql
from wyymusic import Music
from subprocess import run
import time

#此处填写百度api账号
APPID = ''
APPKEY = ''
SECRETKEY = ''
client = AipSpeech(APPID, APPKEY, SECRETKEY)

KEYWORD = ''
KIND = '书籍'
URL = 'https://www.douban.com/'
headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}

db = None
cursor = None

framerate=8000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=2
chunk=2014

IN_FILE = 'infile.wav'
OUT_FILE = 'outfile.mp3'
DECIDE_FILE = 'decide.mp3'
CONTINUE_FILE = 'continue.mp3'

BASE_URL = r'https://www.douban.com/search?q='
MAX_NUMBER = 10

HOST = 'localhost'
USER = 'root'
PASSWORD = '123456'
PORT = 3306
DB = 'Python'

MUSIC_BASE_URL = 'https://music.163.com/search/m/?s=%stype=1'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_book_url(KIND, KEYWORD):
    response = requests.get(url=BASE_URL + KEYWORD, headers=headers, verify=False).text
    soup = BeautifulSoup(response, 'lxml')
    STAR = 0
    url = ''
    number = 0
    star = 0
    for book in soup.select('div.result-list > div.result'):
        number += 1
        if book.select('div.content > div.title > h3 > span')[0].string[1:-1].strip() == KIND and \
                book.select('div.content > div.title > h3 > a')[0].string.strip() == KEYWORD:
            try:
                if is_number(book.select('div.content > div.title > div.rating-info > span.rating_nums')[0].string):
                    star = float(book.select('div.content > div.title > div.rating-info > span.rating_nums')[0].string)
            except:
                star = 0
            if star > STAR:
                STAR = star
                url = book.select('div.content > div.title > h3 > a')[0].attrs['href']
        if number > MAX_NUMBER:
            break
    if url:
        return url
    else:
        print('找不到指定内容')
        return None

def get_book_information(url):
    L = {}

    response = requests.get(url=url, headers = headers, verify=False).text
    soup = BeautifulSoup(response, 'lxml')
    text = soup.select('div.intro')[0].get_text()
    writer = re.compile('作者:\s*(\S*?)\s*(\S*?)\s*出版社')
    publishing_house = re.compile('出版社:\s*(\S*?)\s*原作名')
    writer_old_name = re.compile('原作名:\s*(\S*?)\s*译者')
    transformer = re.compile('译者:\s*(\S*?)\s*出版年')
    year = re.compile('出版年:\s*(\S*?)\s*页数')
    page_number = re.compile('页数:\s*(\S*?)\s*定价')
    price = re.compile('定价:\s*(\S*?)\s*装帧')
    binding_layout = re.compile('装帧:\s*(\S*?)\s*丛书')
    series = re.compile('丛书:\s*(\S*?)\s*ISBN')
    ISBN = re.compile('ISBN:\s*(\d*)')
    all = soup.select('div#info')[0].get_text()
    if writer.search(all) and writer.search(all):
        L['作者'] = writer.search(all).group(1) + writer.search(all).group(2)
    else:
        L['作者'] = ''
    if publishing_house.search(all):
        L['出版社'] = publishing_house.search(all).group(1)
    else:
        L['出版社'] = ''
    if writer_old_name.search(all):
        L['原作名'] = writer_old_name.search(all).group(1)
    else:
        L['原作名'] = ''
    if transformer.search(all):
        L['译者'] = transformer.search(all).group(1)
    else:
        L['译者'] = ''
    if year.search(all):
        L['出版年'] = year.search(all).group(1)
    else:
        L['出版年'] = ''
    if page_number.search(all):
        L['页数'] = page_number.search(all).group(1)
    else:
        L['页数'] = ''
    if price.search(all):
        L['定价'] = price.search(all).group(1)
    else:
        L['定价'] = ''
    if binding_layout.search(all):
        L['装帧'] = binding_layout.search(all).group(1)
    else:
        L['装帧'] = ''
    if series.search(all):
        L['丛书'] = series.search(all).group(1)
    else:
        L['丛书'] = ''
    # if ISBN.search(all):
    #     L['ISBN'] = ISBN.search(all).group(1)
    if text:
        L['内容简洁'] = text
    else:
        L['内容简洁'] = ''
    return L


'''电影/电视剧'''
def get_movie_information(url):
    L = {}

    response = requests.get(url=url, headers=headers, verify=False).text
    soup = BeautifulSoup(response, 'lxml')
    text = soup.select('div.related-info div.indent span')[0].get_text()
    director = re.compile('导演:\s*(.*?)\s*编剧')
    scriptwriter = re.compile('编剧:\s*(.*?)\s*主演')
    protagonist = re.compile('主演:\s*(.*?)\s*类型')
    type = re.compile('类型:\s*(.*?)\s*制片国家/地区')
    country = re.compile('制片国家/地区:\s*(\S*?)\s*语言')
    language = re.compile('语言:\s*(\S*?)\s*首播')
    debut = re.compile('首播:\s*(\S*?)\s*集数')
    episode_number = re.compile('集数:\s*(\S*?)\s*单集片长')
    length = re.compile('单集片长:\s*(\S*?)\s*又名')
    other_name = re.compile('又名:\s*(.*?)\s*IMDB链接')
    IMDB = re.compile('IMDB链接:\s*(.*)')

    movie_type = re.compile('类型:\s*(.*?)\s*官方网站')
    release_date = re.compile('上映日期:\s*(.*?)\s*片长')
    movie_length = re.compile('片长:\s*(.*?)\s*又名')
    all = soup.select('div#info')[0].get_text()
    if director.search(all) and director.search(all):
        L['导演'] = director.search(all).group(1)
    else:
        L['导演'] = ''
    if scriptwriter.search(all):
        L['编剧'] = scriptwriter.search(all).group(1)
    else:
        L['编剧'] = ''
    if protagonist.search(all):
        L['主演'] = protagonist.search(all).group(1)
    else:
        L['主演'] = ''
    if type.search(all):
        L['类型'] = type.search(all).group(1)
    else:
        L['类型'] = ''
    if country.search(all):
        L['制片国家/地区'] = country.search(all).group(1)
    else:
        L['制片国家/地区'] = ''
    if language.search(all):
        L['语言'] = language.search(all).group(1)
    else:
        L['语言'] = ''
    if debut.search(all):
        L['首播'] = debut.search(all).group(1)
    else:
        L['首播'] = ''
    if episode_number.search(all):
        L['集数'] = episode_number.search(all).group(1)
    else:
        L['集数'] = ''
    if length.search(all):
        L['时间'] = length.search(all).group(1)
    else:
        L['时间'] = ''
    if other_name.search(all):
        L['又名'] = other_name.search(all).group(1)
    else:
        L['又名'] = ''
    if IMDB.search(all):
        L['IMDB链接'] = IMDB.search(all).group(1)
    else:
        L['IMDB链接'] = ''
    if text:
        L['内容简洁'] = text
    else:
        L['内容简洁'] = ''

    if movie_type.search(all):
        L['类型'] = movie_type.search(all).group(1)
    else:
        L['类型'] = ''
    if movie_length.search(all):
        L['时间'] = movie_length.search(all).group(1)
    else:
        L['时间'] = ''
    if release_date.search(all):
        L['首播'] = release_date.search(all).group(1)
    else:
        L['首播'] = ''
    return L

def get_music_information(KEYWORD):
    response = requests.get(url=MUSIC_BASE_URL % (KEYWORD), headers=headers, verify = False)

# 文字转语音
def textTovoicefile(text):
    result = client.synthesis(text, 'zh', 1, {
        'vol': 5,
    })
    # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
    if not isinstance(result, dict):
        with open(OUT_FILE, 'wb') as f:
            f.write(result)


def decide():
    result = client.synthesis('是否继续查询', 'zh', 1, {
        'vol': 5,
    })
    # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
    if not isinstance(result, dict):
        with open(CONTINUE_FILE, 'wb') as f:
            f.write(result)

# 读取文件获取语音
def get_file_content(filePath):
    # cmd_str = "ffmpeg -y  -i %s  -acodec pcm_s16le -f s16le -ac 1 -ar 16000 %s.pcm" % (filePath, filePath)
    # os.system(cmd_str)  # 调用系统命令ffmpeg,传入音频文件名即可
    with open(filePath + '.pcm', 'rb') as fp:
        return fp.read()

# 语音转文字
def voiceTotext(filepath):
    cmd_str = "ffmpeg -y -i %s -acodec pcm_s16le -f s16le -ac 1 -ar 16000 %s.pcm" % (filepath, filepath)
    os.system(cmd_str)  # 调用系统命令ffmpeg,传入音频文件名即可
    a = client.asr(get_file_content(filepath), 'pcm', 16000, {
        'dev_pid': 1536,
    })
    if a.get('result'):
        print(a.get('result')[0])
        return a.get('result')[0]       # 返回识别文字

def save_wave_file(filename,data):
    '''save the date to the wavfile'''
    wf=wave.open(filename,'wb')
    wf.setnchannels(channels)#声道
    wf.setsampwidth(sampwidth)#采样字节 1 or 2
    wf.setframerate(framerate)#采样频率 8000 or 16000
    wf.writeframes(b"".join(data))
    wf.close()

# 录语音保存成01.wav
def my_record():
    pa=PyAudio()
    stream=pa.open(format = paInt16,channels=1,
                   rate=framerate,input=True,
                   frames_per_buffer=NUM_SAMPLES)
    my_buf=[]
    count=0
    while count<TIME*5:#控制录音时间
        string_audio_data = stream.read(NUM_SAMPLES)#一次性录音采样字节大小
        my_buf.append(string_audio_data)
        count+=1
        print('.')
    save_wave_file(IN_FILE,my_buf)
    stream.close()

def play_mp3():
    os.system(OUT_FILE)
    # run(OUT_FILE, shell=True)

def database_init():
    global db
    global cursor
    db = pymysql.connect(host=HOST, user=USER, password = PASSWORD, port=PORT, db=DB)
    cursor = db.cursor()
    book_sql = 'CREATE TABLE IF NOT EXISTS book (name VARCHAR(255) NOT NULL, writer VARCHAR(255) NOT NULL, ' \
          'publishing_house VARCHAR(255) NOT NULL, writer_old_name VARCHAR(255), transformer VARCHAR(255), ' \
          'year VARCHAR(255), page_name VARCHAR(255), price VARCHAR(255), binding_layout VARCHAR(255), ' \
          'series VARCHAR(255),text VARCHAR (10000), PRIMARY KEY(name, writer, publishing_house))'
    movie_sql = 'CREATE TABLE IF NOT EXISTS movie (name VARCHAR(255) NOT NULL, director VARCHAR(255) NOT NULL, ' \
          'scriptwriter VARCHAR(255) NOT NULL, protagonist VARCHAR(255), type VARCHAR(255), ' \
          'country VARCHAR(255), language VARCHAR(255), debut VARCHAR(255), episode_number VARCHAR(255), ' \
          'length VARCHAR(255), other_name VARCHAR(255), IMDB VARCHAR(255), text VARCHAR(10000), PRIMARY KEY(name, director, scriptwriter))'
    teleplay_sql = 'CREATE TABLE IF NOT EXISTS teteplay (name VARCHAR(255) NOT NULL, director VARCHAR(255) NOT NULL, ' \
          'scriptwriter VARCHAR(255) NOT NULL, protagonist VARCHAR(255), type VARCHAR(255), ' \
          'country VARCHAR(255), language VARCHAR(255), debut VARCHAR(255), episode_number VARCHAR(255), ' \
          'length VARCHAR(255), other_name VARCHAR(255), IMDB VARCHAR(255), text VARCHAR(10000), PRIMARY KEY(name, director, scriptwriter))'
    cursor.execute(book_sql)
    cursor.execute(movie_sql)
    cursor.execute(teleplay_sql)

def database_close():
    global db
    db.close()

def database(L):
    global db
    global cursor
    book_sql = 'INSERT INTO book VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    movie_sql = 'INSERT INTO movie VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    teteplay_sql = 'INSERT INTO teteplay VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    try:
        if KIND == '书籍':
            cursor.execute(book_sql, L)
        elif KIND == '电影':
            cursor.execute(movie_sql, L)
        elif KIND == '电视剧':
            cursor.execute(teteplay_sql, L)
        try:
            db.commit()
        except:
            db.rollback()
    except:
        pass

def find_database():
    table = ''
    sql = ''
    one = ''
    if KIND == '书籍':
        table = 'book'
    elif KIND == '电视剧':
        table = 'teteplay'
    elif KIND == '电影':
        table = 'movie'
    sql = 'select * from ' + table + ' where name="' + KEYWORD + '"'
    if table:
        try:
            print('开始进行数据库查找')
            cursor.execute(sql)
            if cursor.rowcount >= 1:
                result = cursor.fetchall()
                return result[0]
            else:
                return None
        except:
            return None
    else:
        return None


def get_kind():
    global KIND
    while True:
        my_record()
        KIND = voiceTotext(IN_FILE)
        if KIND == '书籍' or KIND == '电影' or KIND == '电视剧' or KIND == '音乐':
            break
        else:
            os.system(DECIDE_FILE)
            time.sleep(2)

def all(L, content):
    string = ''
    if content:
        L.append(KEYWORD)
        for key, value in content.items():
            if value:
                string = string + ',' + str(key) + ',' + str(value)
                L.append(str(value))
            else:
                L.append('')
    else:
        print('搜索失败')
    L = tuple(L)
    database(L)
    textTovoicefile(string)
    play_mp3()

def all_2(L, content):
    string = ''
    if content:
        L.append(KEYWORD)
        for key, value in content.items():
            if value:
                string = string + ',' + str(key) + ',' + str(value)
                L.append(str(value))
            else:
                L.append('')
    else:
        print('搜索失败')
    textTovoicefile(string)
    play_mp3()


if __name__ == '__main__':
    database_init()
    while True:

        L = []
        get_kind()
        content = {}
        my_record()  # 录音并保存成音频文件
        KEYWORD = voiceTotext(IN_FILE)  # 语音转文字
        if KIND == '音乐':
            music = Music(KEYWORD)
            music.play()
            flag = input('是否继续Y/N:')
            if flag == 'Y' or flag == 'y':
                continue
            else:
                break
        C = find_database()
        if C:
            if KIND == '书籍':
                index = ['名字', '作者', '出版社', '原作名', '译者', '出版年', '页数', '定价', '装帧', '丛书', '内容简洁']
                i = 0
                for index in index:
                    content[index] = C[i]
                    i  += 1
                all_2(L, content)
            elif KIND == '电影' or KIND == '电视剧':
                index = ['名字', '导演', '编剧', '主演', '类型', '制片国家/地区', '语言', '首播', '集数', '时间', '又名', 'IMDB链接', '内容简洁']
                i = 0
                for index in index:
                    content[index] = C[i]
                    i += 1
                all_2(L, content)
                flag = input('是否继续Y/N:')
                if flag == 'Y' or flag == 'y':
                    continue
                else:
                    break

        # search(URL, KEYWORD)
        url = get_book_url(KIND, KEYWORD)
        print('数据库中不存在，进行网页搜索')
        if url:
            if KIND == '书籍':
                content = get_book_information(get_book_url(KIND, KEYWORD))
                all(L, content)
            elif KIND == '电影' or KIND== '电视剧':
                content = get_movie_information(get_book_url(KIND, KEYWORD))
                all(L, content)
            else:
                print('转换错误，请重试')
                continue
        flag = input('是否继续Y/N:')
        if flag == 'Y' or flag == 'y':
            continue
        else:
            break

    database_close()


