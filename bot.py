#standard:
import json
import io
import os
import logging

#third party:
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from telegram.ext import Defaults
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, MAX_MESSAGE_LENGTH, ParseMode
from telegram.ext import CallbackQueryHandler, InlineQueryHandler
from telegram.ext import CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler

#local:
from readConfigfile import read_config
import dataFuncs


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) # setting up the logging module
logger = logging.getLogger(__name__)

BOT_TOKEN = read_config("config.ini", "Bot")["bottoken"]
MAIN_GROUP = read_config("config.ini", "Telegram")["maingroupid"]
CHANNEL = read_config("config.ini", "Telegram")["channelid"]
ADMIN_GROUP = read_config("config.ini", "Telegram")["admingroupid"]
QUESTION_WORD = read_config("config.ini", "Other")["questionword"]
ANSWER_WORD = read_config("config.ini", "Other")["answerword"]

defaults = Defaults(parse_mode=ParseMode.HTML)
updater = Updater(token=BOT_TOKEN, use_context=True, defaults=defaults)


def main():
    disp = updater.dispatcher

    addHandlers(disp)

    updater.start_polling()
    updater.idle()

def addHandlers(dispatcher):
    dispatcher.add_error_handler(error_log)

    dispatcher.add_handler(CommandHandler('start', start, Filters.private), group=1)
    dispatcher.add_handler(CommandHandler('help', help), group=1)
    dispatcher.add_handler(CommandHandler('sendMeChatId', send_me_chat_id), group=1)

    dispatcher.add_handler(MessageHandler(Filters.group & (~Filters.command), processQuestion), group=1)
    dispatcher.add_handler(MessageHandler(Filters.group & (~Filters.command), processAnswerReply), group=2)

    dispatcher.add_handler(MessageHandler(Filters.private & (~Filters.command), getQuestionById), group=1)
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(answerButton, pattern=r'question')],
        states={
            1: [MessageHandler(Filters.private & (~Filters.command), processAnswerPrivate)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern=r'cancel')]
    ))


def error_log(update, context):
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))


def start(update, context):
    chatid = update.effective_chat.id
    fname = update.effective_chat.first_name

    message = f'Hola {fname}, este bot tiene como objetivo ayudar al colectivo de MATCOM a organizar las preguntas y respuestas en el chat destinado a brindar apoyo a los estudiantes del preuniversitario en la preparacion para las pruebas de ingreso.\nSi eres parte del colectivo de MATCOM tambien puedes responder las preguntas desde aqui.\n\nEnvia el codigo de la pregunta y te brindare las respuestas que tenemos actualmente. Usa el comando /help para informacion mas detallada.\n\nCualquier duda escribeme: <a href="tg://user?id=887217360">@SergiPantoja</a>'

    try:
        context.bot.send_message(chat_id=chatid, text=message)
    except:
        raise

def help(update, context):
    chatid = update.effective_chat.id
    message = "⚙️ Para hacer una pregunta manda un mensaje que incluya #" + QUESTION_WORD + " en su texto en el grupo principal, este mensaje se enviara al canal de preguntas y respuestas incluyendo el codigo de la pregunta.\n⚙️ Para responder una pregunta tienes dos vias:\n1 - En el grupo privado hazle 'reply' al mensaje de pregunta enviado por el bot.\n2 - En privado con el bot envia el codigo de la pregunta (se encuentra en el canal) toca el boton 'responder' y envia tu respuesta.\nPor ambas vias tu mensaje debe incluir #" + ANSWER_WORD + ".\n⚙️Tanto preguntas como respuestas permiten el uso de fotos, documentos o audios, pero no olvides incluir los hashtags en el mensaje."

    try:
        context.bot.send_message(chat_id=chatid, text=message)
    except:
        raise


def processQuestion(update, context):
    chatId = update.effective_chat.id
    if str(chatId) != MAIN_GROUP:
        return
    if update.message is None or (update.message.text is None and update.message.caption is None):
        return

    askedBy = update.effective_user.username if update.effective_user.username is not None else update.effective_user.first_name
    userId = update.effective_user.id
    receivedText = update.message.text if update.message.text is not None else update.message.caption

    if ("#" + QUESTION_WORD).lower() in receivedText.lower():
        path = os.path.join(dataFuncs.PATH, "question.csv")
        questionId = len(dataFuncs.loadFileRows(path)) + 1
        topMessage = '#' + QUESTION_WORD + ' #%s\nPregunta hecha por <a href="tg://user?id=%s">%s</a>\n\n' % (questionId, userId, askedBy)
        bottomMessage = '\n\nLinks de las respuestas actuales:'

        #Sending to channel and saving question for later edits
        msg = sendTo(context.bot, CHANNEL, update.effective_message, top=topMessage, bottom=bottomMessage)
        dataFuncs.write_question(msg.link, msg.message_id, topMessage + receivedText + bottomMessage)

        #Sending to adming group for replies
        sendTo(context.bot, ADMIN_GROUP, update.effective_message, top=topMessage)

        #sending confirmation
        context.bot.send_message(chat_id=chatId, text="Pregunta enviada", reply_to_message_id=update.effective_message.message_id)
    else:
        return

def processAnswerReply(update, context):
    chatId = update.effective_chat.id
    if str(chatId) != ADMIN_GROUP:
        return
    if update.message is None or (update.message.text is None and update.message.caption is None):
        return

    receivedText = update.message.text if update.message.text is not None else update.message.caption

    if ("#" + ANSWER_WORD).lower() in receivedText.lower():
        if update.message.reply_to_message is None:
            context.bot.send_message(chat_id=chatId, text="Al responder una pregunta en el grupo hagale 'reply' al texto de la misma, gracias.")
            return
        else:
            processAnswerHelper(update, context)
            #sending confirmation
            context.bot.send_message(chat_id=chatId, text="Respuesta enviada", reply_to_message_id=update.effective_message.message_id)
    else:
        return

def getQuestionById(update, context):
    message = update.effective_message
    try:
        if not message.text.isdigit():
            return
    except:
        return
    questionId = message.text

    #load question
    try:
        question = dataFuncs.get_question(questionId)
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Parece que dicha pregunta no existe...")
        return

    #temporarily save the ID in case the user wants to answer the question
    userId = update.effective_chat.id
    context.bot_data[userId] = questionId

    questionLink = question["link"]
    answerLinks = question["answers"].values()

    #Sending response
    message = "Pregunta:\n %s\n\nRespuestas:\n" % questionLink
    for i in answerLinks:
        message += i + "\n"
    kbd = [[InlineKeyboardButton("Responder", callback_data="question")]]
    context.bot.send_message(chat_id=userId, text=message, reply_markup=InlineKeyboardMarkup(kbd))
def answerButton(update, context):
    query = update.callback_query
    query.answer()

    kbd = [[InlineKeyboardButton("Cancelar", callback_data="cancel")]]

    context.bot.send_message(chat_id=update.effective_chat.id, text="Envie la respuesta.", reply_markup=InlineKeyboardMarkup(kbd))
    return 1
def cancel(update, context):
    query = update.callback_query
    query.answer()

    context.bot_data.pop(update.effective_chat.id, None)

    query.edit_message_text(text="accion cancelada")
    return ConversationHandler.END
def processAnswerPrivate(update, context):
    if update.message is None or (update.message.text is None and update.message.caption is None):
        context.bot_data.pop(update.effective_chat.id, None)
        return ConversationHandler.END

    receivedText = update.message.text if update.message.text is not None else update.message.caption

    if ("#" + ANSWER_WORD).lower() in receivedText.lower():
        try:
            questionId = context.bot_data.pop(update.effective_chat.id)
        except KeyError:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Oops!")
            return

        processAnswerHelper(update, context, qId=questionId)

        #sending confirmation
        context.bot.send_message(chat_id=update.effective_chat.id, text="Respuesta enviada")
    else:
        context.bot_data.pop(update.effective_chat.id, None)
        return ConversationHandler.END


# UTILS:
def sendTo(bot, chatId, message, **kwargs):
    """
    Sends a message to the specified chat with the specified format.

    Accepted kwargs:
    top: String to be included before the text or caption provided.
    bottom: String to be included after the text or caption provided.

    """

    text = message.text
    audio = message.audio.file_id if message.audio is not None else None
    doc = message.document.file_id if message.document is not None else None
    caption = message.caption
    try:
        photo = message.photo[0].file_id if message.photo is not None else None
    except:
        photo = None

    top = kwargs.get("top", None)
    bottom = kwargs.get("bottom", None)

    str = text if text is not None else caption
    if top is not None:
        str = top + str
    if bottom is not None:
        str += bottom

    if text is not None:
        msg = bot.sendMessage(chat_id=chatId, text=str, disable_web_page_preview=True)
    elif audio is not None:
        if caption is not None:
            msg = bot.sendAudio(chat_id=chatId, audio=audio, caption=str)
        else:
            msg = bot.sendAudio(chat_id=chatId, audio=audio)
    elif doc is not None:
        if caption is not None:
            msg = bot.sendDocument(chat_id=chatId, document=doc, caption=str)
        else:
            msg = bot.sendDocument(chat_id=chatId, document=doc)
    elif photo is not None:
        if caption is not None:
            msg = bot.sendPhoto(chat_id=chatId, photo=photo, caption=str)
        else:
            msg = bot.sendPhoto(chat_id=chatId, photo=photo)

    return msg

def processAnswerHelper(update, context, qId=None):
    answeredBy = update.effective_user.username if update.effective_user.username is not None else update.effective_user.first_name
    userId = update.effective_user.id

    #getting questionId
    if qId is None:
        questionAnswered = update.message.reply_to_message

        if questionAnswered.caption is not None:
            questionId = questionAnswered.caption.split(" ")[1][1:].split("\n")[0]
        else:
            questionId = questionAnswered.text.split(" ")[1][1:].split("\n")[0]
    else:
        questionId = qId

    #Load question
    questionDict = dataFuncs.get_question(questionId)
    answerNumber = len(questionDict["answers"]) + 1

    #Sending to channel and save answer
    topMessage = "#" + ANSWER_WORD + "\npregunta #%s - respuesta #%s\n\n" % (questionId, answerNumber)
    bottomMessage = '\n\n<a href="%s">Link a la pregunta</a>\n\nRespuesta brindada por <a href="tg://user?id=%s">%s</a>' % (questionDict["link"], userId, answeredBy)
    msg = sendTo(context.bot, CHANNEL, update.message, top=topMessage, bottom=bottomMessage)
    dataFuncs.write_answer(msg.link, questionId)

    #Sending to group
    sendTo(context.bot, MAIN_GROUP, update.message, top=topMessage, bottom=bottomMessage)

    #Edit the question original message in the channel with the new answer
    newText = questionDict["text"] + "\n"
    j = 1
    for i in questionDict["answers"].values():
        newText += f"({j}) " + i + "\n"
        j += 1
    newText += f"({j}) " + msg.link

    questionMessageId = questionDict["messageId"]
    try:
        context.bot.edit_message_text(text=newText, chat_id=CHANNEL, message_id=questionMessageId, disable_web_page_preview=True)
    except:
        try:
            context.bot.edit_message_caption(chat_id=CHANNEL, message_id=questionMessageId, caption=newText)
        except:
            raise

def send_me_chat_id(update, context): #group
    """ sends the caller the id of the chat in which this command was sent.
    Use it to know what IDs to put in the config.ini file ;) """
    userid = update.effective_user.id
    chatid = update.effective_chat.id
    context.bot.send_message(chat_id=userid, text=chatid)


if __name__=="__main__":
    main()
