"""FSM-состояния для админ-хендлеров."""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_reply = State()
