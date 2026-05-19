from aiogram.utils.keyboard import InlineKeyboardBuilder

async def admin_menu_builder(message):
    builder = InlineKeyboardBuilder()

    # Add buttons in pairs (2 per row)
    builder.button(text="📡 Broadcast Message", callback_data="admin_broadcast")
    builder.button(text="👥 Set Admin", callback_data="admin_set_admin")

    builder.button(text="❌ Remove Admin", callback_data="admin_remove_admin")
    builder.button(text="📊 View Stats", callback_data="admin_stats")

    builder.button(text="🚨 Pending Reports", callback_data="admin_reports")
    builder.button(text="📋 Report Stats", callback_data="admin_report_stats")

    builder.button(text="❓ Help", callback_data="admin_help_menu")

    builder.adjust(2)

    await message.answer(
        "👨‍💼 **Admin Control Panel**\n\nSelect an action:", 
        reply_markup=builder.as_markup()
    )

def _build_cancel_button() -> InlineKeyboardBuilder:
    """Build a keyboard with cancel button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="cancel_operation")
    return builder



