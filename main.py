from text_to_speech_csv import MessagesForMission

action = input('Взять данные из .csv?[y/n]: ')
if not action and (action != 'n' or action != 'т'):
    messages = MessagesForMission()
else:
    from text_to_speech_google import MessagesForMissionFromGoogle
    messages = MessagesForMissionFromGoogle()
messages.main
