import telebot
import config
import sqlite3

bot = telebot.TeleBot(config.token)

def init_db():
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            user_id INTEGER,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(message.chat.id, config.img, caption=config.message_welcome)

@bot.message_handler(commands=['answer'])
def answer_user(message):
    try:
        _, user_id, *reply_message = message.text.split()
        user_id = int(user_id)
        reply_text = ' '.join(reply_message)
        
        send_message_to_user(user_id, reply_text)
        notify_admin(f"Сообщение отправлено пользователю {user_id}: {reply_text}")
    except Exception as e:
        bot.reply_to(message, "Ошибка: проверьте правильность команды.")


@bot.message_handler(commands=['list_messages'])
def list_messages(message):
    try:
        user_id = int(message.text.split()[1])
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        cursor.execute('SELECT message FROM user_messages WHERE user_id = ?', (user_id,))
        messages = cursor.fetchall()
        conn.close()
        
        if messages:
            response = "\n".join(msg[0] for msg in messages)
            bot.reply_to(message, f"Сообщения для пользователя {user_id}:\n{response}")
        else:
            bot.reply_to(message, f"Нет сообщений для пользователя {user_id}.")
    except Exception as e:
        bot.reply_to(message, "Ошибка: проверьте правильность команды.")


@bot.message_handler(func=lambda message: True)
def handle_user_message(message):
    user_nick = message.from_user.first_name
    user_id = message.from_user.id
    message_text = message.text
    
    save_message_to_db(user_id, message_text)

    if message.forward_from:
        notify_admin(f"Пересланное сообщение от {user_nick} (ID: {user_id}): {message_text}")
        send_message_to_user(user_id, config.message_send)
    else:
        notify_admin(f"Новое сообщение от {user_nick} (ID: {user_id}): {message_text}")
        send_message_to_user(user_id, config.message_send)

def notify_admin(notification_text):
    bot.send_message(config.admin, notification_text)

def send_message_to_user(user_id, text):
    bot.send_message(user_id, text)

def save_message_to_db(user_id, message_text):
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_messages (user_id, message) VALUES (?, ?)', (user_id, message_text))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Бот запущен...")
    bot.polling()