import logging
import psycopg2 as psy
import sys
from aiogram import Bot, Dispatcher, executor, types
import logging
from systemd import journal
from pytz import timezone
from datetime import datetime
import datetime



ukraine_time = timezone('Europe/Kiev')
log = logging.getLogger('ioretcio')
log.addHandler(journal.JournalHandler())
log.setLevel(logging.INFO)

def io(text):
    print(text)
    log.error(text)
    
conn = psy.connect(database="support_and_suggestions_bot",
                    host="localhost",
                    user="postgres",
                    password="postgres",
                    port=5432)

conn.autocommit = True
id = sys.argv[1]
with conn.cursor() as cursor:
    cursor.execute(f"SELECT * FROM entities WHERE id='{id}'")
    row = cursor.fetchone()
    TOKEN = row[1]
    target_chat = row[2]
    greatings = row[3]  
bot = Bot(TOKEN)
dp = Dispatcher(bot)
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(f"{greatings}")
    
@dp.message_handler(content_types=['any'])
async def echo(message):
    if( message["from"]["id"] == message["chat"]["id"]):
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT count(*) from blacklist where tg_id={message['from']['id']}")
            result = cursor.fetchone()
            if (result[0]==0):
                result =await bot.forward_message(target_chat, message["chat"]["id"], message["message_id"])
        with conn.cursor() as cursor:
            cursor.execute(f"INSERT INTO messages (from_chat_id, from_message_id, admin_chat_id, admin_message_id, time, bot_id)\
                VALUES ({message['message_id']}, {message['from']['id']}, {target_chat}, {result['message_id']}, { datetime.datetime.timestamp(datetime.datetime.now(ukraine_time))  },{id}  )")
    else:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * from messages where admin_message_id={message['reply_to_message']['message_id']} and admin_chat_id={target_chat}")
            user_id = cursor.fetchone()[2]
            
            if(message.text=="/razban" or message.text=="разбан" or message.text == "Разбан"):
                cursor.execute(f"DELETE FROM blacklist WHERE tg_id={user_id}")
                
                
            if(message.text=="/ban" or message.text=="бан" or message.text == "Бан"):
                cursor.execute(f"INSERT INTO blacklist (tg_id) VALUES ({user_id})")
            else:
                await bot.copy_message(user_id, target_chat, message["message_id"])

            

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    