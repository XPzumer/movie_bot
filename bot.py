import os
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Konfiguratsiya - BU YERNI TO'G'RI TO'LDIRING!
TOKEN = "7940054379:AAHMPU92jPRejDiVq8HXHieAK_v_REMHOok"  # @BotFather bergan token
CHANNEL_ID = -1002898856062  # Kanal ID (-100 bilan boshlanadi)
ADMIN_ID = 7841068189  # Sizning Telegram ID
DB_FILE = "content_db.json"

# Ma'lumotlar bazasi
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"codes": {}, "saved": {}}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Kod Kiriting", callback_data='enter_code')],
        [InlineKeyboardButton("💾 Saqlanganlar", callback_data='saved_content')],
        [
            InlineKeyboardButton("📢 Kanalimiz", url="https://t.me/your_channel"),
            InlineKeyboardButton("📷 Instagram", url="https://instagram.com/your_profile")
        ],
        [InlineKeyboardButton("ℹ️ Biz Haqimizda", callback_data='about')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎬 *Maxsus Kontentlar Botiga Xush Kelibsiz!*\n\n"
        "🔑 Kodingizni kiriting yoki saqlangan kontentlaringizni ko'ring",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Kod kiritish uchun handler
async def enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔐 *Maxsus kodni kiriting:*\n\n"
        "Kod shakli: `ABC123` yoki `MOV456`\n\n"
        "Yuborish uchun kodni shu yerga yozing:",
        parse_mode='Markdown'
    )

# Foydalanuvchi xabarlarini qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and not update.message.text.startswith('/'):
        await send_content(update, context, update.message.text)
    elif update.message.video or update.message.photo:
        await handle_media(update, context)

# Media fayllarni qayta ishlash
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        if update.message.video:
            file_id = update.message.video.file_id
            await update.message.reply_text(f"Video File ID: `{file_id}`\n\nKod qo'shish uchun: /add CODE video 'Nomi' {file_id}", parse_mode='Markdown')
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            await update.message.reply_text(f"Rasm File ID: `{file_id}`\n\nKod qo'shish uchun: /add CODE photo 'Nomi' {file_id}", parse_mode='Markdown')

# Kontent yuborish
async def send_content(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    db = load_db()
    content = db['codes'].get(code.upper())
    
    if not content:
        await update.message.reply_text("❌ Bunday kod topilmadi! Kodni tekshirib, qayta urinib ko'ring.")
        return
    
    try:
        if content['type'] == 'video':
            await context.bot.send_video(
                chat_id=update.message.chat_id,
                video=content['file_id'],
                caption=f"🎬 *{content['name']}*\n#️⃣ `{code.upper()}`",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=content['file_id'],
                caption=f"🖼 *{content['name']}*\n#️⃣ `{code.upper()}`",
                parse_mode='Markdown'
            )
        
        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data=f'like_{code}'),
                InlineKeyboardButton("💾 Saqlash", callback_data=f'save_{code}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Kontentni baholang:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

# Admin uchun kontent qo'shish
async def add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q! Faqat adminlar yangi kod qo'sha oladi.")
        return
    
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("❌ Noto'g'ri format. To'g'ri format:\n/add CODE turi 'Nomi' FILE_ID\n\nMasalan:\n/add MOV123 video 'Interstellar filmi' BAQAgMAAxkBAANkZj...")
        return
    
    code = args[0].upper()
    content_type = args[1]
    name = ' '.join(args[2:-1])
    file_id = args[-1]
    
    db = load_db()
    db['codes'][code] = {
        "type": content_type,
        "name": name,
        "file_id": file_id
    }
    save_db(db)
    
    await update.message.reply_text(f"✅ *{code}* kodi muvaffaqiyatli qo'shildi!\n\nNomi: *{name}*\nTuri: *{content_type}*", parse_mode='Markdown')

# Callback query handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    await query.answer()
    
    if data == 'enter_code':
        await enter_code(update, context)
    elif data == 'saved_content':
        await show_saved(update, context)
    elif data == 'about':
        await about(update, context)
    elif data == 'back_to_main':
        await start(update, context)
    elif data.startswith('like_'):
        code = data.split('_')[1]
        await query.edit_message_text("✅ Sizga ushbu kontent yoqdi!")
    elif data.startswith('save_'):
        code = data.split('_')[1]
        db = load_db()
        user_id = str(query.from_user.id)
        
        if user_id not in db['saved']:
            db['saved'][user_id] = []
        
        if code not in db['saved'][user_id]:
            db['saved'][user_id].append(code)
            save_db(db)
            await query.edit_message_text("✅ Kontent saqlandi! \"Saqlanganlar\" bo'limida ko'rishingiz mumkin.")
        else:
            await query.edit_message_text("⚠️ Bu kontent allaqachon saqlangan")
    elif data.startswith('view_'):
        code = data.split('_')[1]
        await send_content(update, context, code)

# Saqlangan kontentlar
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    db = load_db()
    
    saved = db['saved'].get(user_id, [])
    
    if not saved:
        await query.edit_message_text("ℹ️ Sizda saqlangan kontentlar yo'q")
        return
    
    keyboard = []
    for code in saved:
        if code in db['codes']:  # Faqat mavjud kodlarni ko'rsatish
            keyboard.append([InlineKeyboardButton(f"{db['codes'][code]['name']} ({code})", callback_data=f'view_{code}')])
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data='back_to_main')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💾 *Saqlangan kontentlaringiz:*\n\nQuyidagi kontentlardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Biz haqimizda
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "ℹ️ *Biz Haqimizda*\n\n"
        "Bu bot orqali siz maxsus kodlar yordamida "
        "eksklyuziv kontentlarga ega bo'lasiz!\n\n"
        "📆 Ish vaqti: 24/7\n"
        "📩 Aloqa: @admin_username\n\n"
        "Botdan to'liq foydalanish uchun /start buyrug'ini yuboring.",
        parse_mode='Markdown'
    )

# Asosiy funksiya
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_content))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO, handle_media))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()