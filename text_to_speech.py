import requests
import httplib2
import apiclient.discovery

from oauth2client.service_account import ServiceAccountCredentials
from os import path
from io import BytesIO
import wave

from common.settings import IAM_TOKEN, FOLDER_ID, SHEETS_ID, RANGE


def get_data_from_google():
    CREDENTIALS_FILE = 'common/creds.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
         ]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

    spreadsheet_data = service.spreadsheets().values().get(
        spreadsheetId=SHEETS_ID,
        range=RANGE,
        majorDimension='ROWS'
    ).execute()
    SPREADSHEAT_HEADER = spreadsheet_data["values"][0]
    spam = list(map(lambda i: dict(zip(SPREADSHEAT_HEADER, i)),
                    spreadsheet_data["values"][1:]))
    return spam


def data_for_voice(t_lang):
    for line in get_data_from_google():
        file_num = line["#"] if len(line["#"]) > 1 \
            else '0' + line["#"]
        file_name = '-' + line["Trigger"].replace(' ', '-')
        raw = file_num + file_name + '.raw'
        raw = path.join('src', raw)
        wav = file_num + file_name + '.wav'
        wav = path.join('wav', wav)
        if line["#"] and line[t_lang + '_to_voice']:
            with BytesIO() as f:
                for audio_content in synthesize(line['Voice_' + t_lang],
                                                spd=1.0):
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
        if action == 1:
            data_for_voice('ru')
        elif action == 2:
            pass
        elif action == 3:
            break
        elif action == 4:
            data_for_voice('en')
        elif action == 'q' or 'Q':
            break
        else:
            print('Введён неверный номер')


if __name__ == "__main__":
    main()
