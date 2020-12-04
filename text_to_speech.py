"""Synthesize voice message for mission in DCS."""
import csv
from time import time
from io import BytesIO
import json
from os import path, system

import requests
import wave

from common.settings import FOLDER_ID

token_file = path.join('common', 'token')
texts = path.join('src/texts.csv')


class MessagesForMission(object):
    """Main class for translate and synthesize messages."""
    def __init__(self):
        self.translate_url = (
            'https://translate.api.cloud.yandex.net/translate/v2/translate'
            )
        self.synthesize_url = (
            'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
            )
        self.good_response_code = 200

    def get_data(self):
        """Get data from .csv file."""
        row_list = []
        with open(texts, 'r') as read_f:
            for line in csv.DictReader(read_f, delimiter=','):
                row_list.append(line)
        return row_list

    def create_audio_messages(self, params):
        """
        Write wave file.
        Args:
        text - text for synthesize
        wav - filename
        """
        for line in self.get_data():
            if line[params['trigger']]:
                with BytesIO() as raw_data:
                    for audio_content in self.synthesize(
                        line['Voice_ru'], params['lang'], params['voice']
                    ):
                        raw_data.write(audio_content)
                    raw_data.seek(0)
                    pcmdata = raw_data.read()
                try:
                    path.getmtime('wav')
                except FileNotFoundError:
                    system('mkdir wav')
                with wave.open(create_file_name(line), 'wb') as wavfile:
                    wavfile.setparams(
                        (1, 2, 48000, 0, 'NONE', 'not compressed'),
                    )
                    wavfile.writeframes(pcmdata)

    def synthesize(self, text, lang, voice, emotion='evil', spd=1.0):
        """Synthesize voice message.
        Raises:
        RuntimeError
        """
        with requests.post(
            url=self.synthesize_url,
            headers={
                'Authorization': 'Bearer {0}'.format(get_token()),
            },
            data={
                'text': text,
                'lang': lang,
                'folderId': FOLDER_ID,
                'voice': voice,
                'emotion': emotion,
                'speed': spd,
                'format': 'lpcm',
                'sampleRateHertz': 48000,
            },
            stream=True,
        ) as response:
            if response.status_code != self.good_response_code:
                raise RuntimeError(
                    'Invalid response received: code: {0}, message: {1}'.
                    format(response.status_code, response.text),
                )
            for chunk in response.iter_content(chunk_size=None):
                yield chunk

    def translate(self, what):
        """Translate messages to english.
        Raises:
        RuntimeError
        """
        translated = {}
        translated_texts = []
        sheet = self.get_data()
        task = what + '_translate'
        what_read = 'New Trigger' if what == 'trigger' else 'Text_2_en'
        what_write = 'Default Trigger' if what == 'trigger' else 'Text_en'
        for row in sheet:
            try:
                row.get(task)
            except KeyError:
                continue
            else:
                translated_texts.append('{0}.{1}'.format(
                    row['Number'], row[what_read],
                ),
                )
        json_data = json.dumps(
            {
                # Change "" to ''
                'sourceLanguageCode': 'ru',
                'targetLanguageCode': 'en',
                'texts': translated_texts,
                'folderId': FOLDER_ID,
            },
        )
        with requests.post(
            url=self.translate_url,
            headers={
                'Authorization': 'Bearer {0}'.format(get_token()),
                'Content-Type': 'application/json',
            },
            data=json_data,
        ) as response:
            if response.status_code != self.good_response_code:
                raise RuntimeError(
                    'Invalid response received: code: {0}, message: {1}'.
                    format(response.status_code, response.text),
                )
            eggs = json.loads(response.text)
            for spam in eggs['translations']:
                spam = spam['text']
                spam_num = spam[:spam.find('.')]
                translated[spam_num] = spam[len(spam_num) + 1:]
        write_data = []
        temp_lst = []
        for row in sheet:
            try:
                if row[task]:
                    row[what_write] = translated[row["Number"]]
            except Exception:
                row[what_write] = '-'
                continue
            finally:
                temp_lst.append(row[what_write])
        write_data.append(temp_lst)
        w_range = "F2:F107" if what == 'trigger' else "M2:M107"
        get_write_data_from_google('write', data=write_data, w_range=w_range)

    @property
    def main(self):
        """Menu for actions."""
        audio_params = {
            'en': {
                'lang': 'en-US',
                'trigger': 'en_to_voice',
                'text': 'Voice_en',
                'voice': 'alyss',
                },
            'ru': {
                'lang': 'ru-RU',
                'trigger': 'ru_to_voice',
                'text': 'Voice_ru',
                'voice': 'jane',
            },
        }
        while True:
            print(
                '1. Перевести триггеры', '2. Перевести сообщения',
                '3. Сделать русскую озвучку',
                '4. Сделать английскую озвучку', 'q. Выйти', sep='\n',
                  )
            action = input('Выбери действие: ').lower()
            if action == 'q' or action == 'й':
                break
            try:
                action = int(action)
            except ValueError:
                print('Неверное значение, попробуй ещё раз')
                continue
            if action == 1:
                self.get_data()
            elif action == 2:
                self.get_data()
            elif action == 3:
                self.create_audio_messages(audio_params['ru'])
            elif action == 4:
                self.create_audio_messages(audio_params['en'])


def get_token():
    """Return new token for access yandex cloud.
    return:
    iam token
    """
    live_hours = 11
    seconds_in_hour = 3600
    try:
        token_modify_time = path.getmtime(token_file)
    except FileNotFoundError:
        system('yc iam create-token > {0}'.format(token_file))
    else:
        difference_time = (
            time() - token_modify_time
        ) // seconds_in_hour
        if difference_time > live_hours:
            system('yc iam create-token > {0}'.format(token_file))
    with open(path.join('common', 'token')) as token:
        return token.read().rstrip()


def create_file_name(line):
    """Create file name for wav.
    returns
    string
    """
    if len(line['#']) > 1:
        file_num = line['#']
    else:
        file_num = '0{0}'.format(line['#'])
    file_name = '{0}'.format(line['New Trigger'].split('.')[0])
    file_name = '{0}-{1}{2}'.format(file_num, file_name, '.wav')
    return path.join('wav', file_name)


if __name__ == '__main__':
    messages = MessagesForMission()
    messages.main
