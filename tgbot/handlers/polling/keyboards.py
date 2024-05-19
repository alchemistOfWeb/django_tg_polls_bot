from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.polling.manage_data import QUESTION_CHOICE_BTN_PRFX
# from tgbot.handlers.onboarding.static_text import secret_level_button_text
from polls.models import Question


def make_keyboard_for_question(question:Question) -> InlineKeyboardMarkup:
    buttons = []

    for choice in question.choices:
        btn = InlineKeyboardButton(
            choice.text, callback_data=f'{QUESTION_CHOICE_BTN_PRFX}-{choice.id}')
        buttons.append([btn])
        
    return InlineKeyboardMarkup(buttons)
