"""Synthesize voice message for mission in DCS."""
import csv
from time import time
from io import BytesIO
import json
from os import path, system

import requests
import wave

from common.settings import FOLDER_ID

texts = path.join('src/texts.csv')


class MessagesForMission(object):
    """Main class for translate and synthesize messages."""

    def __init__(self):
        """Init variables for translate text and synthesize sounds."""
        self._translate_url = (
            'https://translate.api.cloud.yandex.net/translate/v2/translate'
            )
        self._synthesize_url = (
            'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
            )
        self._good_response_code = 200
        self.what_read = ''
        self.what_write = ''
        self.translated = {}
        self.task = ''
        self.text_to_translate = []
        self.text_wo_translate = []
        self._audio_params = {
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


    def get_data(self):
        """Get data from .csv file."""
        row_list = []
        with open(texts, 'r') as read_f:
            for line in csv.DictReader(read_f, delimiter=','):
                row_list.append(line)
        return row_list

    def create_audio_messages(self, language):
        """
        Write wave file.
        Args:
        language for audio parameters
        """
        for line in self.get_data():
            if line[self._audio_params[language]['trigger']]:
                text = line[self._audio_params[language]['text']]
                with BytesIO() as raw_data:
                    for audio_content in self.synth_wave(text, language):
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
        print('Озвучка завершена')

    def synth_wave(self, text, language, emotion='evil', spd=1.0):
        """Synthesize voice message.
        Raises:
        RuntimeError
        """
        with requests.post(
            url=self._synthesize_url,
            headers={
                'Authorization': 'Bearer {0}'.format(get_token()),
            },
            data={
                'text': text,
                'lang': self._audio_params[language]['lang'],
                'folderId': FOLDER_ID,
                'voice': self._audio_params[language]['voice'],
                'emotion': emotion,
                'speed': spd if language != 'en' else 1.2,
                'format': 'lpcm',
                'sampleRateHertz': 48000,
            },
            stream=True,
        ) as response:
            if response.status_code != self._good_response_code:
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
        # FIX: Translate texts not working
        self.task = '{0}_translate'.format(what)
        self.what_read = 'New Trigger' if what == 'trigger' else 'Text_2_en'
        self.what_write = 'Default Trigger' if what == 'trigger' else 'Text_en'
        for row in self.get_data():
            if row[self.task]:
                self.text_to_translate.append('{0}.{1}'.format(
                    row['Number'], row[self.what_read],
                ),
                )
            else:
                self.text_wo_translate.append(row)
        json_data = json.dumps(
            {
                'sourceLanguageCode': 'ru',
                'targetLanguageCode': 'en',
                'texts': self.text_to_translate,
                'folderId': FOLDER_ID,
            },
        )
        with requests.post(
            url=self._translate_url,
            headers={
                'Authorization': 'Bearer {0}'.format(get_token()),
                'Content-Type': 'application/json',
            },
            data=json_data,
        ) as response:
            if response.status_code != self._good_response_code:
                raise RuntimeError(
                    'Invalid response received: code: {0}, message: {1}'.
                    format(response.status_code, response.text),
                )
            eggs = json.loads(response.text)
            for spam in eggs['translations']:
                spam = spam['text']
                spam_num = spam[:spam.find('.')]
                self.translated[spam_num] = spam[len(spam_num) + 1:].lstrip()
        self.write_translated_text()

    def write_translated_text(self):
        """Write translated triggers and messages to a sheet."""
        for new_row in self.get_data():
            if new_row[self.task]:
                new_row[self.what_write] = self.translated[new_row['Number']]
            else:
                new_row[self.what_write] = '-'
                continue
            self.text_wo_translate.append(new_row)
        with open(texts, 'w') as write_file:
            writer = csv.DictWriter(
                write_file,
                delimiter=',',
                fieldnames=self.text_wo_translate[0].keys(),
            )
            writer.writeheader()
            for row in self.text_wo_translate:
                writer.writerow(row)
        print('Перевод завершён')

    @property
    def main(self):
        """Menu for actions."""
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
                self.translate('trigger')
            elif action == 2:
                self.translate('text')
            elif action == 3:
                self.create_audio_messages('ru')
            elif action == 4:
                self.create_audio_messages('en')


def get_token():
    """Return new token for access yandex cloud.
    return:
    iam token
    """
    live_hours = 11
    seconds_in_hour = 3600
    try:
        token_modify_time = path.getmtime(
            path.join('common', 'token'),
            )
    except FileNotFoundError:
        system('yc iam create-token > {0}'.format(
            path.join('common', 'token'),
        ),
        )
    else:
        difference_time = (
            time() - token_modify_time
        ) // seconds_in_hour
        if difference_time > live_hours:
            system('yc iam create-token > {0}'.format(
                path.join('common', 'token'),
            ),
            )
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
