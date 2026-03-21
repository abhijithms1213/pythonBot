from telegram import ForceReply, Update
import re
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


def msg_process(msg_date, update: Update):
    msg = update.message.text
    print(msg)
    split_msgs = msg.split()
    print(f'split msg {split_msgs}')
    pattern = r'https?://\S+|www\.\S+'
    deadlines = ['', '']
    necessary_keywords = []

    for word in split_msgs:
        print(f'word; {word}')
        if re.findall(pattern, word):
            print('under pattern find')
            necessary_keywords.append(word)
        lower_case: str = word.lower()
        # if '24d' or '17d' or '14d' or '24' or '17' or '14' in lower_case:
        if '24d' in lower_case:
            print('under date find')
            necessary_keywords.append(word)
        # if any (lower_case in deadlines for word in split_msgs ):

    print(f'full list i got: {necessary_keywords}')