import os
import background
import FreeAI
import telebot
from telebot import types
import time
import google_speech

token = os.environ['BOT_TOKEN']
prompt1 = "Напиши любой анекдот "
prompt2 = "Напиши анекдот про "
temperature = 0.7  # Set custom temperature (optional)
max_tokens = 4096  # Set custom max_tokens (optional)

bot = telebot.TeleBot(token)
keyboard_main = types.ReplyKeyboardMarkup(True, True)
keyboard_main.add('Рандомный анек', 'Своя затравка', 'Помощь')
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
    'Если есть желание использовать свою затравку по типу "кто? где? про что?", то используй кнопку "Своя затравка"',
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


@bot.message_handler(content_types=['text'])
def com_text(message):
  if message.text.lower() == 'рандомный анек':
    com_random(message)
  elif message.text.lower() == 'своя затравка':
    com_topic(message)
  elif message.text.lower() == 'помощь':
    com_help(message)


background.keep_alive()
bot.polling()
