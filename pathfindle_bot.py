import random
import os
import telebot
from systemd import journal
import mariadb
from datetime import datetime
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton



dir = os.path.dirname(__file__)
TOKEN = os.environ['P_TOKEN']
bot = telebot.TeleBot(TOKEN)

variables = {}

try:
    conn = mariadb.connect(
        user="wordlerbot",
        password="i4mp455w0rd_",
        host="localhost",
        database="bot_db"

    )
    journal.write(f"Connected well")
except mariadb.Error as e:
    journal.write(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Get Cursor
cur = conn.cursor()


def send_help(chat_id):
    bot.send_message(chat_id,'Help does not exist here yet')

def set_keyboard(buttons_list, need_prev=0, need_next=0):
    w=(len(buttons_list) // 3) + 1
    buttons = [telebot.types.KeyboardButton(i) for i in buttons_list]
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=w, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    
    menu=[]
    if (need_prev):
        menu.append(telebot.types.KeyboardButton('<-'))
    if (need_next):
        menu.append(telebot.types.KeyboardButton('->'))
    keyboard.add(*menu)
    return keyboard

def get_phrases_by_word(word): # 10 or less
    try:
        cur.execute("select distinct phrase_id from routelebot_tokens where word=?  ORDER BY RAND() LIMIT 10",(word,))
        return [i[0] for i in cur.fetchall()]
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}") 
        return


def present_phrase(chat_id, phrase_id):
    try:
        cur.execute("select phrase, source_name, source_author from routelebot_quotes where id=?",(phrase_id,))
        phrase, source_name, source_author=cur.fetchone()
        
        cur.execute("select word from routelebot_tokens where phrase_id=?",(phrase_id,))
        wordlist=[i[0] for i in cur.fetchall()]
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}") 

    variables[chat_id]['variants'] = [*wordlist]
    last_flg=1 if variables[chat_id]['pointer']>0 else 0
    next_flg=1 if variables[chat_id]['pointer']<len(variables[chat_id]['phrases'])-1 else 0
    if (last_flg):
        variables[chat_id]['variants'].append('<-')
        
    if (next_flg):
        variables[chat_id]['variants'].append('->')
        

    msg=bot.send_message(chat_id, f"{phrase}\n{source_name}, {source_author}", reply_markup=set_keyboard(wordlist, last_flg, next_flg))
    bot.register_next_step_handler(msg, phrase_navigator)

    #here go write phrase n construct menu out of words, next phrase, prev??

# handlers


@bot.message_handler(commands=['help'])
def helper(message):
    send_help(message.chat.id)

@bot.message_handler(commands=['start', 'go'])

def start_handler(message):
    chat_id = message.chat.id
    name=' '.join(filter(None, (message.chat.first_name, message.chat.last_name)))
    try:
        
        cur.execute(
    "INSERT INTO routelebot_users (id, name, last_visited, alias) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE last_visited=?", 
    (chat_id, name, datetime.now(), message.chat.username, datetime.now()) )
        conn.commit()
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}")

    variables[chat_id] = {}
    # variables[chat_id]['mode']=mode
    variables[chat_id]['path'] = []
    #variables[chat_id][path]: [word1, word2 ...], when path[len-1]=tgt_word -> win
    variables[chat_id]['phrases'] = []
    # variables[chat_id][phrases] [path[len(path)-1]]: [ph1_id, ph2_id]
    variables[chat_id]['pointer'] = 0
    # variables[chat_id][pointer]: which phrase
    variables[chat_id]['variants'] = []

    
    lng = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    lng_btn1 = telebot.types.KeyboardButton('ENG')
    lng_btn2 = telebot.types.KeyboardButton('RUS')
    lng.add(lng_btn1, lng_btn2)
    msg = bot.send_message(chat_id, 'Выберите язык | Choose your language', reply_markup=lng)

    bot.register_next_step_handler(msg, askLang)

def askLang(message):
    chat_id = message.chat.id
    text = message.text
    if (text is None or text not in ['ENG', 'RUS']):
        msg=bot.send_message(chat_id, 'Input must be correct!')
        bot.register_next_step_handler(msg, askLang)
    if (message.text == '/help'):
        send_help(chat_id)
    variables[chat_id]['mode'] = 'ru' if text == 'RUS' else 'en'
    #daily or non-daily will be here, if ever

    #get id
    try:
        cur.execute('select game_id, start_words, target_word from routelebot_games where lang=? ORDER BY RAND() LIMIT 1', (variables[chat_id]['mode'],))
        variables[chat_id]['g_id'], variables[chat_id]['start_words'], variables[chat_id]['target_word'] = cur.fetchone()
        variables[chat_id]['variants'] = variables[chat_id]['start_words'].split(', ')
    except mariadb.Error as e:
        journal.write(f"Error in db: {e}")


    
    msg = bot.send_message(chat_id, f'Your goal is to reach "%s", choose your start:' % variables[chat_id]['target_word'] if variables[chat_id]['mode'] == 'en' else f'Ваша цель — получить слово "%s", выберите слово для старта:' % variables[chat_id]['target_word'], reply_markup=set_keyboard(variables[chat_id]['start_words'].split(', ')))
    
    bot.register_next_step_handler(msg, set_phrases)

def set_phrases(message):
    chat_id = message.chat.id
    if (message.text == '/help'):
        send_help(chat_id)
        return
    if (message.text is None or message.text not in variables[chat_id]['variants']):
        msg = bot.send_message(chat_id, f'Input should not be arbitrary, input is {message.text}' if variables[chat_id]['mode'] == 'en' else f'Вы ввели что-то недопустимое')
        bot.register_next_step_handler(msg, phrase_navigator)
        return 
    variables[chat_id]['path'].append(message.text)
    variables[chat_id]['pointer'] = 0
    variables[chat_id]['phrases'] = get_phrases_by_word(message.text)

    present_phrase(chat_id,variables[chat_id]['phrases'][variables[chat_id]['pointer']])

    
    
def phrase_navigator (message):
    chat_id=message.chat.id
    if (message.text == '/help'):
        send_help(chat_id)
        return
    
    if (message.text == '<-'):
        variables[chat_id]['pointer'] = variables[chat_id]['pointer'] - 1
        present_phrase(chat_id,variables[chat_id]['phrases'][variables[chat_id]['pointer']])
        return
    if (message.text == '->'):
        variables[chat_id]['pointer'] = variables[chat_id]['pointer'] + 1
        present_phrase(chat_id,variables[chat_id]['phrases'][variables[chat_id]['pointer']])
        return

    if (message.text == variables[chat_id]['target_word']):
        variables[chat_id]['path'].append(message.text)
        bot.send_message(chat_id, f"You won. Your path was: {variables[chat_id]['path']}\n Send /start to play again." if variables[chat_id]['mode'] == 'en' else f"Вы выиграли! Ваш путь: {variables[chat_id]['path']}\n Нажмите /start, чтобы сыграть еще раз!")
        return

    else:
        set_phrases(message)



bot.polling(none_stop=True)