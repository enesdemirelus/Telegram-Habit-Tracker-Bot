from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, date
from zoneinfo import ZoneInfo


load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT")
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_response():
    response = (
    supabase.table("Habits")
    .select("*")
    .execute()
)
    return response

def day_calculator():
    beginning_date = datetime(2025, 12, 24, tzinfo=ZoneInfo("America/Chicago"))
    now = datetime.now(ZoneInfo("America/Chicago"))
    day_difference = (now.date() - beginning_date.date()).days
    return day_difference

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    number_of_habits = len(response.data)
    day_difference = day_calculator()
    
    await update.message.reply_text(f"Welcome to the Enes' Habit Tracker.\n\nDay = {day_difference}\nNumber of Habits = {number_of_habits}\n\nPlease select what you want to do:\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit\n/update_streak")
    
async def habit_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    
    if len(response.data) == 0:
        await update.message.reply_text("You do not have any habit. Please add a new habit below:\n\n /add_new_habit")
    else:
        
        lines = ["Here is the dashboard of your habits 💪", ""]

        for i, habit in enumerate(response.data, start=1):
            if habit["habit_structure"] == "weekly":
                line = f"[{i}]: {habit['habit_name']} - {habit['weekly_streak']}/{habit['week_goal']}"
            else:
                line = f"[{i}]: {habit['habit_name']} - {habit['streak']}"

            lines.append(line)

        habit_dashboard = "\n".join(lines)
        await update.message.reply_text(habit_dashboard)
        
        
async def update_streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "select_update_streak"
    response = get_response()
    
    lines = ["Here is all of your habits, please choose which one you want to update the streak of", ""]
    
    for i, habit in enumerate(response.data, start=1):
        if habit["habit_structure"] == "weekly":
            line = f"[{i}]: {habit['habit_name']} - {habit['weekly_streak']}/{habit['week_goal']}"
        else:
            line = f"[{i}]: {habit['habit_name']} - {habit['streak']}"

        lines.append(line)

    habit_dashboard = "\n".join(lines)
    await update.message.reply_text(habit_dashboard)
    
    
    
async def add_new_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "add_new_habit"
    
    await update.message.reply_text(
        "📝 **Add a New Habit**\n\n"
        "Please enter your habit in the following format without bullet points:\n\n"
        "• **Habit Name**\n"
        "• **weekly** or **daily**\n"
        "• **Weekly goal** (only if weekly)\n\n",
        parse_mode="Markdown"
)
    
    
async def handle_update_streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    mode = context.user_data.get("mode")
    text = (update.message.text or "").strip()
    
    if mode == "select_update_streak":
        if not text.isdigit():
            await update.message.reply_text("Please reply with a number.")
            return
        
        selected = int(text) - 1
        if selected < 0 or selected >= len(response.data):
            await update.message.reply_text("Invalid number. Please pick a habit number from the list.")
            return
        
        habit = response.data[selected]
        context.user_data["mode"] = "update_streak_context"
        context.user_data["habit_to_update"] = habit
        
        await update.message.reply_text(
            f"What do you want to update the streak to: {habit['habit_name']}\n\n[1] Increase One\n[2] Decrease One\n[3] Increase Custom\n[4] Reset"
        )
        return
    
    if mode == "update_streak_context":
        habit = context.user_data["habit_to_update"]
        
        
        

    
async def handle_add_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    text = (update.message.text or "").strip()
    
    if mode == "add_new_habit":
        lines = text.splitlines()
        lines = [l.strip() for l in text.splitlines() if l.strip()]

                
        if lines[1].lower() == "weekly":
            response = (
                supabase.table("Habits")
                .insert({
                    "habit_name": lines[0],
                    "habit_structure": "weekly",
                    "week_goal": int(lines[2])
                })
                .execute()
            )

        if lines[1].lower() == "daily":
            response = (
                supabase.table("Habits")
                .insert({
                    "habit_name": lines[0],
                    "habit_structure": "daily"
                })
                .execute()
            )
                
        await update.message.reply_text(
            f"A new habit has been added to your Habit Tracker:\n\n{lines[0]}\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
        )
    
    context.user_data.pop("mode", None)
            
async def update_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    context.user_data["mode"] = "update_pick"
    
    lines = ["Here is all of your habits, please choose which one you want to update", ""]
    
    for i, habit in enumerate(response.data, start=1):
        if habit["habit_structure"] == "weekly":
            line = f"[{i}]: {habit['habit_name']} - {habit['weekly_streak']}/{habit['week_goal']}"
        else:
            line = f"[{i}]: {habit['habit_name']} - {habit['streak']}"

        lines.append(line)

    habit_dashboard = "\n".join(lines)
    await update.message.reply_text(habit_dashboard)
         
    
async def delete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    context.user_data["mode"] = "delete_pick"
    
    lines = ["Here is all of your habits, please choose which one you want to delete", ""]

    for i, habit in enumerate(response.data, start=1):
        if habit["habit_structure"] == "weekly":
            line = f"[{i}]: {habit['habit_name']} - {habit['weekly_streak']}/{habit['week_goal']}"
        else:
            line = f"[{i}]: {habit['habit_name']} - {habit['streak']}"

        lines.append(line)

    habit_dashboard = "\n".join(lines)
    await update.message.reply_text(habit_dashboard)
    
async def handle_delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()

    mode = context.user_data.get("mode")
    text = (update.message.text or "").strip().lower()
    
    if mode == "delete_pick":    
        if not text.isdigit():
            await update.message.reply_text("Please reply with a number.")
            return
        
        selected = int(text) - 1
        if selected < 0 or selected >= len(response.data):
            await update.message.reply_text("Invalid number. Please pick a habit number from the list.")
            return
        
        habit = response.data[selected]
        context.user_data["mode"] = "delete_confirm"
        context.user_data["habit_to_delete"] = habit
        
        await update.message.reply_text(
            f"Are you sure you want to delete: \n\n{habit['habit_name']}\n\nReply with yes or no."
        )
        return
    
    if mode == "delete_confirm":
        habit = context.user_data["habit_to_delete"]
        
        if text == "yes":
            new_response = (
                supabase.table("Habits")
                .delete()
                .eq("habit_name", habit['habit_name'])
                .execute()
            )
            
            await update.message.reply_text(
                f"🗑️ Deleted: {habit['habit_name']}\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
            )
        else:
            await update.message.reply_text(f"❌ Delete cancelled.\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit")

    
    context.user_data.pop("mode", None)
        

async def handle_update_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    
    mode = context.user_data.get("mode")
    text = (update.message.text or "").strip().lower()
    
    if mode == "update_pick":
        if not text.isdigit():
            await update.message.reply_text("Please reply with a number.")
            return
        
        selected = int(text) - 1
        if selected < 0 or selected >= len(response.data):
            await update.message.reply_text("Invalid number. Please pick a habit number from the list.")
            return
        
        habit = response.data[selected]
        context.user_data["mode"] = "update_context"
        context.user_data["habit_to_update"] = habit
        
        await update.message.reply_text(
            f"What do you want to update about: {habit['habit_name']}\n\n[1] Habit Name\n[2] Habit Structure\n[3] Weekly Goal\n[4] Reset the streak (Weekly or All)"
        )
        return
    
    if mode == "update_context":
        habit = context.user_data["habit_to_update"]
        
        if text == "1":
            context.user_data["mode"] = "update_name"
            await update.message.reply_text(
                f"Enter the new name for the habit:\n\nCurrent: {habit['habit_name']}"
            )
            return

        elif text == "2":
            context.user_data["mode"] = "update_structure"
            await update.message.reply_text(
                "⚠️ Changing habit structure will RESET ALL STREAKS.\n\n"
                "Pick the new habit structure:\n\n"
                "[1] Weekly\n"
                "[2] Daily"
            )
            return

        elif text == "3":
            if habit["habit_structure"] != "weekly":
                await update.message.reply_text(
                    "❌ Daily habits do not have a goal.\n\n"
                    "Only weekly habits can have a goal updated.\n\n"
                    "/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
                )
                context.user_data.pop("mode", None)
                return

            context.user_data["mode"] = "update_goal"
            await update.message.reply_text(
                "This habit is currently **WEEKLY**.\n\n"
                "Pick a new weekly goal (0 to 7):",
                parse_mode="Markdown"
            )
            return

        elif text == "4":
            context.user_data["mode"] = "reset_streak_confirm"
            await update.message.reply_text(
                "⚠️ This will RESET the streak for this habit.\n\n"
                "Are you sure?\n\n"
                "Reply with: yes or no"
            )
            return

            
    if mode == "update_name":
        habit = context.user_data["habit_to_update"]
        new_name = update.message.text.strip()

        if not new_name:
            await update.message.reply_text("Habit name cannot be empty. Please enter a valid name.")
            return

        supabase.table("Habits").update({"habit_name": new_name}).eq("habit_name", habit['habit_name']).execute()

        await update.message.reply_text(
            f"Name of the habit:\n\n{habit['habit_name']} ➜ {new_name}\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
        )

        context.user_data.pop("mode", None)


    elif mode == "update_structure":
        habit = context.user_data["habit_to_update"]

        if text not in ("1", "2"):
            await update.message.reply_text("Please reply with 1 (Weekly) or 2 (Daily).")
            return

        new_structure = "weekly" if text == "1" else "daily"
        update_data = {"habit_structure": new_structure, "streak": 0, "weekly_streak": 0, "week_goal": 3 if new_structure == "weekly" else None}
        supabase.table("Habits").update(update_data).eq("habit_name", habit['habit_name']).execute()

        await update.message.reply_text(
            f"Habit structure will change from {habit['habit_structure']} ➜ {new_structure}.\n\nAll streaks will be reset.\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
        )

        context.user_data.pop("mode", None)


    elif mode == "update_goal":
        habit = context.user_data["habit_to_update"]

        if not text.isdigit():
            await update.message.reply_text("Please enter a valid number.")
            return

        new_goal = int(text)

        if new_goal < 0:
            await update.message.reply_text("Goal cannot be less than 0.")
            return

        if habit["habit_structure"] == "weekly" and new_goal > 7:
            await update.message.reply_text("Weekly goal cannot be more than 7.")
            return

        supabase.table("Habits").update({"week_goal": new_goal}).eq("habit_name", habit['habit_name']).execute()

        await update.message.reply_text(
            f"New goal set for {habit['habit_name']}:\n\n{new_goal}\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
        )

        context.user_data.pop("mode", None)


    elif mode == "reset_streak_confirm":
        habit = context.user_data["habit_to_update"]

        if text not in ("yes", "no"):
            await update.message.reply_text("Please reply with yes or no.")
            return

        if text == "yes":
            supabase.table("Habits").update({"streak": 0, "weekly_streak": 0}).eq("habit_name", habit['habit_name']).execute()
            await update.message.reply_text(
                f"Streak for {habit['habit_name']} has been reset.\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit"
            )
        else:
            await update.message.reply_text(f"Reset cancelled.\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit")

        context.user_data.pop("mode", None)

        

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode in ("delete_pick", "delete_confirm"):
        return await handle_delete_message(update, context)

    if mode == "add_new_habit":
        return await handle_add_message(update, context)
    
    if mode in ("update_pick", "update_context", "update_name", "update_structure", "update_goal", "reset_streak_confirm"):
        return await handle_update_message(update, context)

    return
    

    
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("habit_dashboard", habit_dashboard))
    app.add_handler(CommandHandler("add_new_habit", add_new_habit))
    app.add_handler(CommandHandler("delete_habit", delete_habit))
    app.add_handler(CommandHandler("update_habit", update_habit))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
        

main()




