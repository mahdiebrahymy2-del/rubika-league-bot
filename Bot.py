import urllib.request
import json
import time
import os

# ==================================================
# تنظیمات
# ==================================================

TOKEN = ""

# شناسه خودت
MANAGER_ID = "u0HXdRY029886f0a258848773c9d2261"

# فعلاً خالی است؛ بعداً شناسه مالک را اینجا می‌گذاریم
OWNER_ID = ""

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

DATA_FILE = "league_data.json"


# ==================================================
# دیتابیس
# ==================================================

def load_data():

    default = {
        "teams": [],
        "matches": [],
        "scorers": [],
        "cards": [],
        "announcements": [],
        "users": []
    }

    try:

        if os.path.exists(DATA_FILE):

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            for key in default:

                if key not in data:
                    data[key] = default[key]

            return data

    except Exception as e:

        print("❌ خطا در خواندن دیتابیس:", e)

    return default


db = load_data()


def save_data():

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                db,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("❌ خطا در ذخیره دیتابیس:", e)


# وضعیت کاربرها
states = {}


# ==================================================
# API روبیکا
# ==================================================

def api_call(method, data=None):

    if data is None:
        data = {}

    body = json.dumps(
        data
    ).encode("utf-8")

    request = urllib.request.Request(

        BASE_URL + "/" + method,

        data=body,

        headers={
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


# ==================================================
# ارسال پیام
# ==================================================

def send_message(
    chat_id,
    text,
    keypad=None
):

    data = {

        "chat_id": str(chat_id),

        "text": text
    }

    if keypad is not None:

        data["chat_keypad_type"] = "New"

        data["chat_keypad"] = keypad

    try:

        return api_call(
            "sendMessage",
            data
        )

    except Exception as e:

        print(
            "❌ خطا در ارسال:",
            e
        )

        return None


# ==================================================
# دسترسی
# ==================================================

def is_admin(sender_id):

    if sender_id == MANAGER_ID:
        return True

    if OWNER_ID and sender_id == OWNER_ID:
        return True

    return False


# ==================================================
# ذخیره کاربر
# ==================================================

def remember_user(chat_id):

    chat_id = str(chat_id)

    if chat_id not in db["users"]:

        db["users"].append(chat_id)

        save_data()


# ==================================================
# ساخت دکمه
# ==================================================

def button(text, button_id):

    return {

        "id": button_id,

        "type": "Simple",

        "button_text": text
    }


def make_keypad(rows):

    return {

        "rows": [

            {
                "buttons": [
                    button(text, bid)
                    for text, bid in row
                ]
            }

            for row in rows
        ],

        "resize_keyboard": True,

        "on_time_keyboard": False
    }


# ==================================================
# منوی کاربران
# ==================================================

USER_MENU = make_keypad([

    [
        ("📊 جدول لیگ", "table"),
        ("📅 برنامه بازی‌ها", "matches")
    ],

    [
        ("⚽ نتایج بازی‌ها", "results"),
        ("🥅 آقای گل‌ها", "scorers")
    ],

    [
        ("🟨🟥 کارت‌ها", "cards"),
        ("👥 تیم‌ها", "teams")
    ],

    [
        ("📢 اطلاعیه‌ها", "news")
    ]

])


# ==================================================
# منوی مدیریت
# ==================================================

ADMIN_MENU = make_keypad([

    [
        ("📊 جدول لیگ", "table"),
        ("📅 برنامه بازی‌ها", "matches")
    ],

    [
        ("⚽ نتایج بازی‌ها", "results"),
        ("🥅 آقای گل‌ها", "scorers")
    ],

    [
        ("🟨🟥 کارت‌ها", "cards"),
        ("👥 تیم‌ها", "teams")
    ],

    [
        ("📢 اطلاعیه‌ها", "news"),
        ("⚙️ مدیریت لیگ", "manage")
    ]

])


# ==================================================
# پنل مدیریت
# ==================================================

MANAGE_MENU = make_keypad([

    [
        ("➕ افزودن تیم", "add_team"),
        ("✏️ ویرایش تیم", "edit_team")
    ],

    [
        ("🗑️ حذف تیم", "delete_team"),
        ("➕ افزودن بازی", "add_match")
    ],

    [
        ("⚽ ثبت نتیجه", "add_result"),
        ("✏️ ویرایش نتیجه", "edit_result")
    ],

    [
        ("🗑️ حذف نتیجه", "delete_result"),
        ("🥅 ثبت گلزن", "add_scorer")
    ],

    [
        ("🟨🟥 ثبت کارت", "add_card"),
        ("📢 ارسال اطلاعیه", "announce")
    ],

    [
        ("🔄 بروزرسانی", "refresh"),
        ("🔙 بازگشت", "back")
    ]

])


# ==================================================
# پیدا کردن تیم
# ==================================================

def find_team(name):

    name = name.strip().lower()

    for team in db["teams"]:

        if team["name"].strip().lower() == name:

            return team

    return None


def team_name(team_id):

    for team in db["teams"]:

        if team["id"] == team_id:

            return team["name"]

    return "نامشخص"


# ==================================================
# ساخت ID
# ==================================================

def next_id(items):

    numbers = []

    for item in items:

        try:

            numbers.append(
                int(item["id"])
            )

        except:
            pass

    return str(
        max(numbers, default=0) + 1
    )


# ==================================================
# جدول لیگ
# ==================================================

def get_table():

    if not db["teams"]:

        return "📊 جدول لیگ\n\nهنوز تیمی ثبت نشده است."

    table = {}

    for team in db["teams"]:

        table[team["id"]] = {

            "name": team["name"],

            "played": 0,

            "wins": 0,

            "draws": 0,

            "losses": 0,

            "gf": 0,

            "ga": 0,

            "points": 0
        }


    for match in db["matches"]:

        if not match.get("played"):
            continue

        home = match["home"]

        away = match["away"]

        if home not in table:
            continue

        if away not in table:
            continue

        hg = match["home_goals"]

        ag = match["away_goals"]


        table[home]["played"] += 1

        table[away]["played"] += 1


        table[home]["gf"] += hg

        table[home]["ga"] += ag


        table[away]["gf"] += ag

        table[away]["ga"] += hg


        if hg > ag:

            table[home]["wins"] += 1

            table[away]["losses"] += 1

            table[home]["points"] += 3


        elif hg < ag:

            table[away]["wins"] += 1

            table[home]["losses"] += 1

            table[away]["points"] += 3


        else:

            table[home]["draws"] += 1

            table[away]["draws"] += 1

            table[home]["points"] += 1

            table[away]["points"] += 1


    ordered = sorted(

        table.values(),

        key=lambda x: (

            -x["points"],

            -(x["gf"] - x["ga"]),

            -x["gf"],

            x["name"]
        )
    )


    text = (

        "📊 جدول لیگ\n\n"

        "رتبه | تیم | بازی | برد | مساوی | باخت | تفاضل | امتیاز\n"
    )


    for index, row in enumerate(
        ordered,
        1
    ):

        difference = (
            row["gf"] -
            row["ga"]
        )

        text += (

            f"{index} | "

            f"{row['name']} | "

            f"{row['played']} | "

            f"{row['wins']} | "

            f"{row['draws']} | "

            f"{row['losses']} | "

            f"{difference:+d} | "

            f"{row['points']}\n"
        )


    return text


# ==================================================
# تیم‌ها
# ==================================================

def get_teams():

    if not db["teams"]:

        return "👥 هنوز تیمی ثبت نشده است."

    text = "👥 تیم‌های لیگ\n\n"

    for i, team in enumerate(
        db["teams"],
        1
    ):

        text += f"{i}. {team['name']}\n"

    return text


# ==================================================
# بازی‌ها
# ==================================================

def get_matches(results=False):

    if not db["matches"]:

        return "⚽ هنوز بازی‌ای ثبت نشده است."


    title = (
        "⚽ نتایج بازی‌ها"
        if results
        else
        "📅 برنامه بازی‌ها"
    )


    text = title + "\n\n"


    found = False


    for i, match in enumerate(
        db["matches"],
        1
    ):

        if results and not match.get("played"):
            continue


        found = True


        line = (

            f"{i}. "

            f"{team_name(match['home'])}"

            " 🆚 "

            f"{team_name(match['away'])}"
        )


        if match.get("date"):

            line += (
                f"\n   📅 {match['date']}"
            )


        if match.get("played"):

            line += (

                f"\n   ⚽ "

                f"{match['home_goals']}"

                " - "

                f"{match['away_goals']}"
            )

        else:

            line += "\n   ⏳ برگزار نشده"


        text += line + "\n\n"


    if not found:

        return (
            title +
            "\n\nموردی وجود ندارد."
        )


    return text


# ==================================================
# گلزنان
# ==================================================

def get_scorers():

    if not db["scorers"]:

        return "🥅 هنوز گلزنی ثبت نشده است."


    ordered = sorted(

        db["scorers"],

        key=lambda x:
        -x["goals"]
    )


    text = "🥅 آقای گل‌ها\n\n"


    for i, player in enumerate(
        ordered,
        1
    ):

        text += (

            f"{i}. "

            f"{player['name']}"

            " — "

            f"{player['team']}"

            " — ⚽ "

            f"{player['goals']} گل\n"
        )


    return text


# ==================================================
# کارت‌ها
# ==================================================

def get_cards():

    if not db["cards"]:

        return "🟨🟥 هنوز کارتی ثبت نشده است."


    text = "🟨🟥 کارت‌ها\n\n"


    for i, card in enumerate(
        db["cards"],
        1
    ):

        text += (

            f"{i}. "

            f"{card['player']}"

            " — "

            f"{card['team']}"

            "\n"

            f"   🟨 {card['yellow']}"

            " | "

            f"🟥 {card['red']}\n"
        )


    return text


# ==================================================
# اطلاعیه‌ها
# ==================================================

def get_news():

    if not db["announcements"]:

        return "📢 هنوز اطلاعیه‌ای ثبت نشده است."


    text = "📢 اطلاعیه‌های لیگ\n\n"


    for news in reversed(
        db["announcements"][-10:]
    ):

        text += (
            "• "
            + news["text"]
            + "\n\n"
        )


    return text


# ==================================================
# ارسال منوی اصلی
# ==================================================

def main_menu(
    chat_id,
    admin
):

    if admin:

        send_message(

            chat_id,

            "👑 پنل مدیریت لیگ\n\n"
            "به ربات لیگ خوش آمدی ⚽\n"
            "شما دسترسی مدیریت دارید.",

            ADMIN_MENU
        )

    else:

        send_message(

            chat_id,

            "🏆 به ربات لیگ فوتبال خوش آمدی!\n\n"
            "از منوی زیر استفاده کن:",

            USER_MENU
        )


# ==================================================
# پردازش مراحل ورودی
# ==================================================

def process_state(
    chat_id,
    text
):

    key = str(chat_id)

    if key not in states:
        return False


    state = states[key]

    action = state["action"]


    # ----------------------------------------------
    # افزودن تیم
    # ----------------------------------------------

    if action == "add_team":

        if find_team(text):

            send_message(
                chat_id,
                "❌ این تیم قبلاً ثبت شده است."
            )

            return True


        db["teams"].append({

            "id": next_id(
                db["teams"]
            ),

            "name": text
        })


        save_data()

        states.pop(key)


        send_message(

            chat_id,

            f"✅ تیم «{text}» اضافه شد.",

            MANAGE_MENU
        )

        return True


    # ----------------------------------------------
    # ویرایش تیم - انتخاب
    # ----------------------------------------------

    if action == "edit_team_select":

        try:

            index = int(text) - 1

            team = db["teams"][index]

            states[key] = {

                "action":
                "edit_team_name",

                "index":
                index
            }


            send_message(

                chat_id,

                "✏️ نام جدید تیم را بفرست:\n\n"
                f"نام فعلی: {team['name']}"
            )


        except:

            send_message(
                chat_id,
                "❌ شماره تیم اشتباه است."
            )


        return True


    # ----------------------------------------------
    # ویرایش تیم - نام جدید
    # ----------------------------------------------

    if action == "edit_team_name":

        index = state["index"]

        db["teams"][index]["name"] = text

        save_data()

        states.pop(key)


        send_message(

            chat_id,

            "✅ نام تیم تغییر کرد.",

            MANAGE_MENU
        )

        return True


    # ----------------------------------------------
    # حذف تیم
    # ----------------------------------------------

    if action == "delete_team":

        try:

            index = int(text) - 1

            team = db["teams"][index]

            team_id = team["id"]


            for match in db["matches"]:

                if (

                    match["home"] == team_id
                    or
                    match["away"] == team_id
                ):

                    send_message(

                        chat_id,

                        "❌ این تیم در بازی‌ها استفاده شده و حذف نشد."
                    )

                    states.pop(key)

                    return True


            name = team["name"]

            db["teams"].pop(index)

            save_data()

            states.pop(key)


            send_message(

                chat_id,

                f"🗑️ تیم «{name}» حذف شد.",

                MANAGE_MENU
            )


        except:

            send_message(
                chat_id,
                "❌ شماره تیم اشتباه است."
            )


        return True


    # ----------------------------------------------
    # افزودن بازی
    # ----------------------------------------------

    if action == "add_match":

        parts = [
            x.strip()
            for x in text.split("|")
        ]


        if len(parts) < 2:

            send_message(

                chat_id,

                "❌ فرمت اشتباه.\n\n"
                "مثال:\n"
                "رئال | چلسی | 2026/09/25"
            )

            return True


        home = find_team(parts[0])

        away = find_team(parts[1])


        if not home or not away:

            send_message(

                chat_id,

                "❌ یکی از تیم‌ها پیدا نشد."
            )

            return True


        if home["id"] == away["id"]:

            send_message(

                chat_id,

                "❌ تیم نمی‌تواند با خودش بازی کند."
            )

            return True


        date = ""

        if len(parts) >= 3:

            date = parts[2]


        db["matches"].append({

            "id":
            next_id(db["matches"]),

            "home":
            home["id"],

            "away":
            away["id"],

            "date":
            date,

            "played":
            False,

            "home_goals":
            0,

            "away_goals":
            0
        })


        save_data()

        states.pop(key)


        send_message(

            chat_id,

            "✅ بازی با موفقیت ثبت شد.",

            MANAGE_MENU
        )


        return True


    # ----------------------------------------------
    # انتخاب بازی برای نتیجه
    # ----------------------------------------------

    if action == "result_select":

        try:

            index = int(text) - 1

            match = db["matches"][index]


            states[key] = {

                "action":
                "result_score",

                "index":
                index
            }


            send_message(

                chat_id,

                "⚽ نتیجه را بفرست.\n\n"

                f"{team_name(match['home'])}"

                " 🆚 "

                f"{team_name(match['away'])}"

                "\n\n"

                "مثال: 2-1"
            )


        except:

            send_message(
                chat_id,
                "❌ شماره بازی اشتباه است."
            )


        return True


    # ----------------------------------------------
    # ثبت نتیجه
    # ----------------------------------------------

    if action == "result_score":

        try:

            score = text.replace(
                " ",
                ""
            ).split("-")


            if len(score) != 2:

                raise ValueError


            home_goals = int(
                score[0]
            )

            away_goals = int(
                score[1]
            )


            if (
                home_goals < 0
                or
                away_goals < 0
            ):

                raise ValueError


            index = state["index"]


            db["matches"][index][
                "home_goals"
            ] = home_goals


            db["matches"][index][
                "away_goals"
            ] = away_goals


            db["matches"][index][
                "played"
            ] = True


            save_data()

            states.pop(key)


            send_message(

                chat_id,

                "✅ نتیجه ثبت شد.\n"
                "📊 جدول هم خودکار بروزرسانی شد.",

                MANAGE_MENU
            )


        except:

            send_message(

                chat_id,

                "❌ نتیجه اشتباه است.\n\n"
                "مثال صحیح:\n"
                "3-1"
            )


        return True


    # ----------------------------------------------
    # حذف نتیجه
    # ----------------------------------------------

    if action == "delete_result":

        try:

            index = int(text) - 1

            db["matches"][index][
                "played"
            ] = False


            db["matches"][index][
                "home_goals"
            ] = 0


            db["matches"][index][
                "away_goals"
            ] = 0


            save_data()

            states.pop(key)


            send_message(

                chat_id,

                "🗑️ نتیجه حذف شد.",

                MANAGE_MENU
            )


        except:

            send_message(
                chat_id,
                "❌ شماره بازی اشتباه است."
            )


        return True


    # ----------------------------------------------
    # ویرایش نتیجه
    # ----------------------------------------------

    if action == "edit_result_select":

        try:

            index = int(text) - 1

            match = db["matches"][index]


            states[key] = {

                "action":
                "result_score",

                "index":
                index
            }


            send_message(

                chat_id,

                "✏️ نتیجه جدید را بفرست.\n\n"

                f"{team_name(match['home'])}"

                " 🆚 "

                f"{team_name(match['away'])}"

                "\n\n"

                "مثال: 4-2"
            )


        except:

            send_message(
                chat_id,
                "❌ شماره بازی اشتباه است."
            )


        return True


    # ----------------------------------------------
    # ثبت گلزن
    # ----------------------------------------------

    if action == "add_scorer":

        parts = [
            x.strip()
            for x in text.split("|")
        ]


        if len(parts) != 3:

            send_message(

                chat_id,

                "❌ فرمت:\n"
                "نام | تیم | تعداد گل\n\n"
                "مثال:\n"
                "مهدی | رئال | 3"
            )

            return True


        try:

            goals = int(parts[2])

            if goals < 1:
                raise ValueError


        except:

            send_message(
                chat_id,
                "❌ تعداد گل باید عدد باشد."
            )

            return True


        db["scorers"].append({

            "name":
            parts[0],

            "team":
            parts[1],

            "goals":
            goals
        })


        save_data()

        states.pop(key)


        send_message(

            chat_id,

            "✅ گلزن ثبت شد.",

            MANAGE_MENU
        )


        return True


    # ----------------------------------------------
    # ثبت کارت
    # ----------------------------------------------

    if action == "add_card":

        parts = [
            x.strip()
            for x in text.split("|")
        ]


        if len(parts) != 4:

            send_message(

                chat_id,

                "❌ فرمت:\n"
                "بازیکن | تیم | زرد | قرمز\n\n"
                "مثال:\n"
                "علی | رئال | 2 | 1"
            )

            return True


        try:

            yellow = int(parts[2])

            red = int(parts[3])

            if yellow < 0 or red < 0:
                raise ValueError


        except:

            send_message(

                chat_id,

                "❌ تعداد کارت‌ها باید عدد باشد."
            )

            return True


        db["cards"].append({

            "player":
            parts[0],

            "team":
            parts[1],

            "yellow":
            yellow,

            "red":
            red
        })


        save_data()

        states.pop(key)


        send_message(

            chat_id,

            "✅ کارت‌ها ثبت شد.",

            MANAGE_MENU
        )


        return True


    # ----------------------------------------------
    # اطلاعیه
    # ----------------------------------------------

    if action == "announce":

        if not text:

            send_message(
                chat_id,
                "❌ متن خالی است."
            )

            return True


        db["announcements"].append({

            "text":
            text
        })


        save_data()

        states.pop(key)


        sent = 0


        for user_id in db["users"]:

            result = send_message(

                user_id,

                "📢 اطلاعیه لیگ\n\n"
                + text
            )


            if result:

                sent += 1


        send_message(

            chat_id,

            f"✅ اطلاعیه ارسال شد.\n"
            f"👥 تعداد ارسال: {sent}",

            MANAGE_MENU
        )


        return True


    return False


# ==================================================
# شروع
# ==================================================

print(
    "🤖 ربات لیگ روشن شد!"
)


offset_id = None


# ==================================================
# حلقه اصلی
# ==================================================

while True:

    try:

        request_data = {

            "limit": 20
        }


        if offset_id:

            request_data[
                "offset_id"
            ] = offset_id


        result = api_call(

            "getUpdates",

            request_data
        )


        if result.get(
            "status"
        ) != "OK":

            time.sleep(2)

            continue


        data = result.get(
            "data",
            {}
        )


        updates = data.get(
            "updates",
            []
        )


        for update in updates:

            chat_id = update.get(
                "chat_id"
            )


            message = update.get(
                "new_message",
                {}
            )


            if not chat_id:

                continue


            text = message.get(
                "text",
                ""
            ).strip()


            sender_id = message.get(
                "sender_id",
                ""
            )


            print(
                "💬 پیام:",
                text
            )


            print(
                "🆔 فرستنده:",
                sender_id
            )


            remember_user(
                chat_id
            )


            # --------------------------------------
            # مراحل در حال اجرا
            # --------------------------------------

            if process_state(
                chat_id,
                text
            ):

                continue


            admin = is_admin(
                sender_id
            )


            # --------------------------------------
            # START
            # --------------------------------------

            if text == "/start":

                states.pop(
                    str(chat_id),
                    None
                )


                main_menu(
                    chat_id,
                    admin
                )


            # --------------------------------------
            # جدول
            # --------------------------------------

            elif text == "📊 جدول لیگ":

                send_message(
                    chat_id,
                    get_table()
                )


            # --------------------------------------
            # برنامه
            # --------------------------------------

            elif text == "📅 برنامه بازی‌ها":

                send_message(
                    chat_id,
                    get_matches(False)
                )


            # --------------------------------------
            # نتایج
            # --------------------------------------

            elif text == "⚽ نتایج بازی‌ها":

                send_message(
                    chat_id,
                    get_matches(True)
                )


            # --------------------------------------
            # گلزنان
            # --------------------------------------

            elif text == "🥅 آقای گل‌ها":

                send_message(
                    chat_id,
                    get_scorers()
                )


            # --------------------------------------
            # کارت‌ها
            # --------------------------------------

            elif text == "🟨🟥 کارت‌ها":

                send_message(
                    chat_id,
                    get_cards()
                )


            # --------------------------------------
            # تیم‌ها
            # --------------------------------------

            elif text == "👥 تیم‌ها":

                send_message(
                    chat_id,
                    get_teams()
                )


            # --------------------------------------
            # اطلاعیه
            # --------------------------------------

            elif text == "📢 اطلاعیه‌ها":

                send_message(
                    chat_id,
                    get_news()
                )


            # --------------------------------------
            # مدیریت
            # --------------------------------------

            elif text == "⚙️ مدیریت لیگ":

                if admin:

                    send_message(

                        chat_id,

                        "⚙️ مدیریت لیگ\n\n"
                        "دسترسی شما تأیید شد.\n"
                        "یکی از امکانات را انتخاب کن:",

                        MANAGE_MENU
                    )

                else:

                    send_message(

                        chat_id,

                        "⛔ دسترسی غیرمجاز!\n\n"
                        "این بخش فقط برای مدیران لیگ است."
                    )


            # --------------------------------------
            # افزودن تیم
            # --------------------------------------

            elif (
                text == "➕ افزودن تیم"
                and admin
            ):

                states[
                    str(chat_id)
                ] = {

                    "action":
                    "add_team"
                }


                send_message(

                    chat_id,

                    "➕ نام تیم را بفرست:"
                )


            # --------------------------------------
            # ویرایش تیم
            # --------------------------------------

            elif (
                text == "✏️ ویرایش تیم"
                and admin
            ):

                if not db["teams"]:

                    send_message(
                        chat_id,
                        "❌ تیمی وجود ندارد."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "edit_team_select"
                    }


                    send_message(

                        chat_id,

                        "✏️ شماره تیم را بفرست:\n\n"

                        + get_teams()
                    )


            # --------------------------------------
            # حذف تیم
            # --------------------------------------

            elif (
                text == "🗑️ حذف تیم"
                and admin
            ):

                if not db["teams"]:

                    send_message(
                        chat_id,
                        "❌ تیمی وجود ندارد."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "delete_team"
                    }


                    send_message(

                        chat_id,

                        "🗑️ شماره تیم را بفرست:\n\n"

                        + get_teams()
                    )


            # --------------------------------------
            # افزودن بازی
            # --------------------------------------

            elif (
                text == "➕ افزودن بازی"
                and admin
            ):

                if len(db["teams"]) < 2:

                    send_message(

                        chat_id,

                        "❌ حداقل دو تیم لازم است."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "add_match"
                    }


                    send_message(

                        chat_id,

                        "➕ بازی را این‌طور بفرست:\n\n"

                        "تیم میزبان | تیم مهمان | تاریخ\n\n"

                        "مثال:\n"

                        "رئال | چلسی | 2026/09/25"
                    )


            # --------------------------------------
            # ثبت نتیجه
            # --------------------------------------

            elif (
                text == "⚽ ثبت نتیجه"
                and admin
            ):

                if not db["matches"]:

                    send_message(

                        chat_id,

                        "❌ بازی‌ای وجود ندارد."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "result_select"
                    }


                    send_message(

                        chat_id,

                        "⚽ شماره بازی را بفرست:\n\n"

                        + get_matches(False)
                    )


            # --------------------------------------
            # ویرایش نتیجه
            # --------------------------------------

            elif (
                text == "✏️ ویرایش نتیجه"
                and admin
            ):

                if not db["matches"]:

                    send_message(

                        chat_id,

                        "❌ بازی‌ای وجود ندارد."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "edit_result_select"
                    }


                    send_message(

                        chat_id,

                        "✏️ شماره بازی را بفرست:\n\n"

                        + get_matches(False)
                    )


            # --------------------------------------
            # حذف نتیجه
            # --------------------------------------

            elif (
                text == "🗑️ حذف نتیجه"
                and admin
            ):

                if not db["matches"]:

                    send_message(

                        chat_id,

                        "❌ بازی‌ای وجود ندارد."
                    )

                else:

                    states[
                        str(chat_id)
                    ] = {

                        "action":
                        "delete_result"
                    }


                    send_message(

                        chat_id,

                        "🗑️ شماره بازی را بفرست:\n\n"

                        + get_matches(False)
                    )


            # --------------------------------------
            # گلزن
            # --------------------------------------

            elif (
                text == "🥅 ثبت گلزن"
                and admin
            ):

                states[
                    str(chat_id)
                ] = {

                    "action":
                    "add_scorer"
                }


                send_message(

                    chat_id,

                    "🥅 اطلاعات گلزن:\n\n"

                    "نام | تیم | تعداد گل\n\n"

                    "مثال:\n"

                    "مهدی | رئال | 3"
                )


            # --------------------------------------
            # کارت
            # --------------------------------------

            elif (
                text == "🟨🟥 ثبت کارت"
                and admin
            ):

                states[
                    str(chat_id)
                ] = {

                    "action":
                    "add_card"
                }


                send_message(

                    chat_id,

                    "🟨🟥 اطلاعات کارت:\n\n"

                    "بازیکن | تیم | زرد | قرمز\n\n"

                    "مثال:\n"

                    "علی | رئال | 2 | 1"
                )


            # --------------------------------------
            # اطلاعیه
            # --------------------------------------

            elif (
                text == "📢 ارسال اطلاعیه"
                and admin
            ):

                states[
                    str(chat_id)
                ] = {

                    "action":
                    "announce"
                }


                send_message(

                    chat_id,

                    "📢 متن اطلاعیه را بفرست:"
                )


            # --------------------------------------
            # بروزرسانی
            # --------------------------------------

            elif (
                text == "🔄 بروزرسانی"
                and admin
            ):

                send_message(

                    chat_id,

                    "🔄 اطلاعات لیگ بروزرسانی شد.\n\n"

                    + get_table(),

                    MANAGE_MENU
                )


            # --------------------------------------
            # بازگشت
            # --------------------------------------

            elif (
                text == "🔙 بازگشت"
                and admin
            ):

                states.pop(
                    str(chat_id),
                    None
                )


                main_menu(
                    chat_id,
                    True
                )


        # ------------------------------------------
        # offset
        # ------------------------------------------

        next_offset = data.get(
            "next_offset_id"
        )


        if next_offset:

            offset_id = next_offset


        time.sleep(2)


    except Exception as e:

        print(
            "❌ خطا:",
            e
        )

        time.sleep(5)
