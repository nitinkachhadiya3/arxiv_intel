import uuid
import tempfile
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from src.bot.core import get_fresh_previews, generate_custom_previews, publish_selected
from src.bot.state import state
from src.bot.config import Config

# /start command – shows two main options
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Get Posts", callback_data="GET_POSTS")],
        [InlineKeyboardButton("Custom Post", callback_data="CUSTOM_POST")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to ArxivIntel Bot! Choose an action:", reply_markup=reply_markup)

# Callback for Get Posts
async def handle_get_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("🔄 Fetching fresh posts for you...")
    
    try:
        previews = get_fresh_previews()
        for preview in previews:
            media = []
            for idx, url in enumerate(preview["media_urls"]):
                # Adding caption to the first image of the media group
                caption = preview["caption"] if idx == 0 else ""
                media.append(InputMediaPhoto(media=url, caption=caption))
            
            # Add a button to publish this preview
            button = InlineKeyboardButton("🚀 Post to IG", callback_data=f"POST|{preview['uuid']}")
            reply_markup = InlineKeyboardMarkup([[button]])
            await query.message.reply_media_group(media=media)
            # Send the button separately or find a way to attach it (Telegram media groups don't support reply_markup on the whole group easily in some versions, but let's try sending a follow-up message)
            await query.message.reply_text(f"Action for post above:", reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(f"❌ Error fetching posts: {str(e)}")

# Callback for Custom Post – start description collection
async def handle_custom_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    # Initialize state for this chat if not present
    if chat_id not in state:
        state[chat_id] = {"mode": "idle", "desc": "", "photos": []}
        
    state[chat_id]["mode"] = "await_desc"
    await query.message.reply_text("✍️ Please send a short description for your custom post.")

# Message handler for description (when awaiting)
async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if state.get(chat_id, {}).get("mode") == "await_desc":
        state[chat_id]["desc"] = update.message.text
        state[chat_id]["photos"] = []
        state[chat_id]["mode"] = "await_photos"
        await update.message.reply_text("📸 Great! Now send up to 5 photos (one per message).\n\nWhen you are finished, send /done.")

# Photo handler – store uploaded photo URLs via Cloudinary
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if state.get(chat_id, {}).get("mode") == "await_photos":
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        
        # Download to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            await file.download_to_drive(custom_path=temp_path)
            
            # Upload to Cloudinary
            from src.bot.cloudinary_uploader import CloudinaryUploader
            url = CloudinaryUploader.upload_file(temp_path)
            
            state[chat_id]["photos"].append(url)
            count = len(state[chat_id]["photos"])
            await update.message.reply_text(f"✅ Photo {count}/5 uploaded.")
            
            if count >= 5:
                await update.message.reply_text("✨ Maximum of 5 photos reached. Generating drafts...")
                await send_custom_drafts(update, context)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

# /done command to finish photo collection
async def finish_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if state.get(chat_id, {}).get("mode") == "await_photos":
        if not state[chat_id]["photos"]:
            await update.message.reply_text("⚠️ Please send at least one photo or use /start to cancel.")
            return
        await update.message.reply_text("✨ Generating custom drafts based on your input...")
        await send_custom_drafts(update, context)

async def send_custom_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    desc = state[chat_id].get("desc", "")
    photos = state[chat_id].get("photos", [])
    
    try:
        drafts = generate_custom_previews(desc, photos)
        for draft in drafts:
            media = []
            for idx, url in enumerate(draft["media_urls"]):
                caption = draft["caption"] if idx == 0 else ""
                media.append(InputMediaPhoto(media=url, caption=caption))
            
            button = InlineKeyboardButton("🚀 Post to IG", callback_data=f"POST|{draft['uuid']}")
            reply_markup = InlineKeyboardMarkup([[button]])
            await update.message.reply_media_group(media=media)
            await update.message.reply_text(f"Action for draft above:", reply_markup=reply_markup)
            
        # Reset mode but keep state for IDs until published (or handled differently)
        state[chat_id]["mode"] = "idle"
        await update.message.reply_text("✅ Drafts generated! Click 'Post to IG' to publish.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating drafts: {str(e)}")

# Callback for publishing a selected preview/draft
async def handle_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("POST|"):
        preview_uuid = data.split("|", 1)[1]
        await query.message.reply_text("📡 Publishing to Instagram... (Ghost-Safe mode active)")
        
        try:
            result = publish_selected(preview_uuid)
            media_id = result.get('instagram_media_id', 'Success')
            await query.message.reply_text(f"✅ Post published successfully!\nMedia ID: `{media_id}`", parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to publish: {str(e)}")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_get_posts, pattern="^GET_POSTS$"))
    app.add_handler(CallbackQueryHandler(handle_custom_post, pattern="^CUSTOM_POST$"))
    app.add_handler(CallbackQueryHandler(handle_publish, pattern="^POST\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("done", finish_photos))
