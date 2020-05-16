import requests
import httplib2
import apiclient.discovery
import json

from oauth2client.service_account import ServiceAccountCredentials
from os import path
from io import BytesIO
import wave

from common.settings import IAM_TOKEN, FOLDER_ID, SHEETS_ID, DEFAULT_RANGE


def get_write_data_from_google(action='read', data=None, w_range=''):
    CREDENTIALS_FILE = 'common/creds.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
         ]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

    if action == 'read':
        spreadsheet_data = service.spreadsheets().values().get(
            spreadsheetId=SHEETS_ID,
            range=DEFAULT_RANGE,
            majorDimension='ROWS'
        ).execute()
        SPREADSHEAT_HEADER = spreadsheet_data["values"][0]
        spam = list(map(lambda i: dict(zip(SPREADSHEAT_HEADER, i)),
                        spreadsheet_data["values"][1:]))
        return spam
    else:
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                 "range": w_range,
                 "majorDimension": "COLUMNS",
                 "values": data
                },
                ]
        }
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEETS_ID,
            body=body
        ).execute()
        print('Перевод записан')
        return None


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
                with BytesIO() as f:
                    for audio_content in synthesize(line['Voice_' + t_lang],
                                                    t_lang,
                                                    spd=1.0):
                        f.write(audio_content)
                    f.seek(0)
                    pcmdata = f.read()
                with wave.open(wav, 'wb') as wavfile:
                    wavfile.setparams((
                        1,
                        2,
                        48000,
                        0,
                        'NONE',
                        'not compressed'))
                    wavfile.writeframes(pcmdata)
                    print(file_name)
        except KeyError:
            continue
    return None


def synthesize(text, lang, spd=1.0):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + IAM_TOKEN,
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
        'Authorization': 'Bearer ' + IAM_TOKEN,
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

    write_data = list()
    temp_lst = list()
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
    w_range = "F2:F75" if what == 'trigger' else "M2:M76"
    get_write_data_from_google('write', data=write_data, w_range=w_range)

    return None


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


if __name__ == "__main__":
    main()
