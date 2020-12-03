"""Synthesize voice message for mission in DCS."""
import csv
from datetime import datetime
from io import BytesIO
from os import path, system

import requests
import wave

from common.settings import FOLDER_ID

token_file = path.join('common', 'token')


class MessagesForMission(object):
    """Main class for translate and synthesize messages."""
    def get_data(self):
        """Get data from .csv file."""
        with open('src/texts2.csv', 'r') as read_f:
            for line in csv.DictReader(read_f, delimiter=','):
                if line['ru_to_voice']:
                    wav_name = path.join(
                        'wav',
                        create_file_name(line)
                        )
                    self.write_file(line['Voice_ru'], wav_name)


    def write_file(self, text, wav):
        """
        Write wave file.
        Args:
        text - text for synthesize
        wav - filename
        """
        with BytesIO() as raw_data:
            for audio_content in self.synthesize(text):
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

    def synthesize(self, text, voice='jane', emotion='evil', spd=1.0):
        """Synthesize voice message.
        Raises:
        RuntimeError
        """
        good_response_code = 200
        with requests.post(
            url='https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
            headers={
                'Authorization': 'Bearer {0}'.format(get_token()),
            },
            data={
                'text': text,
                'lang': 'ru-RU',
                'folderId': FOLDER_ID,
                'voice': voice,
                'emotion': emotion,
                'speed': spd,
                'format': 'lpcm',
                'sampleRateHertz': 48000,
            },
            stream=True,
        ) as response:
            if response.status_code != good_response_code:
                raise RuntimeError(
                    'Invalid response received: code: {0}, message: {1}'.
                    format(response.status_code, response.text),
                )
            for chunk in response.iter_content(chunk_size=None):
                yield chunk

    @property
    def main(self):
        """Menu for actions."""
        while True:
            print('1. Перевести триггеры',
                  '2. Перевести сообщения', '3. Сделать русскую озвучку',
                  '4. Сделать английскую озвучку', 'q. Выйти', sep='\n'
                  )
            action = input('Выбери действие: ').lower()
            if action == 'q' or action == 'й':
                break
            try:
                action = int(action)
            except Exception:
                print('Неверное значение, попробуй ещё раз')
                continue
            if action == 1:
                self.get_data()
            elif action == 2:
                self.get_data()
            elif action == 3:
                self.get_data()
            elif action == 4:
                self.get_data()
            else:
                continue


def get_token():
    """Return new token for access yandex cloud.
    return:
    iam token
    """
    live_hours = 10
    seconds_in_hour = 3600
    try:
        token_modify_time = path.getmtime(token_file)
    except FileNotFoundError:
        system('yc iam create-token > {0}'.format(token_file))
    else:
        difference_time = (
            datetime.now() - datetime.fromtimestamp(token_modify_time)
        ).seconds // seconds_in_hour
        if difference_time > live_hours:
            system('yc iam create-token > {0}'.format(token_file))
    with open(path.join('common', 'token')) as token:
        return token.read().rstrip()


def create_file_name(line):
    if len(line['#']) > 1:
        file_num = line['#']
    else:
        file_num = '0{0}'.format(line['#'])
    file_name = '{0}'.format(line['New Trigger'].split('.')[0])
    return '{0}-{1}{2}'.format(file_num, file_name, '.wav')


if __name__ == '__main__':
    messages = MessagesForMission()
    messages.main
