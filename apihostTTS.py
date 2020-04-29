import requests
import shutil
import os
import time
import re
from pygame import mixer

mixer.init()


def playmp3(filepath):
    """Запускаем mp3 файл"""
    global stop
    stop = 0
    song = mixer.music.load(filepath)
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.1)
        if stop == 1:
            break
    mixer.music.stop()


def speakme(mytext):
    """Функция говорящая фразу вслух"""
    fm = os.path.join('mp3/', re.sub('[^а-яА-Я]', '', mytext))
    fm = fm[:200]+'.mp3'
    if not(os.path.exists(fm)):
        mytext = mytext.replace(' ', '+')
        myurl = 'https://apihost.ru/php/voice.php?&text='+mytext+'&format=mp3&'
        f'lang=ru-RU&speed=1.0&emotion=neutral&speaker=oksana&robot=1&download'
        r = requests.get(myurl, stream=True)
        if r.status_code == 200:
            with open(fm, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print(f'Сервер вернул код: {r.status_code}')
    playmp3(fm)


speakme('Приветствую тебя, Иван!')
speakme('Сегодня мы научились использовать синтез речи на радость людям!')
