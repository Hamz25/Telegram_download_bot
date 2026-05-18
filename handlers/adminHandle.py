"""
Admin Control Panel Handler
Module for managing admin operations including broadcasts, admin management,
statistics viewing, and report handling.
"""

import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from states.bot_states import AdminStates

from Logic.admin import (
    is_admin,
    add_admin,
    remove_admin,
    get_all_admins,
    is_broadcast_enabled,
)
from Logic.utils.user_tracker import get_all_user_ids, get_user_count
from Logic.utils.report_tracker import (
    get_pending_reports,
    get_pending_count,
    get_report_count,
)

# Router initialization
router = Router()

# ============================================================================
# Helper Functions
# ============================================================================


def _build_cancel_button() -> InlineKeyboardBuilder:
    """Build a keyboard with cancel button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="cancel_operation")
    return builder


async def _check_admin_authorization(
    user_id: int, query: types.CallbackQuery = None, message: types.Message = None
) -> bool:
    """Check if user is authorized as admin and send notification if not."""
    if not is_admin(user_id):
        if query:
            await query.answer("❌ Not authorized", show_alert=True)
        elif message:
            await message.answer("❌ You are not authorized to use this command.")
        return False
    return True


# ============================================================================
# Core Command Handlers
# ============================================================================


@router.message(Command("admin_menu"))
async def admin_menu(message: types.Message):
    """
    Display admin control panel with action buttons.
    
    Shows a menu with buttons for:
    - Broadcasting messages to all users
    - Managing admin privileges
    - Viewing statistics
    - Handling user reports
    - Accessing help
    """
    if not await _check_admin_authorization(message.from_user.id, message=message):
        return

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


# ============================================================================
# Cancel Operation Handler
# ============================================================================


@router.callback_query(F.data == "cancel_operation")
async def cancel_button(query: types.CallbackQuery, state: FSMContext):
    """Cancel current operation and clear FSM state."""
    await state.clear()
    # Delete the message with buttons
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.message.answer("✅ Operation cancelled. Send /admin_menu to start over.")


# ============================================================================
# Broadcast Handlers
# ============================================================================


@router.callback_query(F.data == "admin_broadcast")
async def broadcast_button(query: types.CallbackQuery, state: FSMContext):
    """
    Initiate broadcast message operation.
    
    Transitions to waiting_for_broadcast state to receive message from admin.
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    builder = _build_cancel_button()
    await query.message.answer(
        "📝 Send the message you want to broadcast to all users:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.message(AdminStates.waiting_for_broadcast)
async def receive_broadcast(message: types.Message, state: FSMContext):
    """
    Receive and distribute broadcast message to all users.
    
    Processes message delivery with error handling and reports statistics.
    """
    broadcast_message = message.text.strip()
    
    # Check for cancel
    if broadcast_message.lower() == "cancel":
        await message.answer("✅ Operation cancelled.")
        await state.clear()
        return
    
    user_ids = get_all_user_ids()

    if not user_ids:
        await message.answer("ℹ️ No users to broadcast to.")
        await state.clear()
        return

    # Send status update
    status = await message.answer(
        f"📡 Broadcasting message to {len(user_ids)} user(s)...\n\n"
        f"Message: {broadcast_message}"
    )

    sent = 0
    failed = 0

    # Distribute message to all users
    for user_id in user_ids:
        try:
            await message.bot.send_message(
                chat_id=user_id, 
                text=f"{broadcast_message}"
            )
            sent += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"⚠️ Failed to send to user {user_id}: {e}")
            failed += 1

    # Send final report
    await status.edit_text(
        f"✅ Broadcast complete!\n\n"
        f"📤 Sent: {sent}/{len(user_ids)}\n"
        f"❌ Failed: {failed}"
    )
    print(
        f"[Admin] Broadcast sent by {message.from_user.id} to {sent} users, {failed} failed"
    )
    await state.clear()


# ============================================================================
# Admin Management Handlers
# ============================================================================


@router.callback_query(F.data == "admin_set_admin")
async def set_admin_button(query: types.CallbackQuery, state: FSMContext):
    """
    Initiate admin privilege assignment operation.
    
    Prompts for user ID to promote to admin.
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    builder = _build_cancel_button()
    await query.message.answer(
        "👤 Send the **user ID** you want to make an admin:\n\nExample: `123456789`",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(AdminStates.waiting_for_set_admin)


@router.message(AdminStates.waiting_for_set_admin)
async def receive_set_admin(message: types.Message, state: FSMContext):
    """
    Process user ID and grant admin privileges.
    
    Validates input and adds user to admin list.
    """
    if message.text.lower() == "cancel":
        await message.answer("✅ Operation cancelled.")
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Invalid user ID. Send only numbers, or type 'cancel' to exit."
        )
        return

    if add_admin(user_id):
        await message.answer(f"✅ User {user_id} is now an admin!")
        print(f"[Admin] User {user_id} promoted to admin by {message.from_user.id}")
    else:
        await message.answer(f"ℹ️ User {user_id} is already an admin.")

    await state.clear()


@router.callback_query(F.data == "admin_remove_admin")
async def remove_admin_button(query: types.CallbackQuery, state: FSMContext):
    """
    Initiate admin privilege removal operation.
    
    Prompts for user ID to demote from admin.
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    builder = _build_cancel_button()
    await query.message.answer(
        "👤 Send the **user ID** you want to remove from admins:\n\nExample: `123456789`",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(AdminStates.waiting_for_remove_admin)


@router.message(AdminStates.waiting_for_remove_admin)
async def receive_remove_admin(message: types.Message, state: FSMContext):
    """
    Process user ID and remove admin privileges.
    
    Validates input and removes user from admin list.
    """
    if message.text.lower() == "cancel":
        await message.answer("✅ Operation cancelled.")
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Invalid user ID. Send only numbers, or type 'cancel' to exit."
        )
        return

    if remove_admin(user_id):
        await message.answer(f"✅ User {user_id} is no longer an admin!")
        print(f"[Admin] User {user_id} removed from admins by {message.from_user.id}")
    else:
        await message.answer(f"ℹ️ User {user_id} is not an admin.")

    await state.clear()


# ============================================================================
# Statistics Handlers
# ============================================================================


@router.callback_query(F.data == "admin_stats")
async def stats_button(query: types.CallbackQuery):
    """
    Display overall bot statistics.
    
    Shows:
    - Total user count
    - Total admin count
    - Broadcast status
    - List of all admin IDs
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    total_users = get_user_count()
    admins = get_all_admins()
    broadcast_status = "🟢 Enabled" if is_broadcast_enabled() else "🔴 Disabled"

    admin_list_str = ", ".join(str(uid) for uid in admins) if admins else "None"

    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"👨‍💼 Total Admins: {len(admins)}\n"
        f"📡 Broadcast Status: {broadcast_status}\n\n"
        f"**Admin IDs:**\n{admin_list_str}"
    )

    await query.message.answer(stats_text)


@router.callback_query(F.data == "admin_report_stats")
async def report_stats_button(query: types.CallbackQuery):
    """
    Display report handling statistics.
    
    Shows:
    - Total reports received
    - Pending reports
    - Resolved reports
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    pending = get_pending_count()
    total = get_report_count()
    resolved = total - pending

    stats_text = (
        f"📊 **Report Statistics**\n\n"
        f"📝 Total Reports: {total}\n"
        f"🔴 Pending: {pending}\n"
        f"🟢 Resolved: {resolved}\n"
    )

    await query.message.answer(stats_text)


# ============================================================================
# Report Handlers
# ============================================================================


@router.callback_query(F.data == "admin_reports")
async def reports_button(query: types.CallbackQuery):
    """
    Display pending user reports.
    
    Shows the first 5 pending reports with:
    - Report ID
    - Username
    - Message preview (truncated to 50 chars)
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    reports = get_pending_reports()

    if not reports:
        await query.message.answer("✅ No pending reports!")
        return

    pending_count = len(reports)
    report_text = f"📋 **Pending Reports ({pending_count})**\n\n"

    for idx, report in enumerate(reports[:5], 1):
        message_preview = report["message"][:50]
        if len(report["message"]) > 50:
            message_preview += "..."

        report_text += (
            f"{idx}. 📌 ID: `{report['report_id']}`\n"
            f"   👤 @{report['username']}\n"
            f"   💬 {message_preview}\n\n"
        )

    if pending_count > 5:
        report_text += f"... and {pending_count - 5} more reports"

    await query.message.answer(report_text)


# ============================================================================
# Help Handler
# ============================================================================


@router.callback_query(F.data == "admin_help_menu")
async def help_menu_button(query: types.CallbackQuery):
    """
    Display comprehensive help documentation for admin commands.
    
    Lists all available admin features with descriptions.
    """
    if not await _check_admin_authorization(query.from_user.id, query=query):
        return
    
    # Delete the button message
    try:
        await query.message.delete()
    except Exception:
        pass

    help_text = (
        "👨‍💼 **Admin Commands Help**\n\n"
        "📡 **Broadcast** - Send a message to all users at once\n\n"
        "👥 **Set Admin** - Promote a user to admin status (requires user ID)\n\n"
        "❌ **Remove Admin** - Remove admin privileges from a user\n\n"
        "📊 **View Stats** - Display bot statistics and admin list\n\n"
        "🚨 **Pending Reports** - View all pending user reports\n\n"
        "📋 **Report Stats** - View report handling statistics\n\n"
        "💡 **Tip:** Use `/admin_menu` to open this panel anytime!"
    )

    await query.message.answer(help_text)