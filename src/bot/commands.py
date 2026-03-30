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

# Callback for Custom Post – start collection
async def handle_custom_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Use effective_user.id for most reliable ID
    user_id = update.effective_user.id
    
    try:
        # Reset session for custom post
        user_data = state.get_user_data(user_id)
        user_data["mode"] = "collect_custom"
        user_data["desc"] = ""
        user_data["photos"] = []
        state.set_user_data(user_id, user_data)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "CUSTOM POST MODE\n\n"
                "Please send reference images (max 5) or text content now.\n"
                "You can send multiple items. Click 'Submit & Generate' when finished."
            )
        )
    except Exception as e:
        import logging
        logging.error(f"Error in handle_custom_post: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"Error: {str(e)}")

# Message handler for text and images during collection
async def handle_custom_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = state.get_user_data(user_id)
    
    if user_data.get("mode") != "collect_custom":
        await start(update, context)
        return

    try:
        if update.message.text:
            user_data["desc"] = update.message.text
            await context.bot.send_message(chat_id=user_id, text="Text received.")
        
        elif update.message.photo:
            if len(user_data["photos"]) >= 5:
                await context.bot.send_message(chat_id=user_id, text="Max 5 photos.")
            else:
                photo = update.message.photo[-1]
                file = await photo.get_file()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_path = temp_file.name
                temp_file.close()
                try:
                    await file.download_to_drive(custom_path=temp_path)
                    from src.bot.cloudinary_uploader import CloudinaryUploader
                    url = CloudinaryUploader.upload_file(temp_path)
                    user_data["photos"].append(url)
                    await context.bot.send_message(chat_id=user_id, text=f"Photo {len(user_data['photos'])}/5 received.")
                finally:
                    if os.path.exists(temp_path): os.remove(temp_path)

        state.set_user_data(user_id, user_data)
        
        keyboard = [[InlineKeyboardButton("Submit & Generate", callback_data="SUBMIT_CUSTOM")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="Click below to finish:", reply_markup=reply_markup)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"Input Error: {str(e)}")

# Callback for Submit button
async def handle_submit_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_data = state.get_user_data(user_id)
    
    if not user_data.get("desc") and not user_data.get("photos"):
        await context.bot.send_message(chat_id=user_id, text="Please provide content first.")
        return
        
    await context.bot.send_message(chat_id=user_id, text="Generating your post preview...")
    await send_custom_drafts(update, context)

async def send_custom_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Use trigger originating update (could be query or message)
    chat_id = update.effective_chat.id
    user_data = state.get_user_data(chat_id)
    
    desc = user_data.get("desc", "")
    photos = user_data.get("photos", [])
    
    try:
        import asyncio
        drafts = await asyncio.to_thread(generate_custom_previews, desc, photos)
        for draft in drafts:
            media = []
            for idx, url in enumerate(draft["media_urls"]):
                caption = draft["caption"] if idx == 0 else ""
                media.append(InputMediaPhoto(media=url, caption=caption))
            
            button = InlineKeyboardButton("🚀 Post to IG", callback_data=f"POST|{draft['uuid']}")
            reply_markup = InlineKeyboardMarkup([[button]])
            
            # Application of the preview message
            if len(media) > 1:
                await context.bot.send_media_group(chat_id=chat_id, media=media)
            else:
                await context.bot.send_photo(chat_id=chat_id, photo=media[0].media, caption=media[0].caption)
                
            await context.bot.send_message(chat_id=chat_id, text=f"Final Preview (Ghost-Safe):", reply_markup=reply_markup)
            
        # Reset mode
        user_data["mode"] = "idle"
        state.set_user_data(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text="✅ Generation complete! Check the previews above.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error generating drafts: {str(e)}")

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
            await query.message.reply_text(f"✅ Published successfully!\nMedia: IG_{media_id}", parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to publish: {str(e)}")

def register_handlers(app):
    # CallbackQuery handlers MUST come first to ensure buttons are caught
    app.add_handler(CallbackQueryHandler(handle_custom_post, pattern="^CUSTOM_POST$"))
    app.add_handler(CallbackQueryHandler(handle_get_posts, pattern="^GET_POSTS$"))
    app.add_handler(CallbackQueryHandler(handle_submit_custom, pattern="^SUBMIT_CUSTOM$"))
    app.add_handler(CallbackQueryHandler(handle_publish, pattern=r"^POST\|"))
    
    # Commands and Messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_custom_input))
