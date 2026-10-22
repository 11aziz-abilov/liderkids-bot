from aiogram.fsm.state import State, StatesGroup

class LinkChildState(StatesGroup):
    waiting_for_code = State()

class PaymentState(StatesGroup):
    waiting_for_receipt = State()
