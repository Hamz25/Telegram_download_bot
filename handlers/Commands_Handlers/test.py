from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from Logic.Logger import logger
from states.bot_states import BotStates
import os


from languages import get_text  


router = Router()
test_password = os.getenv("TEST_PASSWORD")


@router.message(lambda message: message.text and message.text.startswith(f"/test_{test_password}"))
async def test_cmd(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.testing_state) #it will set the state of the bot to testing state so we can only use the test code only by activating the test state