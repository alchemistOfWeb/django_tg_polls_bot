from django.utils import timezone
from django.conf import settings

import datetime
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.polling import static_text
from tgbot.handlers.polling.keyboards import make_keyboard_for_question
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User as TgUser
from polls.models import Poll, Answer


CONTROL_DATA_KEY = 'control_data'
QUESTION_INDEX_KEY = 'current_question'
QUESTIONS_NUM_KEY = 'questions_num'
POLL_ID_KEY = "poll_id"
INPUT_DATA_KEY = "input_data"
ANSWERS_KEY = "answers"


def command_start(update: Update, context: CallbackContext) -> None:
    user, created = TgUser.get_user_and_created(update, context)

    first_active_poll = Poll.objects.filter(active=True).first()
    questions_num = first_active_poll.questions.count()
    current_question_ind = 0

    if current_question_ind >= questions_num:
        handle_polling_end(user, update, context)
        return

    context.chat_data[INPUT_DATA_KEY] = {}
    context.chat_data[CONTROL_DATA_KEY] = {}
    context.chat_data[INPUT_DATA_KEY][ANSWERS_KEY] = []

    context.chat_data[INPUT_DATA_KEY][POLL_ID_KEY] = first_active_poll.id
    context.chat_data[CONTROL_DATA_KEY][QUESTIONS_NUM_KEY] = questions_num
    question = first_active_poll.questions.order_by('order')[current_question_ind]
    
    current_question_ind +=1
    context.chat_data[CONTROL_DATA_KEY]["question_id"] = question.id
    context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY] = current_question_ind
    
    # send first question
    msg = update.message.reply_text(
        text=question.text,
        reply_markup=make_keyboard_for_question(question)
    )
    context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"] = []
    context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"].append(msg.message_id)


def question_message_handling(update: Update, context: CallbackContext) -> None:
    user = TgUser.get_user(update, context)
    user_id = user.user_id
    answer_text = update.message.text
    prev_question_id = context.chat_data[CONTROL_DATA_KEY]["question_id"]
    context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"].append(update.message.message_id)

    # set answer id with choice id in answers list in chat_data
    current_question_ind = context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY]
    
    context.chat_data[INPUT_DATA_KEY][ANSWERS_KEY].append({
        "question": prev_question_id, 
        "text": answer_text
    })

    # get poll
    current_poll = get_poll(context)

    # check if current_question_ind more than limit
    questions_limit = context.chat_data[CONTROL_DATA_KEY][QUESTIONS_NUM_KEY]
    if current_question_ind >= questions_limit:
        handle_polling_end(user, update, context)
        return

    # send new question
    question = current_poll.questions.order_by('order')[current_question_ind]
    current_question_ind +=1
    context.chat_data[CONTROL_DATA_KEY]["question_id"] = question.id
    context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY] = current_question_ind
    msg = send_question_msg(context, user_id, question)
    context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"].append(msg.message_id)


def question_handling(update: Update, context: CallbackContext) -> None:
    # callback_data: {QUESTION_CHOICE_BTN_PRFX}-{choice.id}
    # get some args and params and anwer handling:
    user = TgUser.get_user(update, context)
    user_id = user.user_id
    query = update.callback_query
    query.answer()
    callback_data = query.data
    choice_id = int(callback_data.split('-')[1])
    prev_question_id = context.chat_data[CONTROL_DATA_KEY]["question_id"]

    # set answer id with choice id in answers list in chat_data
    current_question_ind = context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY]
    
    context.chat_data[INPUT_DATA_KEY][ANSWERS_KEY].append({
        "question": prev_question_id, 
        "choice": choice_id
    })

    # get poll
    current_poll = get_poll(context)

    # check if current_question_ind more than limit
    questions_limit = context.chat_data[CONTROL_DATA_KEY][QUESTIONS_NUM_KEY]
    if current_question_ind >= questions_limit:
        handle_polling_end(user, update, context)
        return

    # send new question
    question = current_poll.questions.order_by('order')[current_question_ind]
    current_question_ind +=1
    context.chat_data[CONTROL_DATA_KEY]["question_id"] = question.id
    context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY] = current_question_ind
    msg = send_question_msg(context, user_id, question)
    context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"].append(msg.message_id)


def send_question_msg(context, user_id, question):
    return context.bot.send_message(
        chat_id=user_id,
        text=question.text,
        reply_markup=make_keyboard_for_question(question),
        parse_mode=ParseMode.HTML
    )


def get_poll(context):
        current_poll_id = context.chat_data[INPUT_DATA_KEY][POLL_ID_KEY]
        return Poll.objects.get(id=current_poll_id)


def handle_polling_end_if_no_qeuestions(user, update: Update, context: CallbackContext):
    update.message.reply_text(
        text=static_text.no_questions_text.format(username=user.username)
    )


def handle_polling_end(user, update: Update, context: CallbackContext):
    user_id = user.user_id
    
    # create new message(thread) in the tgchannel
    # https://docs.python-telegram-bot.org/en/stable/telegram.bot.html#telegram.Bot.send_message
    msg = context.bot.send_message(
        chat_id=settings.ADMIN_FORUM_TGCHANNEL_CHAT_ID,
        text=static_text.polling_info_text.format(username=user.username)
    )

    print('-'*50)
    print(msg)
    print(msg.message_id)
    print(msg.message_thread_id)
    print('-'*50)
    thread_id = msg.message_id
    context.bot.send_message(
        chat_id=settings.ADMIN_FORUM_TGCHANNEL_CHAT_ID,
        text=static_text.polling_info_text.format(username=user.username)
    )

    # TODO: forwarding messages into the tgchannel
    # https://docs.python-telegram-bot.org/en/stable/telegram.bot.html#telegram.Bot.forward_messages
    for msg_id in context.chat_data[CONTROL_DATA_KEY]["forwarding_messages"]:
        context.bot.forward_message(
            chat_id=settings.ADMIN_FORUM_TGCHANNEL_CHAT_ID,
            from_chat_id=user_id,
            message_thread_id=thread_id,
            message_id=msg_id
        )

    update.message.reply_text(
        text=static_text.polling_end_text.format(username=user.username)
    )
    
    context.refresh_data()
