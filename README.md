### Скрипт для перевода и синтеза речевых сообщений с использованием Yandex.Cloud

Переводенные и озвученные сообщения используются в тренировочной мисси симулятора DCS UH-1H.<br>
<br>
Для запуска необходимо установить зависимости из файла requirements.txt<br>
pip3 install -r requirements.txt<br>
<br>
Необходимо установить [интерфейс командной строки Yandex.Cloud](https://cloud.yandex.ru/docs/cli/quickstart#install)<br>
Токен получается и обновляется автоматически.<br>
<br>
Подготовить файл с исходными данными texts.csv и разместить его в директории src.<br>
Столбцы в файле и их описание:<br>
Number - номер по порядку<br>
\# - номер голосового сообщения<br>
Trigger - необязательное поле<br>
New Trigger - имя триггера в редакторе миссий DCS для перевода<br>
trigger_translate - маркер для перевода, любой символ<br>
Default Trigger - переведенное имя триггера<br>
Text_ru - текст русского сообщения<br>
Voice_ru - текст для озвучки сообщения<br>
ru_to_voice - маркер для озвучки сообщения, любой символ<br>
sec. - длительность аудио файла<br>
Text_2_en - текст сообщения для перевода на английский язык<br>
text_translate - маркер для перевода сообщения, любой символ<br>
Text_en - переведённый текст сообщения<br>
Voice_en - английский текст для создания озвучки<br>
en_to_voice - маркер для озвучки сообщения, может быть любой символ.<br>
<br>
Для русской озвучки используется голос jane.<br>
Для английской озвучки используется голос alyss.<br>
