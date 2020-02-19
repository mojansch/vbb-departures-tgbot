import logging, json
from datetime import datetime

import requests
from telegram import (
    Update,
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

token = "822981203:AAEZ5Y4zZL2UhffvtZ8iLmvVUbPnuiwEbaw"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Willkommen, dieser Bot befindet sich noch in der Entwicklung.

Aktuelle Funktionen:
/abfahrten <Station>""",
    )


def departures(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Nutzung: /abfahrten <Stationsname>"
        )
        return
    query = " ".join(context.args)
    stations = requests.get(
        "https://3.api.transport.rest/stations", params={"query": query, "fuzzy": "true"}
    ).json()

    if not stations:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Diese Station wurde nicht gefunden"
        )
    else:
        stationen_keyboard = []
        for station in stations:
            stationen_keyboard.append(
                [InlineKeyboardButton(station["name"], callback_data=station["id"])]
            )

        stationen_markup = InlineKeyboardMarkup(stationen_keyboard)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welche Station meinen Sie?",
            reply_markup=stationen_markup,
        )


def departures_button(update: Update, context: CallbackContext):
    query = update.callback_query
    station_id = query.data

    station_name = requests.get(
        f"https://3.api.transport.rest/stations/{station_id}"
    ).json()["name"]
    query.edit_message_text(text=f"Abfahrten für {station_name}:")
    departures_list = requests.get(
        f"https://3.api.transport.rest/stations/{station_id}/departures",
        params={"query": query, "fuzzy": "true"},
    ).json()
    answer = "Abfahrten"
    for departure in departures_list:
        if not "cancelled" in departure:
            answer = f"""
Linie: *{departure['line']['name']} {departure['direction']}*
Station: {departure['stop']['name']}
Abfahrtszeit: *{datetime.fromisoformat(departure['when']).strftime('%H:%M')}*"""
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=answer,
            parse_mode=ParseMode.MARKDOWN,
        )


def location(update: Update, context: CallbackContext):
    user_location = update.effective_message.location
    stations = requests.get(
        "https://3.api.transport.rest/stops/nearby",
        params={
            "latitude": user_location.latitude,
            "longitude": user_location.longitude,
            "results": 5,
        },
    ).json()

    if not stations:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Es wurden keine Stationen in der Nähe gefunden.",
        )
    else:
        if len(stations) > 5:
            stations = stations[0:5]
        stationen_keyboard = []
        for station in stations:
            stationen_keyboard.append(
                [InlineKeyboardButton(station["name"], callback_data=station["id"])]
            )

        stationen_markup = InlineKeyboardMarkup(stationen_keyboard)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welche Station meinen Sie?",
            reply_markup=stationen_markup,
        )


def rm(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardRemove()
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Test", reply_markup=reply_markup
    )


def main():
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("abfahrten", departures))
    dp.add_handler(CallbackQueryHandler(departures_button))
    dp.add_handler(CommandHandler("rm", rm))
    dp.add_handler(MessageHandler(Filters.location, location))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
