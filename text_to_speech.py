"""Synthesize voice message for mission in DCS."""
import csv
from io import BytesIO
from os import path, system
from datetime import datetime

import requests
import wave

from common.settings import FOLDER_ID

token_file = path.join('common', 'token')


def get_data():
    """Get data from .csv file."""
    with open('src/texts2.csv', 'r') as read_f:
        for line in csv.DictReader(read_f, delimiter=','):
            if line['ru_to_voice']:
                if len(line['#']) > 1:
                    file_num = line['#']
                else:
                    file_num = '0{0}'.format(line['#'])
                file_name = '-{0}'.format(
                    line['New Trigger'].split('.')[0]
                )
                wav_name = path.join(
                    'wav',
                    '{0}{1}{2}'.format(file_num, file_name, '.wav'),
                )
                write_file(line['Voice_ru'], wav_name)


def write_file(text, wav):
    """
    Write wave file.
    Args:
    text - text for synthesize
    wav - filename
    """
    with BytesIO() as raw_data:
        for audio_content in synthesize(text):
            raw_data.write(audio_content)
        raw_data.seek(0)
        pcmdata = raw_data.read()
    try:
        path.getmtime('wav')
    except FileNotFoundError:
        system('mkdir wav')
    with wave.open(wav, 'wb') as wavfile:
        wavfile.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        wavfile.writeframes(pcmdata)


def synthesize(text, voice='jane', emotion='evil', spd=1.0):
    """Synthesize voice message.
    Raises:
    RuntimeError
    """
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer {0}'.format(get_token()),
    }
    head_data = {
        'text': text,
        'lang': 'ru-RU',
        'folderId': FOLDER_ID,
        'voice': voice,
        'emotion': emotion,
        'speed': spd,
        'format': 'lpcm',
        'sampleRateHertz': 48000,
    }
    with requests.post(
        url, headers=headers, data=head_data, stream=True,
    ) as resp:
        if resp.status_code != 200:
            raise RuntimeError(
                'Invalid response received: code: {0}, message: {1}'.
                format(resp.status_code, resp.text),
            )
        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


def get_token():
    """Return new token for access yandex cloud.
    return:
    iam token
    """
    try:
        token_modify_time = path.getmtime(token_file)
    except FileNotFoundError:
        system('yc iam create-token > {0}'.format(token_file))
    else:
        difference_time = (
            datetime.now() - datetime.fromtimestamp(token_modify_time)
        ).seconds // 3600
        if difference_time > 11:
            system('yc iam create-token > {0}'.format(token_file))
    with open(path.join('common', 'token')) as token:
        return token.read().rstrip()


if __name__ == '__main__':
    get_data()
