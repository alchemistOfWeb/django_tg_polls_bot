from django.utils import timezone
from django.conf import settings

import datetime
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.polling import static_text
from tgbot.handlers.polling.keyboards import make_keyboard_for_question
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User
from polls.models import Poll, Answer


CONTROL_DATA_KEY = 'control_data'
QUESTION_INDEX_KEY = 'current_question'
QUESTIONS_NUM_KEY = 'questions_num'
POLL_ID_KEY = "poll_id"
INPUT_DATA_KEY = "input_data"
ANSWERS_KEY = "answers"


def command_start(update: Update, context: CallbackContext) -> None:
    user, created = User.get_user_and_created(update, context)

    first_active_poll = Poll.objects.filter(active=True).first()
    questions_num = first_active_poll.questions.count()
    current_question_ind = 0

    if current_question_ind >= questions_num:
        handle_polling_end(user, update, context)
        return

    context.chat_data[INPUT_DATA_KEY][POLL_ID_KEY] = first_active_poll.id
    context.chat_data[CONTROL_DATA_KEY][QUESTIONS_NUM_KEY] = questions_num
    context.chat_data[INPUT_DATA_KEY][ANSWERS_KEY] = []
    first_question = first_active_poll.questions.order_by('order')[current_question_ind]
    
    current_question_ind +=1
    context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY] = current_question_ind
    
    # send first question
    update.message.reply_text(
        text=first_question.text,
        reply_markup=make_keyboard_for_question(first_question)
    )


def question_handling(update: Update, context: CallbackContext) -> None:
    # callback_data: {QUESTION_CHOICE_BTN_PRFX}-{choice.id}
    # get some args and params and anwer handling:
    user_id = extract_user_data_from_update(update)['user_id']
    query = update.callback_query
    query.answer()
    callback_data = query.data
    choice_id = int(callback_data.split('-')[1])
    prev_question_id = ...

    # set answer id with choice id in answers list in chat_data
    current_question_ind = context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY]
    
    context.chat_data[INPUT_DATA_KEY][ANSWERS_KEY].append({
        "question": prev_question_id, 
        "choice": choice_id
    })

    # get poll
    current_poll_id = context.chat_data[INPUT_DATA_KEY][POLL_ID_KEY]
    current_poll = Poll.objects.get(id=current_poll_id)

    # check if current_question_ind more than limit
    quations_limit = context.chat_data[CONTROL_DATA_KEY][QUESTIONS_NUM_KEY]
    if current_question_ind >= quations_limit:
        handle_polling_end(update, context)
        return

    # send new question
    question = current_poll.questions.order_by('order')[current_question_ind]
    current_question_ind +=1
    context.chat_data[CONTROL_DATA_KEY][QUESTION_INDEX_KEY] = current_question_ind

    context.bot.send_message(
        chat_id=user_id,
        text=question.text,
        reply_markup=make_keyboard_for_question(question),
        parse_mode=ParseMode.HTML
    )


def handle_polling_end_if_no_qeuestions(user, update: Update, context: CallbackContext):
    update.message.reply_text(
        text=static_text.no_questions_text.format(username=user.username)
    )


def handle_polling_end(user, update: Update, context: CallbackContext):
    user_id = extract_user_data_from_update(update)['user_id']
    # TODO: forwarding messages into the tgchannel...

    # create new message(thread) in the tgchannel
    # https://docs.python-telegram-bot.org/en/stable/telegram.bot.html#telegram.Bot.send_message
    msg = context.bot.send_message(
        chat_id=settings.ADMIN_FORUM_TGCHANNEL_CHAT_ID, 
        text="hello"
    )
    thread_id = msg.id
    # forwarding messages into the tgchannel
    # https://docs.python-telegram-bot.org/en/stable/telegram.bot.html#telegram.Bot.forward_messages
    context.bot.forward_messages(
        chat_id=settings.ADMIN_FORUM_TGCHANNEL_CHAT_ID,
        from_chat_id=user_id,
        message_thread_id=thread_id,
        message_ids=[]
    )

    update.message.reply_text(
        text=static_text.polling_end_text.format(username=user.username)
    )

    context.refresh_data()
