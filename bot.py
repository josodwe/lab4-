import logging
import os
from telegram import Update,BotCommand, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CallbackContext, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from fact_fetcher import TOKEN
import json
import random
FACTS_FILE = "database.txt"
SETTINGS_FILE = "../../Desktop/Amelia/settings.json"

# Функция загрузки фактов из файла
def load_facts():
    with open(FACTS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return  

    user_id = str(update.effective_user.id)
    facts = load_facts()
    settings = load_settings()

    hidden_facts = set(settings.get(user_id, []))
    available_facts = [fact for fact in facts if fact.split(". ")[0] not in hidden_facts]

    if not available_facts:
        await update.message.reply_text("У вас не осталось доступных фактов.")
        return

    fact = random.choice(available_facts)

    keyboard = [
        [
            InlineKeyboardButton("👍", callback_data=f"like:{fact.split('. ')[0]}"),
            InlineKeyboardButton("👎", callback_data=f"dislike:{fact.split('. ')[0]}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(fact, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return  

    await query.answer()

    user_id = str(query.from_user.id)
    settings = load_settings()
    data = query.data


    action, fact_number = data.split(":")

    if action == "dislike":
    
        if user_id not in settings:
            settings[user_id] = []
        if fact_number not in settings[user_id]:
            settings[user_id].append(fact_number)
            save_settings(settings)
        await query.edit_message_text(f"Факт {fact_number} скрыт.")
    elif action == "like":
        await query.answer("Отличный выбор!")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    settings = load_settings()
    hidden_facts = settings.get(user_id, [])

    if not hidden_facts:
        await update.message.reply_text("У вас нет скрытых фактов.")
        return

    text = "Скрытые факты:\n" + "\n".join(hidden_facts)
    await update.message.reply_text(text)

    if context.args:
        action = context.args[0]
        
        if action == "add" and len(context.args) > 1:
            fact_to_add = context.args[1]
            if fact_to_add not in hidden_facts:
                hidden_facts.append(fact_to_add)
                settings[user_id] = hidden_facts
                save_settings(settings)
                await update.message.reply_text(f"Факт {fact_to_add} добавлен в скрытые.")
            else:
                await update.message.reply_text(f"Факт {fact_to_add} уже скрыт.")
        
        elif action == "remove" and len(context.args) > 1:
            fact_to_remove = context.args[1]
            if fact_to_remove in hidden_facts:
                hidden_facts.remove(fact_to_remove)
                settings[user_id] = hidden_facts
                save_settings(settings)
                await update.message.reply_text(f"Факт {fact_to_remove} удалён из скрытых.")
            else:
                await update.message.reply_text(f"Факт {fact_to_remove} не найден в скрытых.")
        
        else:
            await update.message.reply_text("Пожалуйста, используйте правильный формат: /settings add <fact> или /settings remove <fact>")


async def set_commands(application):
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("random_fact", "Получить случайный факт"),
        BotCommand("settings", "Управление скрытыми фактами"),
        BotCommand("help", "Список команд и их описание")
    ]
    await application.bot.set_my_commands(commands)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/random_fact - Получить случайный факт\n"
        "/settings - Управление скрытыми фактами\n"
        "/settings add (номер) - добавить факт в скрытые\n"
        "/settings remove (номер) - удалить факт из скрытых\n"
        "/help - Список команд и их описание"
    )
    await update.message.reply_text(help_text)

if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("random_fact", random_fact))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()
