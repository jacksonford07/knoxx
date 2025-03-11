from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio
import signal
from telegram.error import Conflict
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables or .env file is missing.")
logger.info("Bot token loaded successfully")

# Global application variable
application = None

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    if application:
        logger.info("Stopping application...")
        asyncio.create_task(application.stop())
    
# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# States
AWAITING_FIRST_ANSWER = 1
AWAITING_SECOND_ANSWER = 2
FOLLOW_UP = 3

def get_yes_no_keyboard():
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data="yes"),
        InlineKeyboardButton("No", callback_data="no")
    ]]
    return InlineKeyboardMarkup(keyboard)

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command through callback."""
    keyboard = get_yes_no_keyboard()
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Do you have chatting experience?",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            "Do you have chatting experience?",
            reply_markup=keyboard
        )
    return AWAITING_FIRST_ANSWER

async def handle_first_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Processing...")
    
    if query.data != "yes":
        await query.message.reply_text(
            "I'm sorry, but this role requires prior chatting experience. Thank you for your interest!"
        )
        return ConversationHandler.END
    
    await query.message.reply_text(
        "Are you available for 5-7 days per week for 8-hour shifts?",
        reply_markup=get_yes_no_keyboard()
    )
    return AWAITING_SECOND_ANSWER

async def handle_second_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Processing...")
    
    if query.data != "yes":
        await query.message.reply_text(
            "I'm sorry, but this role requires availability for 5-7 days per week. Thank you for your interest!"
        )
        return ConversationHandler.END
    
    await query.message.reply_text(
        "Great! Here's the form to fill out: "
        "https://docs.google.com/forms/d/e/1FAIpQLSdxTqaq4dCHuIdnV1e3m9oBLlaPWiZV1Qx-Q_0yrmuYmFtK5A/viewform?usp=sharing"
    )
    
    # Set a follow-up reminder in 24 hours
    user_id = query.from_user.id
    context.job_queue.run_once(follow_up_message, 86400, chat_id=user_id, name=str(user_id))
    return ConversationHandler.END

async def follow_up_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.send_message(
            chat_id=job.chat_id,
            text="Hey! Just a reminder to fill out the application form if you haven't already: "
            "https://docs.google.com/forms/d/e/1FAIpQLSdxTqaq4dCHuIdnV1e3m9oBLlaPWiZV1Qx-Q_0yrmuYmFtK5A/viewform?usp=sharing"
        )
    except Exception as e:
        logger.error(f"Error sending follow-up message: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error occurred: {context.error}")
    if isinstance(context.error, Conflict):
        logger.error("Bot conflict detected. Make sure no other instances are running!")

async def main():
    """Run the bot."""
    global application
    
    try:
        # Build application
        logger.info("Building application...")
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Application built successfully")

        # Add handlers
        logger.info("Setting up conversation handler...")
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_callback)],
            states={
                AWAITING_FIRST_ANSWER: [CallbackQueryHandler(handle_first_answer)],
                AWAITING_SECOND_ANSWER: [CallbackQueryHandler(handle_second_answer)],
            },
            fallbacks=[CommandHandler('start', start_callback)],
            per_chat=True,
            per_user=True
        )
        
        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)
        logger.info("Handlers added successfully")

        logger.info("Starting bot polling...")
        
        # Run the bot with minimal settings and proper shutdown
        await application.initialize()
        await application.start()
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            pool_timeout=30,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        if application:
            await application.stop()
        raise e

if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main loop error: {e}", exc_info=True)
        raise e
