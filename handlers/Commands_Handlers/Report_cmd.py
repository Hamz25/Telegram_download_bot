import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


from Logic.utils.report_tracker import save_report, get_pending_reports, mark_report_resolved, get_pending_count
from Logic.admin import is_admin, get_all_admins
from Logic.utils.user_tracker import get_all_user_ids

router = Router()

# FSM States for report handling
class ReportStates(StatesGroup):
    waiting_for_message = State()

# ================================================================================================
# USER REPORT COMMANDS
# ================================================================================================

@router.message(Command("report"))
async def report_command(message: types.Message, state: FSMContext):
    """
    Start the report process.
    User sends /report and is asked to describe the problem.
    """
    await message.answer(
        "📝 **Report a Problem**\n\n"
        "Please describe the issue you encountered:\n"
        "(Your message will be sent to our admins)\n\n"
        "Type your message below:"
    )
    await state.set_state(ReportStates.waiting_for_message)

@router.message(Command("user_help"))
async def user_help(message: types.Message):
    """
    Display user commands with descriptions.
    """
    help_text = (
        "👤 **User Commands**\n\n"
        
        "🚨 **Support & Reporting**\n"
        "`/report` - Report a problem to admins\n"
        "  Send this command and describe your issue\n\n"
        
        "ℹ️ **Information**\n"
        "`/user_help` - Show this help message\n\n"
        
        "---\n\n"
        "**Supported Platforms:**\n"
        "🎵 Spotify - Share a song/album link\n"
        "🎬 YouTube - Share a video link\n"
        "📱 TikTok - Share a video link\n"
        "📸 Instagram - Share stories/reels/posts/highlights\n"
        "🎬 Snapchat - Share video links\n"
    )
    
    await message.answer(help_text)

@router.message(ReportStates.waiting_for_message)
async def receive_report(message: types.Message, state: FSMContext):
    """
    Receive the report message from user.
    Save it and notify admins.
    """
    report_message = message.text.strip()
    
    if not report_message or len(report_message) < 5:
        await message.answer("❌ Please provide a more detailed report (at least 5 characters).")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Save report
    report_id = save_report(user_id, username, report_message)
    
    if not report_id:
        await message.answer("❌ Failed to save report. Please try again later.")
        await state.clear()
        return
    
    # Send confirmation to user
    await message.answer(
        f"✅ Report submitted successfully!\n\n"
        f"📌 Report ID: `{report_id}`\n"
        f"Our admins will review it shortly."
    )
    
    # Send notification to all admins
    admin_ids = get_all_admins()
    
    if admin_ids:
        admin_message = (
            f"🚨 **New Report Received**\n\n"
            f"📌 Report ID: `{report_id}`\n"
            f"👤 From: @{username or 'Unknown'} (ID: {user_id})\n\n"
            f"💬 Message:\n{report_message}\n\n"
            f"Use `/resolve_report {report_id}` to mark as resolved."
        )
        
        for admin_id in admin_ids:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message
                )
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Failed to notify admin {admin_id}: {e}")
    
    await state.clear()

# ================================================================================================
# ADMIN REPORT COMMANDS
# ================================================================================================

@router.message(Command("pending_reports"))
async def view_pending_reports(message: types.Message):
    """
    View all pending reports (admin only).
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return
    
    reports = get_pending_reports()
    
    if not reports:
        await message.answer("✅ No pending reports!")
        return
    
    pending_count = len(reports)
    
    # Build report list
    report_text = f"📋 **Pending Reports ({pending_count})**\n\n"
    
    for idx, report in enumerate(reports[:10], 1):  # Show first 10
        report_text += (
            f"{idx}. 📌 ID: `{report['report_id']}`\n"
            f"   👤 From: @{report['username']}\n"
            f"   💬 {report['message'][:50]}{'...' if len(report['message']) > 50 else ''}\n"
            f"   📅 {report['timestamp']}\n\n"
        )
    
    if pending_count > 10:
        report_text += f"... and {pending_count - 10} more reports"
    
    await message.answer(report_text)

@router.message(Command("resolve_report"))
async def resolve_report_cmd(message: types.Message):
    """
    Resolve a report (admin only).
    Usage: /resolve_report <report_id>
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Usage: /resolve_report <report_id>")
        return
    
    report_id = parts[1]
    admin_response = " ".join(parts[2:]) if len(parts) > 2 else "Report reviewed and resolved"
    
    # Mark as resolved
    if mark_report_resolved(report_id, admin_response):
        await message.answer(f"✅ Report {report_id} marked as resolved!")
    else:
        await message.answer(f"❌ Could not find report {report_id}")

@router.message(Command("report_stats"))
async def report_stats_cmd(message: types.Message):
    """
    View report statistics (admin only).
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return
    
    from Logic.report_tracker import get_pending_count, get_report_count
    
    pending = get_pending_count()
    total = get_report_count()
    resolved = total - pending
    
    stats = (
        f"📊 **Report Statistics**\n\n"
        f"📝 Total Reports: {total}\n"
        f"🔴 Pending: {pending}\n"
        f"🟢 Resolved: {resolved}\n"
    )
    
    await message.answer(stats)
