from aiogram.fsm.state import StatesGroup, State



class BotStates(StatesGroup):
    choosing_quality = State()
    searching_state = State()
    testing_state = State()

class AdminStates(StatesGroup):
    """Finite State Machine states for admin operations."""

    waiting_for_broadcast = State()
    waiting_for_set_admin = State()
    waiting_for_remove_admin = State()
    waiting_for_resolve_report = State()
