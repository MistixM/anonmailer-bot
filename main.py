import requests
import random
import string
import time
import os
import asyncio

from aiogram import Bot, Dispatcher, types, Router

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery

from aiogram.filters import Command, StateFilter

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup

import config

class FSMForm(StatesGroup):
    check_mail = State()

class UserData():
    def __init__(self, mail=''):
        self.mail = mail

API = 'https://www.1secmail.com/api/v1/'
domain_list = ["1secmail.com", "1secmail.org", "1secmail.net"]
domain = random.choice(domain_list)

dp = Dispatcher()
router = Router()
bot = Bot(token=config.TOKEN, parse_mode='HTML')
user_data = UserData()

def main():

    dp.include_router(router)

    start_button_text = "Generate mail 📨"

    @router.message(Command(commands=['start']), StateFilter(default_state))
    async def start_msg(msg: types.Message):
        item = KeyboardButton(text=start_button_text)
        greet_kb = ReplyKeyboardMarkup(keyboard=[[item]], resize_keyboard=True)

        bot_name = await bot.get_me()
        
        await bot.send_message(msg.chat.id,
                               f"Hello, <b>{msg.from_user.full_name}</b>!👋\n\nMy name's <b>{bot_name.full_name}</b>. Need to create anonymous mail? No problem! With me, you can create a temporary email easily and simply! All notifications will come here and you can easily read them.",
                               reply_markup=greet_kb)
    
    @router.message(Command(commands=['deactivate']), StateFilter(default_state))
    async def deactivate_mail(msg: types.Message):
        print('call deactivation')
        try:
            # Delete mail from API
            login, domain = user_data.mail.split('@')

            url = 'https://www.1secmail.com/mailbox'

            data = {
                'action': 'deleteMailbox',
                'login': login,
                'domain': domain
            }

            r = requests.post(url, data=data)
            print(f'[x] Mail {user_data.mail} has been deleted with {r.status_code} status!\n')
            await msg.reply(f'✅ Mail <code>{user_data.mail}</code> has been deactivated!')

        except Exception as e:
            await start_msg(msg)


    @dp.message(lambda msg: msg.text == start_button_text, StateFilter(default_state))
    async def generate_mail_clicked(msg: types.Message):
        username = generate_username()
        mail = f"{username}@{domain}"
        user_data.mail = mail

        mail_req = requests.get(f'{API}?login={username}&domain={domain}')


        await msg.reply(f'Your temporary mail adress: <code>{mail}</code>\n\n⚠️ This mail will be deactivated after 1 hour. All notifications will come here and you can easily read them.\n\n✅ Use /deactivate command to deactivate your mail')
        await check_mail(user_data.mail, msg.chat.id)


def generate_username():
    name = string.ascii_lowercase + string.digits
    username = ''.join(random.choice(name) for i in range(10))

    return username


async def check_mail(mail='', chat_id=None):
    sent_ids = set()

    while True:
        await asyncio.sleep(5)

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
                
                await bot.send_message(chat_id, f"<b>You have {length} notification!</b>\n\n📬 Mail from {sender} — <b>{subject}</b>:\n\n{text}\n\n✅ Use /deactivate command to deactivate your mail")

            sent_ids = new_ids

            
async def main_bot():
    main()
    await dp.start_polling(bot)

async def main_task():
    await main_bot()

if __name__ == "__main__":
    asyncio.run(main_task())