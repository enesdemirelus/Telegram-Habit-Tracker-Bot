from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
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
    
    await update.message.reply_text(f"Welcome to the Enes' Habit Tracker.\n\nDay = {day_difference}\nNumber of Habits = {number_of_habits}\n\nPlease select what you want to do:\n\n/habit_dashboard\n/add_new_habit\n/delete_habit\n/update_habit")
    
async def habit_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = get_response()
    
    if len(response.data) == 0:
        await update.message.reply_text("You do not have any habit. Pleasea add a new habit below:\n\n /add_new_habit")
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
    await update.message.reply_text("update habit")
    
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
        
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode in ("delete_pick", "delete_confirm"):
        return await handle_delete_message(update, context)

    if mode == "add_new_habit":
        return await handle_add_message(update, context)

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




