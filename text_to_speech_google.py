"""Synthesize voice message for mission in DCS."""
import csv
from time import time
from io import BytesIO
import json
from os import path, system

import requests
import wave

from text_to_speech_csv import MessagesForMission
from common.settings import FOLDER_ID

texts = path.join('src/texts.csv')


class MessagesForMissionFromGoogle(MessagesForMission):
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

    def translate(self, what):
        """Translate messages to english.
        Raises:
        RuntimeError
        """
        translated = {}
        translated_texts = []
        sheet = self.get_data()
        task = '{0}_translate'.format(what)
        what_read = 'New Trigger' if what == 'trigger' else 'Text_2_en'
        what_write = 'Default Trigger' if what == 'trigger' else 'Text_en'
        for row in sheet:
            # TODO: Read file row by row and translate if trigger is on
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
                self.translate('triggers')
            elif action == 2:
                self.translate('text')
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

def old_functions():
    def get_write_data_from_google(action='read', data=None, w_range=''):
        credentials_file = 'common/creds.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file,
            ['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
            ]
        )
        httpauth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpauth)

        if action == 'read':
            spreadsheet_data = service.spreadsheets().values().get(
                spreadsheetId=SHEETS_ID,
                range=DEFAULT_RANGE,
                majorDimension='ROWS',
            ).execute()
            spreadsheat_header = spreadsheet_data['values'][0]
            return list(map(
                lambda elem: dict(zip(spreadsheat_header, elem)),
                spreadsheet_data['values'][1:],  # added comma
                ),  # added comma
                )
        else:
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                    "range": w_range,
                    "majorDimension": "COLUMNS",
                    "values": data
                    },
                    ],
            }
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SHEETS_ID,
                body=body
            ).execute()
            print('Перевод записан')

    def data_for_voice(t_lang):
        for line in get_write_data_from_google():
            try:
                if line["#"] and line[t_lang + '_to_voice']:
                    file_num = line["#"] if len(line["#"]) > 1 \
                        else '0' + line["#"]
                    file_name = file_num + '-' + line["Default Trigger"].\
                        replace(' ', '-').replace('.', '').replace('/', '-')
                    wav = file_name + '.wav'
                    wav = path.join('wav', t_lang, wav)
                    with BytesIO() as audio_file:
                        raw_audio = synthesize(
                            line['Voice_{0}'.format(t_lang)],
                            t_lang,
                            spd=1.0,  # added comma
                        )
                        for audio_content in raw_audio:
                            audio_file.write(audio_content)
                        f.seek(0)
                        pcmdata = f.read()
                    with wave.open(wav, 'wb') as wavfile:
                        wavfile.setparams((
                            1,
                            2,
                            48000,
                            0,
                            'NONE',
                            'not compressed'
                        )
                        )
                        wavfile.writeframes(pcmdata)
                        print(file_name)
            except KeyError:
                continue
        return None


    def synthesize(text, lang, spd=1.0):
        url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        headers = {
            'Authorization': 'Bearer ' + YANDEX_TOKEN,
        }

        data = {
            'text': text,
            'lang': 'ru-RU' if lang == 'ru' else 'en-US',
            'folderId': FOLDER_ID,
            'voice': 'jane' if lang == 'ru' else 'alyss',
            'emotion': 'evil',
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


    def translate(what):
        url = 'https://translate.api.cloud.yandex.net/translate/v2/translate'
        headers = {
            'Authorization': 'Bearer ' + YANDEX_TOKEN,
            'Content-Type': 'application/json',
        }

        translated = dict()
        texts = list()
        sheet = get_write_data_from_google()
        task = what + '_translate'
        if what == 'trigger':
            what_read = "New Trigger"
            what_write = "Default Trigger"
        else:
            what_read = "Text_2_en"
            what_write = "Text_en"

        for row in sheet:
            try:
                if row[task]:
                    texts.append(row["Number"] + '.' + row[what_read])
            except KeyError:
                continue

        data = json.dumps({
            "sourceLanguageCode": "ru",
            "targetLanguageCode": "en",
            "texts": texts,
            "folderId": FOLDER_ID,
        })

        with requests.post(url, headers=headers, data=data) as resp:
            if resp.status_code != 200:
                raise RuntimeError('Invalid response received: code: %d, message:'
                                ' %s' % (resp.status_code, resp.text))
            eggs = json.loads(resp.text)
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


    def main():
        while True:
            print(
                '1. Сделать русскую озвучку\n'
                '2. Перевести триггеры на английский\n'
                '3. Перевести текст триггеров на английский\n'
                '4. Сделать английскую озвучку\n'
                'q. Выход'
            )
            action = input('Выполнить: ')
            if action == '1':
                data_for_voice('ru')
            elif action == '2':
                translate('trigger')
            elif action == '3':
                translate('text')
            elif action == '4':
                data_for_voice('en')
            elif action == ('q' or 'Q'):
                break
            else:
                print('Введён неверный номер')


if __name__ == '__main__':
    messages = MessagesForMission()
    messages.main
