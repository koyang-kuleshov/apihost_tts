import requests
import csv
from os import system, path

from settings import IAM_TOKEN, FOLDER_ID


def data():
    with open('src/texts.csv', "r") as read_f:
        reader = csv.DictReader(read_f, delimiter=',')
        for line in reader:
            file_num = line["Номер"] if len(line["Номер"]) > 1 \
                else '0' + line["Номер"]
            file_name = '-' + line["Триггер"].replace(' ', '-')
            raw = file_num + file_name + '.raw'
            raw = path.join('src', raw)
            wav = file_num + file_name + '.wav'
            wav = path.join('wav', wav)
            with open(raw, 'wb') as f:
                for audio_content in synthesize(line["Текст"]):
                    f.write(audio_content)
            system(f'sox -r 48000 -b 16 -e signed-integer -c 1 {raw} \
                   {wav}')
            system(f'rm {raw}')
    return None


def synthesize(text):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + IAM_TOKEN,
    }

    data = {
        'text': text,
        'lang': 'ru-RU',
        'folderId': FOLDER_ID,
        'emotion': 'evil',
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
