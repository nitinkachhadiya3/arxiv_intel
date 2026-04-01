import uuid
import tempfile
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from src.bot.core import get_fresh_previews, generate_custom_previews, publish_selected
from src.bot.sports_core import generate_sports_previews
from src.bot.state import state
from src.bot.config import Config

# /start command – shows main options including sports
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 Get AI/Tech Posts", callback_data="GET_POSTS")],
        [InlineKeyboardButton("✏️ Custom Post", callback_data="CUSTOM_POST")],
        [InlineKeyboardButton("🏏 Live Match Post (IPL)", callback_data="MATCH_POST")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏆 Welcome to ArxivIntel Creative Bot!\n\nChoose an action:",
        reply_markup=reply_markup
    )

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

# ── SPORTS / MATCH flow ──────────────────────────────────────────────────

async def handle_match_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by 🏏 Live Match Post button."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    try:
        user_data = state.get_user_data(user_id)
        user_data["mode"] = "collect_match"
        user_data["match_query"] = ""
        state.set_user_data(user_id, user_data)

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🏏 *LIVE MATCH POST MODE*\n\n"
                "Send me a match query or just hit Generate for the latest IPL match.\n"
                "Example: _RCB vs MI today_ or _Rohit Sharma record_"
            ),
            parse_mode="Markdown",
        )
        keyboard = [
            [InlineKeyboardButton("⚡ Generate Latest IPL Post", callback_data="SUBMIT_MATCH")]
        ]
        await context.bot.send_message(
            chat_id=user_id,
            text="Or type your query above, then click Generate:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        import logging
        logging.error(f"Error in handle_match_post: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"Error: {str(e)}")


async def handle_match_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect optional text query for the sports post."""
    user_id = update.effective_user.id
    user_data = state.get_user_data(user_id)

    if user_data.get("mode") != "collect_match":
        return  # not in match mode – let other handlers deal with it

    if update.message.text:
        user_data["match_query"] = update.message.text[:200]
        state.set_user_data(user_id, user_data)
        keyboard = [[InlineKeyboardButton("⚡ Generate Match Post", callback_data="SUBMIT_MATCH")]]
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Query saved: _{user_data['match_query']}_\nClick Generate when ready.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_submit_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger full multi-agent sports generation."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_data = state.get_user_data(user_id)

    match_query = user_data.get("match_query") or "IPL 2026 latest match today"

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🔄 *Activating Multi-Agent Sports Engine…*\n"
            "  📡 DataAgent: Fetching live match data\n"
            "  🎨 VisualAgent: Planning cinematic slides\n"
            "  🎬 DirectorAgent: Writing captions\n\n"
            "This takes ~30s — building your premium IPL post!"
        ),
        parse_mode="Markdown",
    )
    await send_sports_drafts(update, context, match_query)


async def send_sports_drafts(
    update: Update, context: ContextTypes.DEFAULT_TYPE, match_query: str
):
    """Run generate_sports_previews and send results to Telegram."""
    chat_id = update.effective_chat.id
    try:
        import asyncio
        previews = await asyncio.to_thread(generate_sports_previews, match_query)

        if not previews:
            await context.bot.send_message(chat_id=chat_id, text="❌ No sports previews generated. Try again.")
            return

        for preview in previews:
            match_title = preview.get("match_data", {}).get("match_title", "IPL 2026")
            media = []
            for idx, url in enumerate(preview["media_urls"]):
                caption = f"🏏 {match_title}" if idx == 0 else ""
                media.append(InputMediaPhoto(media=url, caption=caption))

            button = InlineKeyboardButton("🚀 Post to IG", callback_data=f"POST|{preview['uuid']}")
            reply_markup = InlineKeyboardMarkup([[button]])

            if len(media) > 1:
                await context.bot.send_media_group(chat_id=chat_id, media=media)
            elif media:
                await context.bot.send_photo(
                    chat_id=chat_id, photo=media[0].media, caption=media[0].caption
                )

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏆 *{match_title}*\n\nReady to post?",
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )

        # Reset mode
        user_data = state.get_user_data(chat_id)
        user_data["mode"] = "idle"
        state.set_user_data(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text="✅ Sports post ready! Check previews above.")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error generating sports post: {str(e)}")


# ── Publish callback (shared between all post types) ─────────────────────

async def handle_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("POST|"):
        preview_uuid = data.split("|", 1)[1]
        await query.message.reply_text("📡 Publishing to Instagram…")

        try:
            result = publish_selected(preview_uuid)
            media_id = result.get('instagram_media_id', 'Success')
            await query.message.reply_text(f"✅ Published!\nMedia: IG_{media_id}", parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to publish: {str(e)}")

def register_handlers(app):
    # CallbackQuery handlers MUST come first
    app.add_handler(CallbackQueryHandler(handle_custom_post, pattern="^CUSTOM_POST$"))
    app.add_handler(CallbackQueryHandler(handle_get_posts, pattern="^GET_POSTS$"))
    app.add_handler(CallbackQueryHandler(handle_submit_custom, pattern="^SUBMIT_CUSTOM$"))
    app.add_handler(CallbackQueryHandler(handle_match_post, pattern="^MATCH_POST$"))
    app.add_handler(CallbackQueryHandler(handle_submit_match, pattern="^SUBMIT_MATCH$"))
    app.add_handler(CallbackQueryHandler(handle_publish, pattern=r"^POST\|"))

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("match", lambda u, c: handle_submit_match(u, c)))

    # Message handler — route to correct mode
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, _route_message))


async def _route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route incoming text/photo to the correct mode handler."""
    user_id = update.effective_user.id
    mode = state.get_user_data(user_id).get("mode", "idle")
    if mode == "collect_match":
        await handle_match_input(update, context)
    elif mode == "collect_custom":
        await handle_custom_input(update, context)
    else:
        await start(update, context)
