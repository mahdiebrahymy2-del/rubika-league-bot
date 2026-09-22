import os
from rubka import Robot, Message


# =========================
# شناسه‌های مدیریتی
# =========================

OWNER_ID = "u0lqml05474345c112ab2f577c4e274"
ADMIN_ID = "u0HXdRY029886f0a258848773c9d2261"

# مالک و ادمین هر دو دسترسی مدیریتی یکسان دارند
MANAGERS = {OWNER_ID, ADMIN_ID}


# =========================
# توکن ربات
# =========================

TOKEN = os.getenv("RUBIKA_TOKEN")

if not TOKEN:
    raise ValueError("❌ متغیر RUBIKA_TOKEN تنظیم نشده است.")


# =========================
# ساخت ربات
# =========================

bot = Robot(token=TOKEN)


# =========================
# بررسی مدیر بودن
# =========================

def is_manager(message: Message):
    return message.sender_id in MANAGERS


# =========================
# شروع ربات
# =========================

@bot.on_message(commands=["start"])
def start_handler(bot: Robot, message: Message):

    if is_manager(message):
        message.reply(
            "🏆 سلام مدیر!\n\n"
            "⚽ ربات لیگ فوتبال فعال است.\n\n"
            "👑 شما دسترسی مدیریتی دارید."
        )
    else:
        message.reply(
            "🏆 سلام!\n\n"
            "⚽ به ربات لیگ فوتبال خوش آمدید.\n"
            "ربات با موفقیت فعال است ✅"
        )


# =========================
# راهنما
# =========================

@bot.on_message(commands=["help"])
def help_handler(bot: Robot, message: Message):

    if is_manager(message):
        message.reply(
            "📚 راهنمای مدیریت\n\n"
            "👑 مالک و ادمین:\n"
            "هر دو دسترسی مدیریتی یکسان دارند.\n\n"
            "⚽ امکانات مدیریتی لیگ در مراحل بعدی اضافه می‌شود."
        )
    else:
        message.reply(
            "📚 راهنما\n\n"
            "/start - شروع ربات\n"
            "/help - راهنما"
        )


# =========================
# پنل مدیریت
# =========================

@bot.on_message(commands=["panel"])
def panel_handler(bot: Robot, message: Message):

    if not is_manager(message):
        message.reply("⛔ شما دسترسی مدیریت ربات را ندارید.")
        return

    message.reply(
        "👑 پنل مدیریت\n\n"
        "⚽ مدیریت لیگ\n"
        "👥 مدیریت کاربران\n"
        "🏆 مدیریت تیم‌ها\n"
        "📊 مدیریت جدول\n"
        "⚙️ تنظیمات ربات\n\n"
        "مالک و ادمین هر دو به این بخش دسترسی دارند."
    )


# =========================
# پیام‌های معمولی
# =========================

@bot.on_message()
def message_handler(bot: Robot, message: Message):

    text = message.text or ""

    if text == "سلام":
        message.reply("سلام 👋\n⚽ ربات لیگ آماده است.")


# =========================
# اجرای ربات
# =========================

if __name__ == "__main__":
    bot.run()
