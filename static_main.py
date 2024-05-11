import requests
import random
import string
import time

import telebot
from telebot import types

import config

class UserData():
    def __init__(self, mail=''):
        self.mail = mail
    
API = config.API
TOKEN = config.TOKEN

domain_list = ["1secmail.com", "1secmail.org", "1secmail.net"]
domain = random.choice(domain_list)

bot = telebot.TeleBot(token=TOKEN, parse_mode='HTML')
user_data = UserData()

def main():
    start_button_text = "Generate mail 📨"

    @bot.message_handler(commands=['start'])
    def start_msg(msg):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton(start_button_text)

        markup.add(item)

        bot.send_message(msg.chat.id,
                               f"Hello, <b>{msg.from_user.full_name}</b>!👋\n\nMy name's <b>{bot.get_me().full_name}</b>. Need to create anonymous mail? No problem! With me, you can create a temporary email easily and simply! All notifications will come here and you can easily read them.",
                               reply_markup=markup)
    
    @bot.message_handler(content_types='text')
    def generate_mail_clicked(msg):
        if msg.text == start_button_text:
            username = generate_username()
            mail = f'{username}@{domain}'
            user_data.mail = mail

            mail_req = requests.get(f'{API}?login={username}&domain={domain}')

            btn = types.InlineKeyboardButton(text='Deactivate mail 🗑️', callback_data='deactivate_mail')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(btn)

            bot.send_message(msg.chat.id,
                             f'Your temporary mail adress: <code>{mail}</code>\n\n⚠️ This mail will be deactivated after 1 hour. All notifications will come here and you can easily read them.',
                             reply_markup=markup)
            
            check_mail(mail, msg.chat.id)

        else:
            try:
                login, _domain = user_data.mail.split('@')

                url = 'https://www.1secmail.com/mailbox'

                data = {
                    'action': 'deleteMailbox',
                    'login': login,
                    'domain': _domain
                }

                r = requests.post(url, data=data)
                print(f'[x] Mail {user_data.mail} has been deleted with {r.status_code} status!\n')

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item = types.KeyboardButton(start_button_text)

                markup.add(item)

                bot.send_message(msg.chat.id,
                                f'Mail <code>{user_data.mail}</code> has been deactivated! ✅', reply_markup=markup)
            except Exception as e:
                start_msg(msg)

def generate_username():
    name = string.ascii_lowercase + string.digits
    username = ''.join(random.choice(name) for i in range(10))

    return username


def check_mail(mail='', chat_id=None):
    sent_ids = set()

    while True:
        time.sleep(5)

        login, domain = mail.split('@')

        req = f'{API}?action=getMessages&login={login}&domain={domain}'
        r = requests.get(req).json()
        length = len(r)

        if length > 0:
            new_ids = set()

            for i in r:
                for k, v in i.items():
                    if k == 'id':
                        new_ids.add(v)

            new_emails = new_ids - sent_ids

            for i in new_emails:
                read_msg = f"{API}?action=readMessage&login={login}&domain={domain}&id={i}"
                r = requests.get(read_msg).json()

                sender = r.get('from')
                subject = r.get('subject')
                text = r.get('textBody')

                bot.send_message(chat_id, f"<b>You have {length} notification!</b>\n\n📬 Mail from {sender} — <b>{subject}</b>:\n\n{text}")

            sent_ids = new_ids

            

if __name__ == "__main__":
    main()
    bot.infinity_polling()