from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
import logging
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
    raise ValueError("No BOT_TOKEN found in environment variables")
logger.info("Bot token loaded successfully")

# States
AWAITING_FIRST_ANSWER = 1
AWAITING_SECOND_ANSWER = 2

def get_yes_no_keyboard():
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data="yes"),
        InlineKeyboardButton("No", callback_data="no")
    ]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation."""
    keyboard = get_yes_no_keyboard()
    await update.message.reply_text(
        "Do you have chatting experience?",
        reply_markup=keyboard
    )
    return AWAITING_FIRST_ANSWER

async def handle_first_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the first answer."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "no":
        await query.message.reply_text(
            "I'm sorry, but this role requires prior chatting experience. Thank you for your interest!"
        )
        return ConversationHandler.END
    
    keyboard = get_yes_no_keyboard()
    await query.message.reply_text(
        "Are you available for 5-7 days per week for 8-hour shifts?",
        reply_markup=keyboard
    )
    return AWAITING_SECOND_ANSWER

async def handle_second_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the second answer."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "no":
        await query.message.reply_text(
            "I'm sorry, but this role requires availability for 5-7 days per week. Thank you for your interest!"
        )
        return ConversationHandler.END
    
    await query.message.reply_text(
        "Great! Here's the form to fill out: "
        "https://docs.google.com/forms/d/e/1FAIpQLSdxTqaq4dCHuIdnV1e3m9oBLlaPWiZV1Qx-Q_0yrmuYmFtK5A/viewform?usp=sharing\n\n"
        "I'll send you a reminder in 24 hours if you haven't filled it out yet!"
    )
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Error occurred: {context.error}")

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_FIRST_ANSWER: [CallbackQueryHandler(handle_first_answer)],
            AWAITING_SECOND_ANSWER: [CallbackQueryHandler(handle_second_answer)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
