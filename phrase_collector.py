import random
import os
import telebot
from systemd import journal
import mariadb
from datetime import datetime
import pymorphy3
import spacy
import nltk
from nltk.corpus import stopwords
import re
import sys


morph = pymorphy3.MorphAnalyzer()
nlp = spacy.load('en_core_web_sm')
stopwords.words('russian')
stopwords_ru = stopwords.words('russian')

try:
    conn = mariadb.connect(
        user="wordlerbot",
        password="i4mp455w0rd_",
        host="localhost",
        database="bot_db"

    )
    print(f"Connected well")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

cur = conn.cursor()

def lemmatize(text, lng):
    text = re.sub(r"[^а-яА-Яa-zA-Zё\-']", ' ', text)
    text = re.sub(r" +", ' ', text)
    if (lng == 'ru'):
        words = text.split() # разбиваем текст на слова
        res = list()
        for word in words:
            p = morph.parse(word)[0]
            res.append(p.normal_form)
        print(list(dict.fromkeys([i for i in res if i not in stopwords_ru])))
        return list(dict.fromkeys([i for i in res if i not in stopwords_ru]))
    if (lng == 'en'):
        doc = nlp(text)
        lemmatized_tokens = [token.lemma_ for token in doc if token.lemma_.lower() not in nlp.Defaults.stop_words and token.lemma_.lower() != ' ']
        print(list(dict.fromkeys(lemmatized_tokens)))
        return list(dict.fromkeys(lemmatized_tokens))

def insert_phrase(phrase, source_name, source_author, lang):
    id = ''
    try:
        cur.execute("select nextval(bot_db.phrase_ids) from dual")
        id=cur.fetchone()[0]
        print(f'id is {id}')
    except mariadb.Error as e:
        print(f"Error in seq: {e}")
    try:
        cur.execute(
    "INSERT INTO bot_db.routelebot_quotes (id, lang, added_dttm, phrase, source_name, source_author) VALUES (?, ?, sysdate(), ?, ?, ?)", 
    (id, lang, phrase, source_name, source_author) )
        conn.commit()
    except mariadb.Error as e:
        print(f"Error in db q: {e}")

    for i in lemmatize(phrase, lang):
        try:
            cur.execute("INSERT INTO bot_db.routelebot_tokens (phrase_id, word) VALUES (?, ?)", (id, i) )
            conn.commit()
        except mariadb.Error as e:
            print(f"Error in db r: {e}")

insert_phrase(phrase=sys.argv[1], source_name=sys.argv[2], source_author=sys.argv[3], lang=sys.argv[4])
