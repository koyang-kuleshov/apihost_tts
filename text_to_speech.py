import requests
import csv
from os import system, path
from io import BytesIO
import wave

from settings import IAM_TOKEN, FOLDER_ID


def data():
    with open('src/texts2.csv', "r") as read_f:
        reader = csv.DictReader(read_f, delimiter=',')
        for line in reader:
            file_num = line["Номер"] if len(line["Номер"]) > 1 \
                else '0' + line["Номер"]
            file_name = '-' + line["Триггер"].replace(' ', '-')
            raw = file_num + file_name + '.raw'
            raw = path.join('src', raw)
            wav = file_num + file_name + '.wav'
            wav = path.join('wav', wav)
            with BytesIO() as f:
                for audio_content in synthesize(line["Текст"], 1.0):
                    f.write(audio_content)
                f.seek(0)
                pcmdata = f.read()
            with wave.open(wav, 'wb') as wavfile:
                wavfile.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
                wavfile.writeframes(pcmdata)
    return None


def synthesize(text, voice='jane', emotion='evil', spd=1.0):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + IAM_TOKEN,
    }

    data = {
        'text': text,
        'lang': 'ru-RU',
        'folderId': FOLDER_ID,
        'voice': voice,
        'emotion': emotion,
        'speed': spd,
        'format': 'lpcm',
        'sampleRateHertz': 48000,
    }

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError('Invalid response received: code: %d, message:'
                               ' %s' % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


if __name__ == "__main__":
    data()
