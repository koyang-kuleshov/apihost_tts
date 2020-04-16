import requests, shutil, os, time
from pygame import mixer

# Говорит фразу не более 1000 символов
def speakme(mytext):
    mytext=mytext.replace(' ','+')
    myurl='https://apihost.ru/php/voice.php?&text='+mytext+'&format=mp3&lang=ru-RU&speed=1.0&emotion=neutral&speaker=oksana&robot=1&download'
    r = requests.get(myurl, stream=True)
    if r.status_code == 200:
        with open('test.mp3', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        mixer.init()
        song = mixer.music.load('test.mp3')
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)
        mixer.music.stop()
        time.sleep(1)

speakme('Приветствую тебя, человек!')




