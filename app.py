# app.py
import os
import json
from systemd import journal
import mariadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import itertools
from datetime import datetime

import pymorphy3
import spacy
import nltk
from nltk.corpus import stopwords
import re


dir = os.path.dirname(__file__)
USER = os.environ['USER']
PASSWORD = os.environ['PASSWORD']
HOST = os.environ['HOST']
DATABASE = os.environ['DATABASE']

morph = pymorphy3.MorphAnalyzer()
nlp = spacy.load('en_core_web_sm')
#stopwords.words('russian')
stopwords_ru = stopwords.words('russian')


try:
    conn = mariadb.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        database=DATABASE

    )
    journal.write("Connected well")
except mariadb.Error as e:
    journal.write(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

cur = conn.cursor()

app = FastAPI()
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


journal.write("Init well")

async def get_word_occurrences(phrase):
    words = [w for w in re.split(r'[^а-яА-Яa-zA-zё\-\']+',phrase) if len(w)>0]
    journal.write(words)
    words_occurrences={}
    for w in words:
        wo = await get_lemma(w)
        cur.execute("select count(*) from routelebot_tokens where word=?",(wo,))
        words_occurrences[w]=cur.fetchone()[0]
    return words_occurrences


@app.get("/randomPhrase/en")
async def get_random_phrase_eng():
    journal.write("I am eng")
    cur.execute("select phrase, source_name, source_author, id from routelebot_quotes where lang='en' ORDER BY RAND() limit 1")
    phrase, source_name, source_author, id=cur.fetchone()
    journal.write(phrase)
    w = await get_words_by_id(id)
    
    return {'id': id, 'phrase': phrase, 'source_name': source_name , 'source_author' : source_author, 'words_occurrences': await get_word_occurrences(phrase), 'lemmas': w}

@app.get("/randomPhrase/ru")
async def get_random_phrase_ru():
    cur.execute("select phrase, source_name, source_author, id from routelebot_quotes where lang='ru' ORDER BY RAND() limit 1")
    phrase, source_name, source_author, id=cur.fetchone()
    w = await get_words_by_id(id)
    return {'id': id, 'phrase': phrase, 'source_name': source_name , 'source_author' : source_author, 'words_occurrences': await get_word_occurrences(phrase), 'lemmas': w}

@app.get("/randomWords/{lang}")
async def get_random_words(lang):
    cur.execute("select word from routelebot_tokens where lang=? ORDER BY RAND() limit 3",(lang,))
    return [i[0] for i in cur.fetchall()]



@app.get("/phraseIds/{word}")
async def get_phrases_by_word(word): # 10 or less
    w = await get_lemma(word)
    try:
        cur.execute("select distinct phrase_id from routelebot_tokens where word=?  ORDER BY RAND() LIMIT 10",(w,))
        return [i[0] for i in cur.fetchall()]
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}") 
        return

@app.get("/phrase/{id}")
async def get_phrase_by_id(id):
    cur.execute("select phrase, source_name, source_author from routelebot_quotes  where id=? limit 1",(id,))
    phrase, source_name, source_author=cur.fetchone()
    w = await get_words_by_id(id)
    #return json.dumps({'phrase': phrase, 'source_name': source_name , 'source_author' : source_author}, ensure_ascii=False).encode('utf8')
    return {'id':id, 'phrase': phrase, 'source_name': source_name , 'source_author' : source_author, 'words_occurrences': await get_word_occurrences(phrase),'lemmas': w}

@app.get("/phraseWords/{id}")
async def get_words_by_id(id):
    cur.execute("select word from routelebot_tokens where phrase_id=?",(id,))
    return [i[0] for i in cur.fetchall()]
    

@app.get("/lemma/{word}")
async def get_lemma(word):
    w = re.sub(r"[^а-яА-Яa-zA-Zё\-']", ' ', word)
    w = re.sub(r" +", ' ', w)
    lang=""
    if (len(re.findall("[а-яА-Я]", word))>0):
        lang = "ru"
    else:
        lang = "en"
    if (word == 'badly'):
        word='bad'
    if (lang == 'ru'):
        p = morph.parse(word)[0]
        if (p.normal_form == 'спасть'): 
            return 'спать'
        return p.normal_form
    if (lang == 'en'):
        doc = nlp(word)
        return [token.lemma_ for token in doc][0]

@app.get("/possibleGoals/{startWord}/{depth}")
async def get_possible_goals(startWord,depth : int):
    journal.write("I am {} deep".format(depth))
    startWord=await get_lemma(startWord)
    cur.execute("select phrase_id from routelebot_tokens where word=?",(startWord,))
    ids=["'"+str(i[0])+"'" for i in cur.fetchall()]
    if (len(ids) == 0):
        return []
    journal.write("select distinct word from routelebot_tokens where phrase_id in ({})".format(",".join( map(str, ids) )))
    cur.execute("select distinct word from routelebot_tokens where phrase_id in ({}) ORDER BY RAND() limit 10".format(",".join( map(str, ids) )))
    neighbors=[i[0] for i in cur.fetchall()]
    if (depth == 0):
        return neighbors
    else:
        res=[]
        for i in neighbors:
            res.extend(await get_possible_goals(i, depth-1))
            
        return list(set(res))


class Item(BaseModel):
    chat_id: int
    name: str
    alias: str
        

@app.post("/logUser/")
async def log_user(item: Item):
    try:
        
        cur.execute(
    "INSERT INTO routelebot_users (id, name, last_visited, alias) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE last_visited=?", 
    (item.chat_id, item.name, datetime.now(), item.alias, datetime.now()) )
        conn.commit()
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}")