import requests, shutil, os, time, re
from pygame import mixer

mixer.init()

# Запускаем mp3 файл
def playmp3(filepath):
    global stop
    stop=0
    song = mixer.music.load(filepath)
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.1)
        if(stop==1):
            break
    mixer.music.stop()

# Функция говорящая фразу вслух
def speakme(mytext):
    print('Робот сказал: '+mytext)
    fm='mp3/'+re.sub('[^а-яА-Я]', '', mytext)
    fm=fm[:200]
    fm=fm+'.mp3'
    if not(os.path.exists(fm)): 
        mytext=mytext.replace(' ','+')
        myurl='https://apihost.ru/php/voice.php?&text='+mytext+'&format=mp3&lang=ru-RU&speed=1.0&emotion=neutral&speaker=oksana&robot=1&download'
        r = requests.get(myurl, stream=True)
        if r.status_code == 200:
            with open(fm, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            f.close()
    playmp3(fm)

speakme('Приветствую тебя, Иван!')
speakme('Сегодня мы научились использовать синтез речи на радость людям!')




