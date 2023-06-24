import os
import background
import FreeAI
import telebot
from telebot import types
import time
import google_speech
import schedule
from multiprocessing.context import Process

token = os.environ['BOT_TOKEN']
prompt1 = "Напиши любой анекдот "
prompt2 = "Напиши анекдот про "
temperature = 0.7  # Set custom temperature (optional)
max_tokens = 4096  # Set custom max_tokens (optional)

bot = telebot.TeleBot(token)
keyboard_main = types.ReplyKeyboardMarkup(True, True)
keyboard_main.add('Рандомный анек', 'Своя затравка', 'Помощь',
                  'Включить рассылку', 'Отключить рассылку')
keyboard_voice = types.ReplyKeyboardMarkup(True, True)
keyboard_voice.add('Да', 'Нет')


@bot.message_handler(commands=['start'])
def com_start(message):
  bot.send_message(message.chat.id,
                   "На связи AnekBot, могу рассказать анек на любую тему",
                   reply_markup=keyboard_main)


@bot.message_handler(commands=['help'])
def com_help(message):
  bot.send_message(
    message.chat.id,
    'Если хочешь получить случайный анекдот от нейронки, жми кнопку "Рандомный анек"'
  )
  time.sleep(0.5)
  bot.send_message(
    message.chat.id,
    'Если есть желание использовать свою затравку по типу "кто? где? про что?", то используй кнопку "Своя затравка"'
  )
  time.sleep(0.5)
  bot.send_message(
    message.chat.id,
    'Если хочешь, чтобы тебе автоматически приходили анеки утром и вечером, можешь включить рассылку по кнопке "Включить рассылку"'
  )
  time.sleep(0.5)
  bot.send_message(
    message.chat.id,
    'Захочешь отключить рассылку - нажимай "Отключить рассылку"',
    reply_markup=keyboard_main)


@bot.message_handler(commands=['random'])
def com_random(message):
  bot.send_message(message.chat.id, 'Ща придумаю')
  bot.send_chat_action(message.chat.id, 'typing')
  response = FreeAI.generate(prompt1,
                             temperature=temperature,
                             max_tokens=max_tokens)
  msg = bot.send_message(message.chat.id,
                         'Озвучить анек?',
                         reply_markup=keyboard_voice)
  bot.register_next_step_handler(msg, choice, response)


@bot.message_handler(commands=['topic'])
def com_topic(message):
  msg = bot.send_message(message.chat.id, 'Ну давай, пиши')
  bot.register_next_step_handler(msg, com_gen)


def com_gen(message):
  bot.send_message(message.chat.id, 'Ща придумаю')
  bot.send_chat_action(message.chat.id, 'typing')
  pr = prompt2 + str(message)
  response = FreeAI.generate(pr,
                             temperature=temperature,
                             max_tokens=max_tokens)
  msg = bot.send_message(message.chat.id,
                         'Озвучить анек?',
                         reply_markup=keyboard_voice)
  bot.register_next_step_handler(msg, choice, response)


def choice(message, response):
  if message.text == "Да":
    write_voice(message, response)
  else:
    write_text(message, response)


def write_voice(message, response):
  lang = "ru"
  speech = google_speech.Speech(response, lang)
  speech.save('anek.mp3')
  anek_file = open('anek.mp3', 'rb')
  bot.send_voice(message.chat.id, anek_file, reply_markup=keyboard_main)
  if os.path.exists("anek.mp3"):
    os.remove('anek.mp3')
  if os.path.exists("conversation_memory.json"):
    os.remove("conversation_memory.json")


def write_text(message, response):
  bot.send_message(message.chat.id, response, reply_markup=keyboard_main)
  if os.path.exists("conversation_memory.json"):
    os.remove("conversation_memory.json")


@bot.message_handler(content_types=['mail'])
def com_mail(message):
  flag = False
  with open('id.txt', 'r+') as f:
    for line in f:
      if line == str(message.chat.id) + '\n':
        flag = True

    if not flag:
      print(message.chat.id, file=f)
      bot.send_message(message.chat.id,
                       'Рассылка включена',
                       reply_markup=keyboard_main)
    else:
      bot.send_message(message.chat.id,
                       'Рассылка уже включена',
                       reply_markup=keyboard_main)


@bot.message_handler(content_types=['unmail'])
def com_unmail(message):
  with open('id.txt', 'r') as f:
    lines = f.readlines()
  with open('id.txt', 'w') as f:
    for line in lines:
      if line.strip('\n') != str(message.chat.id):
        f.write(line)
  bot.send_message(message.chat.id,
                   'Рассылка отключена',
                   reply_markup=keyboard_main)


@bot.message_handler(content_types=['text'])
def com_text(message):
  if message.text.lower() == 'рандомный анек':
    com_random(message)
  elif message.text.lower() == 'своя затравка':
    com_topic(message)
  elif message.text.lower() == 'помощь':
    com_help(message)
  elif message.text.lower() == 'включить рассылку':
    com_mail(message)
  elif message.text.lower() == 'отключить рассылку':
    com_unmail(message)


def mailing():
  for userid in open('id.txt', 'r').readlines():
    response = FreeAI.generate(prompt1,
                               temperature=temperature,
                               max_tokens=max_tokens)
    bot.send_message(userid, response)
    if os.path.exists("conversation_memory.json"):
      os.remove("conversation_memory.json")


schedule.every().day.at('06:00').do(mailing)
schedule.every().day.at('18:00').do(mailing)


class ScheduleMessage():

  def try_send_schedule():
    while True:
      schedule.run_pending()
      time.sleep(1)

  def start_process():
    p1 = Process(target=ScheduleMessage.try_send_schedule, args=())
    p1.start()


if __name__ == '__main__':
  ScheduleMessage.start_process()
  try:
    background.keep_alive()
    bot.polling()
  except:
    pass
