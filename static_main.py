# Import required libraries
import requests
import random
import string
import time

# Telegram API
import telebot
from telebot import types

# Config (TOKEN, API link)
import config

# Personal mail for each user 
class UserData():
    def __init__(self, mail=''):
        self.mail = mail

# Prepare constans
API = config.API
TOKEN = config.TOKEN

# Prepare domain lists and choose random
domain_list = ["1secmail.com", "1secmail.org", "1secmail.net"]
domain = random.choice(domain_list)

# Connect bot and create user_data object
bot = telebot.TeleBot(token=TOKEN, parse_mode='HTML')
user_data = UserData()

def main():
    # Button to start generation
    start_button_text = "Generate mail 📨"

    # Start command
    @bot.message_handler(commands=['start'])
    def start_msg(msg):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton(start_button_text)

        markup.add(item)

        bot.send_message(msg.chat.id,
                               f"Hello, <b>{msg.from_user.full_name}</b>!👋\n\nMy name's <b>{bot.get_me().full_name}</b>. Need to create anonymous mail? No problem! With me, you can create a temporary email easily and simply! All notifications will come here and you can easily read them.",
                               reply_markup=markup)
    
    # Callback scanner
    @bot.message_handler(content_types='text')
    def generate_mail_clicked(msg):
        # If generate button clicked, generate username and prepare mail
        if msg.text == start_button_text:
            username = generate_username()
            mail = f'{username}@{domain}'
            user_data.mail = mail

            # Register our mail
            mail_req = requests.get(f'{API}?login={username}&domain={domain}')

            # Add deactivation button if user wants to
            btn = types.InlineKeyboardButton(text='Deactivate mail 🗑️', callback_data='deactivate_mail')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(btn)

            # Say to user that mail was successfuly created
            bot.send_message(msg.chat.id,
                             f'Your temporary mail adress: <code>{mail}</code>\n\n⚠️ This mail will be deactivated after 1 hour. All notifications will come here and you can easily read them.',
                             reply_markup=markup)
            
            # Call check_mail function that will check incoming letters
            check_mail(mail, msg.chat.id)

        # If deactivation button clicked, deactivate current mail via using POST request to API
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

                # After success deactivation, return generate button
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item = types.KeyboardButton(start_button_text)

                markup.add(item)

                # And say that everything is okay and user can generate another one
                bot.send_message(msg.chat.id,
                                f'Mail <code>{user_data.mail}</code> has been deactivated! ✅', reply_markup=markup)
            except Exception as e:
                start_msg(msg)

# Username generation for mail using string and random libraries.
def generate_username() -> str:
    name = string.ascii_lowercase + string.digits
    username = ''.join(random.choice(name) for i in range(10))

    return username

# Check incoming letters to user's mail
def check_mail(mail='', chat_id=None):
    sent_ids = set() # Create a set that will write already available letters

    # Check this in infinite loop
    while True:
        time.sleep(5) # API check it every 5 seconds

        login, domain = mail.split('@')

        # Use GET request to API to check available messages
        req = f'{API}?action=getMessages&login={login}&domain={domain}'

        # Convert to JSON
        r = requests.get(req).json() 

        # Calculate length of data
        length = len(r)

        # This condition will check number of messages in user's mail
        # If it's more than 0, add to set via 'for' loop
        if length > 0:
            new_ids = set()

            for i in r:
                for k, v in i.items():
                    # Need to get ID
                    if k == 'id':
                        new_ids.add(v)
            
            new_emails = new_ids - sent_ids

            # Check each mails in set
            for i in new_emails:
                # Open the message via using our login and domain with mail ID
                read_msg = f"{API}?action=readMessage&login={login}&domain={domain}&id={i}"

                # Convert to JSON
                r = requests.get(read_msg).json()

                # Prepare data such as sender, subject and content
                sender = r.get('from')
                subject = r.get('subject')
                text = r.get('textBody')

                # Notify the user about new message in mail
                bot.send_message(chat_id, f"<b>You have {length} notification!</b>\n\n📬 Mail from {sender} — <b>{subject}</b>:\n\n{text}")

            sent_ids = new_ids

            

if __name__ == "__main__":
    main()
    bot.infinity_polling()