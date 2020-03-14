import os

import telebot
import praw
import prawcore
from dotenv import load_dotenv

import meta

load_dotenv()

telebot.apihelper.proxy = {"https": os.getenv("PROXY")}
bot = telebot.TeleBot(os.getenv("TOKEN"))
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent=os.getenv("USER_AGENT"))


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, meta.START_MSG)


@bot.message_handler(commands=["help"])
def send_help(message):
    bot.send_message(message.chat.id, meta.HELP_MSG, parse_mode="Markdown")


@bot.message_handler(commands=["top"])
def send_top(message):
    attributes = message.text.split()[1:]
    attr_len = len(attributes)

    content = {
        "topic": "cats",
        "count": 10,
        "time": "day",
        "is_cat": False
    }
    date = {
        "day": "день",
        "week": "неделю",
        "month": "месяц",
        "year": "год"
    }

    msg = ""

    if attr_len == 0:
        msg = meta.CAT_MSG
        content["is_cat"] = True
        content["count"] = 1
    if attr_len > 0:
        content["topic"] = attributes[0]
    if attr_len > 1:
        count = int(attributes[1])
        if count < 1:
            count = 1
        content["count"] = count
    if attr_len > 2:
        content["time"] = attributes[2]

    try:
        if not content["is_cat"]:
            msg += f"🔝 Топ {content['count']} лучших новостей треда" \
                f" {content['topic']} за {date[content['time']]}:" + "\n\n"
        for post in reddit.subreddit(content["topic"]).top(content["time"], limit=content["count"]):
            msg += f"📰 {post.title}\n🔗 {post.url}\n📓 {post.author.name}\n💯 {post.score}\n\n"
    except (prawcore.exceptions.NotFound, prawcore.exceptions.Redirect, prawcore.exceptions.Forbidden):
        msg = meta.ERR_MSG

    bot.send_message(message.chat.id, msg)


if __name__ == "__main__":
    bot.polling(none_stop=True)
