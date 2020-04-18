import os

import telebot
import praw
import prawcore
import mongoengine
from dotenv import load_dotenv

import meta
from models import Post, User

load_dotenv()

telebot.apihelper.proxy = {"https": os.getenv("PROXY")}
bot = telebot.TeleBot(os.getenv("TOKEN"))
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent=os.getenv("USER_AGENT"))


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user = User.objects(user_id=message.chat.id)
    if user:
        bot.send_message(message.chat.id, meta.REGISTERED_MSG)
        return

    user = User(user_id=message.chat.id, bookmarks=[])
    user.save()
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
            msg = f"🌟 Топ {content['count']} лучших новостей треда" \
                f" {content['topic']} за {date[content['time']]}:" + "\n\n"
        bot.send_message(message.chat.id, msg)
        for post in reddit.subreddit(content["topic"]).top(content["time"], limit=content["count"]):
            if post.selftext:
                description = post.selftext[:400]
                dot_index = description.rindex(".") + 1
                description = description[:dot_index]
            else:
                description = meta.NOINFO_MSG

            record = Post(
                title=post.title,
                topic=content["topic"],
                description=description,
                link=post.shortlink,
                author=post.author.name
            )
            msg = f"📰 {record.title}\n📟 {record.topic}\n🧾 {record.description}\n" \
                f"🔗 {record.link}\n📓 {record.author}\n💯 {post.score}"

            dbpost = Post.objects(link=record.link)
            if not dbpost:
                record.save()

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(
                text="Добавить в закладки", callback_data="add" + record.link))
            bot.send_message(message.chat.id, msg, reply_markup=markup)
    except (prawcore.exceptions.NotFound, prawcore.exceptions.Redirect, prawcore.exceptions.Forbidden):
        msg = meta.ERR_MSG
        bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=["bookmarks"])
def show_bookmarks(message):
    user = User.objects(user_id=message.chat.id).first()
    for bookmark in user.bookmarks:
        record = Post.objects(link=bookmark).first()
        msg = f"📰 {record.title}\n📟 {record.topic}\n🧾 {record.description}\n" \
            f"🔗 {record.link}\n📓 {record.author}\n"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text="Удалить из закладок", callback_data="del" + record.link))
        bot.send_message(message.chat.id, msg, reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data.startswith("add"))
def add_to_bookmarks(call):
    bot.answer_callback_query(call.id)
    link = call.data[3:]
    user = User.objects(user_id=call.message.chat.id).first()
    if link not in user.bookmarks:
        user.bookmarks.append(link)
        user.save()
        bot.send_message(call.message.chat.id, "🔖 Закладка на пост " + link + " добавлена!")
    else:
        bot.send_message(call.message.chat.id, "📖 Пост " + link + " уже находится в закладках!")


@bot.callback_query_handler(lambda call: call.data.startswith("del"))
def del_from_bookmarks(call):
    bot.answer_callback_query(call.id)
    link = call.data[3:]
    user = User.objects(user_id=call.message.chat.id).first()
    if link in user.bookmarks:
        user.bookmarks.remove(link)
        user.save()
        bot.send_message(call.message.chat.id, "❌ Закладка на пост " + link + " удалена!")
    else:
        bot.send_message(call.message.chat.id, "📛 Пост " + link + " уже не находится в закладках!")


if __name__ == "__main__":
    mongoengine.connect(host=os.getenv("DB_HOST"))
    bot.polling(none_stop=True)
