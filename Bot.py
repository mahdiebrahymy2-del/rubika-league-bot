import os
import time
import json
import requests

# =========================
# تنظیمات
# =========================

TOKEN = os.getenv("RUBIKA_TOKEN", "").strip()

OWNER_ID = os.getenv("OWNER_ID", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

USERS_FILE = "users.json"


# =========================
# بررسی تنظیمات
# =========================

if not TOKEN:
    raise RuntimeError("RUBIKA_TOKEN تنظیم نشده است.")

if not OWNER_ID:
    print("⚠️ هشدار: OWNER_ID تنظیم نشده است.")

if not ADMIN_ID:
    print("⚠️ هشدار: ADMIN_ID تنظیم نشده است.")


# =========================
# کاربران
# =========================

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except:
        return set()


def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as file:
            json.dump(
                list(users),
                file,
                ensure_ascii=False
            )
    except Exception as e:
        print("خطا در ذخیره کاربران:", e)


users = load_users()


# =========================
# API
# =========================

def api(method, data=None):
    try:
        response = requests.post(
            f"{API_URL}/{method}",
            json=data or {},
            timeout=35
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:
        print("خطا در API:", e)
        return None


# =========================
# دریافت آپدیت‌ها
# =========================

def get_updates(offset_id=None):

    data = {
        "limit": 10
    }

    if offset_id:
        data["offset_id"] = offset_id

    result = api("getUpdates", data)

    if not result:
        return [], None

    result_data = result.get("data", {})

    if isinstance(result_data, dict):
        updates = result_data.get("updates", [])
        next_offset = result_data.get("next_offset_id")
    else:
        updates = []
        next_offset = None

    return updates, next_offset


# =========================
# ارسال پیام
# =========================

def send_message(chat_id, text):

    if not chat_id:
        return None

    return api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


# =========================
# استخراج اطلاعات پیام
# =========================

def get_message_data(update):

    message = update.get("new_message")

    if not message:
        message = update.get("message")

    if not message:
        message = update.get("inline_message")

    if not isinstance(message, dict):
        message = {}

    chat_id = (
        update.get("chat_id")
        or message.get("chat_id")
        or message.get("object_guid")
    )

    sender_id = (
        message.get("sender_id")
        or update.get("sender_id")
    )

    text = message.get("text") or ""

    message_id = (
        message.get("message_id")
        or update.get("message_id")
    )

    return chat_id, sender_id, text, message_id


# =========================
# سطح دسترسی
# =========================

def is_owner(user_id):
    return bool(
        OWNER_ID
        and user_id
        and user_id == OWNER_ID
    )


def is_admin(user_id):
    return bool(
        is_owner(user_id)
        or (
            ADMIN_ID
            and user_id
            and user_id == ADMIN_ID
        )
    )


# =========================
# پردازش پیام
# =========================

def handle_message(chat_id, sender_id, text):

    global users

    if not chat_id:
        return

    # ثبت کاربر
    if chat_id not in users:
        users.add(chat_id)
        save_users(users)

    text = text.strip()

    # =====================
    # START
    # =====================

    if text == "/start":

        send_message(
            chat_id,
            "🤖 سلام!\n\n"
            "به ربات خوش آمدی ❤️\n\n"
            "دستورات:\n"
            "🔹 /help - راهنما\n"
            "🔹 /id - شناسه شما\n"
        )

        return

    # =====================
    # HELP
    # =====================

    if text == "/help":

        send_message(
            chat_id,
            "📚 راهنمای ربات\n\n"
            "/start\n"
            "شروع ربات\n\n"
            "/id\n"
            "نمایش شناسه\n\n"
            "/help\n"
            "نمایش راهنما"
        )

        return

    # =====================
    # ID
    # =====================

    if text == "/id":

        send_message(
            chat_id,
            f"🆔 شناسه کاربر:\n{sender_id}\n\n"
            f"💬 شناسه چت:\n{chat_id}"
        )

        return

    # =====================
    # اطلاعات مدیر
    # =====================

    if text == "/panel":

        if not is_admin(sender_id):

            send_message(
                chat_id,
                "⛔ شما دسترسی مدیریتی ندارید."
            )

            return

        if is_owner(sender_id):

            send_message(
                chat_id,
                "👑 پنل مالک\n\n"
                "دسترسی کامل مدیریتی فعال است.\n\n"
                "/users - تعداد کاربران\n"
                "/broadcast متن - ارسال همگانی"
            )

        else:

            send_message(
                chat_id,
                "🛡️ پنل ادمین\n\n"
                "دسترسی ادمین برای شما فعال است."
            )

        return

    # =====================
    # تعداد کاربران
    # =====================

    if text == "/users":

        if not is_admin(sender_id):

            send_message(
                chat_id,
                "⛔ این دستور مخصوص مدیران است."
            )

            return

        send_message(
            chat_id,
            f"👥 تعداد کاربران:\n{len(users)}"
        )

        return

    # =====================
    # Broadcast
    # =====================

    if text.startswith("/broadcast "):

        if not is_owner(sender_id):

            send_message(
                chat_id,
                "⛔ فقط مالک ربات اجازه این دستور را دارد."
            )

            return

        message = text[len("/broadcast "):].strip()

        if not message:

            send_message(
                chat_id,
                "❌ متن پیام را وارد کن."
            )

            return

        success = 0
        failed = 0

        for user_chat_id in list(users):

            try:

                result = send_message(
                    user_chat_id,
                    message
                )

                if result:
                    success += 1
                else:
                    failed += 1

                time.sleep(0.2)

            except:

                failed += 1

        send_message(
            chat_id,
            f"📢 ارسال انجام شد.\n\n"
            f"✅ موفق: {success}\n"
            f"❌ ناموفق: {failed}"
        )

        return

    # =====================
    # پیام معمولی
    # =====================

    if text:

        send_message(
            chat_id,
            f"📩 پیامت دریافت شد:\n\n{text}"
        )


# =========================
# اجرای ربات
# =========================

print("🤖 ربات در حال اجراست...")

offset_id = None

while True:

    try:

        updates, new_offset = get_updates(offset_id)

        if new_offset:
            offset_id = new_offset

        for update in updates:

            try:

                chat_id, sender_id, text, message_id = (
                    get_message_data(update)
                )

                print(
                    f"پیام جدید | "
                    f"chat={chat_id} | "
                    f"user={sender_id} | "
                    f"text={text}"
                )

                handle_message(
                    chat_id,
                    sender_id,
                    text
                )

            except Exception as e:

                print(
                    "خطا در پردازش پیام:",
                    e
                )

        time.sleep(2)

    except KeyboardInterrupt:

        print("ربات متوقف شد.")
        break

    except Exception as e:

        print(
            "خطای اصلی:",
            e
        )

        time.sleep(5)
