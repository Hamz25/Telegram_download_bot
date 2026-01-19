from aiogram import types

async def _delete_message_safely(message: types.Message):
    """
    Safely delete a message without raising exceptions.
    
    IMPORTANT: This ensures all button messages are deleted after interaction.
    """
    try:
        await message.delete()
    except Exception as e:
        print(f"[Handler] Could not delete message: {e}")


async def _handle_download_error(
    message_source: types.Message | types.CallbackQuery,
    lang: str,
    error: Exception,
    status_msg: types.Message = None,
):
    """Centralized error handling for downloads."""
    print(f"[Download] Error: {error}")
    import traceback
    traceback.print_exc()

    # Delete status message if present
    if status_msg:
        await _delete_message_safely(status_msg)

    error_msg = get_text("error_general", lang).format(e=str(error)[:200])
    
    if isinstance(message_source, types.CallbackQuery):
        await message_source.message.answer(error_msg)
    else:
        await message_source.answer(error_msg)
