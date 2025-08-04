# boss_bot.py
import logging
import asyncio
import random
from datetime import datetime, timedelta
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai

# ─────────── окружение ───────────
load_dotenv()
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден!")
if not GOOGLE_AI_API_KEY:
    raise ValueError("GOOGLE_AI_API_KEY не найден!")

genai.configure(api_key=GOOGLE_AI_API_KEY)

# ─────────── настройки ───────────
MAX_CHARS   = 700           # макс. символов в ответе
MAX_HISTORY = 8             # сколько реплик запоминать
AI_MODEL    = "gemini-2.0-flash"

AI_INSTRUCTIONS = """
Ты Александр Барашкин, начальник отдела разработки ПО в компании InPizdec.
(остальные пункты инструкции без изменений)
Ограничивайся двумя-тремя короткими предлжениями (желательно не более 300 символов).
"""

# ─────────── триггеры / фразы ───────────
GAME_TRIGGERS = ["игра","играть","поиграть","game","поле чудес","развлечение","fun","отдых","перерыв","я устал","казино","ставки","играем"]
IT_TRIGGERS   = ["код","баг","фича","билд","деплой","тест","говнокод","костыль","рефакторинг","коммит","пуш","мерж","дедлайн","code review","покрытие","юнит тесты","интеграционные тесты"]
BAD_WORDS     = ["дурак","идиот","плохой","ужасный","начальник херовый","барашкин","уволить тебя","плохой бос","говно начальник"]
GOOD_WORDS    = ["хороший","отличный","классный","лучший","крутой начальник","спасибо","благодарю","молодец","умница","крутой бос"]

RANDOM_PHRASES = [
    "Девелоперы, кодите? 💻","Тесты кто писать будет? 🧪","Может уволить всех и нанять индусов? 🤔",
    "Где unit-тесты?! 📋","Опять говнокод пишете? 💩","Дедлайн через час, а у вас билд не собирается! ⏰",
    "Code review делали вообще? 👀","В прод без тестов не пойдет! 🚫","Документацию обновили? 📚",
    "Так-так-так… что тут у нас? 🤔","Салаги, работаете? 😤","InPizdec требует результатов! 💼"
]
TEST_PHRASES = ["А ну-ка тесты делать! 🧪","Где покрытие тестами?! 📊","Когда тесты покроют всё приложение? 🎯","Unit-тесты писали? 🔍","Интеграционные тесты где? 🔗"]
CODE_PHRASES = ["Говнокод опять пишете? 💩","Code review прошли? 👀","Рефакторинг когда планируете? 🔧","Костыли убрали? 🩼"]

# обращение к боту
CALL_ME = ["начальник","барашкин","саня барашкин","alexander","alexandr","alex","boss"]

# ─────────── логирование ───────────
logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────── класс бота ───────────
class BossBot:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self.last_activity: dict[int, datetime] = {}
        self.chat_history: dict[int, list[str]] = {}
        self.model = genai.GenerativeModel(AI_MODEL, system_instruction=AI_INSTRUCTIONS)
        self._setup_handlers()

    # ---------- helpers ----------
    def _trim(self, text: str) -> str:
        return text if len(text) <= MAX_CHARS else text[:MAX_CHARS].rsplit(" ", 1)[0] + "…"

    def post(self, text: str, user: str) -> str:
        return self._trim(text.replace("ИМЯ", user).replace("{ИМЯ}", user))

    def _addressed(self, u: Update) -> bool:
        txt = (u.message.text or "").lower()
        mentioned = any(name in txt for name in CALL_ME)
        replied   = u.message.reply_to_message and u.message.reply_to_message.from_user.id == self.app.bot.id
        return mentioned or replied

    def _remember(self, chat: int, role: str, text: str):
        hist = self.chat_history.setdefault(chat, [])
        hist.append(f"{role}: {text}")
        if len(hist) > MAX_HISTORY:
            hist.pop(0)

    # ---------- telegram handlers ----------
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start",   self.cmd_start))
        self.app.add_handler(CommandHandler("help",    self.cmd_help))
        self.app.add_handler(CommandHandler("status",  self.cmd_status))
        self.app.add_handler(CommandHandler("tests",   self.cmd_tests))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))
        self.app.add_handler(MessageHandler(filters.GAME, self.on_game))

    async def cmd_start(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        name = u.effective_user.first_name or "Сотрудник"
        await u.message.reply_text(f"Приветствую, {name}! 👔\nЯ Александр Барашкин. Помните: тесты — это святое! 🧪")

    async def cmd_help(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("Список команд: /start /status /tests /help", parse_mode="Markdown")

    async def cmd_status(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        msg = random.choice(["📊 Отдел работает штатно","⚠️ Нашёл косяки в коде","🔥 Горячая пора! Все на кодинг!"])
        await u.message.reply_text(msg)

    async def cmd_tests(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text(random.choice(TEST_PHRASES))

    # ---------- main message ----------
    async def on_text(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        try:
            if not self._addressed(u):
                return

            chat_id   = u.effective_chat.id
            user_name = u.effective_user.first_name or "Сотрудник"
            msg       = u.message.text.lower()
            self.last_activity[chat_id] = datetime.now()
            self._remember(chat_id, "user", msg)

            trig = self._check_triggers(msg, user_name)
            if trig:
                self._remember(chat_id, "boss", trig)
                await u.message.reply_text(trig)
                return

            answer = await self._gpt(chat_id, msg, user_name)
            self._remember(chat_id, "boss", answer)
            await u.message.reply_text(answer)

        except Exception as e:
            logger.error("on_text error: %s", e)
            await u.message.reply_text("Что-то я не понял… Повторите доклад! 🤔")

    # ---------- triggers ----------
    def _check_triggers(self, msg: str, user: str) -> str | None:
        if any(t in msg for t in GAME_TRIGGERS):
            return random.choice([f"{user}! Хватит играть! Тесты писать надо! 🧪", f"А ну-ка убрали игрушки, {user}! 💻"])
        if any(t in msg for t in IT_TRIGGERS):
            return random.choice(TEST_PHRASES if "тест" in msg or "покрытие" in msg else CODE_PHRASES)
        if any(w in msg for w in BAD_WORDS):
            return f"{user} УВОЛЕН! 🔥 (Но завтра приходи, код сам себя не напишет 😏)"
        if any(w in msg for w in GOOD_WORDS):
            return f"{user} ПОВЫШЕН! 📈 Теперь ты Senior Developer! 👏"
        return None

    # ---------- LLM ----------
    async def _gpt(self, chat: int, msg: str, user: str) -> str:
        history = "\n".join(self.chat_history.get(chat, []))
        prompt  = f"{history}\nСотрудник {user} пишет: {msg}"
        try:
            resp = self.model.generate_content(prompt)
            return self.post(resp.text.strip(), user)
        except Exception as e:
            logger.error("LLM error: %s", e)
            return self.post(random.choice(["Говорите яснее, сотрудник! 🗣️","Повторите ещё раз, не расслышал ☕"]), user)

    # ---------- games ----------
    async def on_game(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        user = u.effective_user.first_name or "Сотрудник"
        await u.message.reply_text(f"{user}! А ну прекратили играть! Тесты писать надо! 🧪")

    # ---------- idle messages ----------
    async def _idle_loop(self):
        while True:
            await asyncio.sleep(random.randint(1_800, 3_600))
            now = datetime.now()
            for chat, last in list(self.last_activity.items()):
                if now - last > timedelta(minutes=30):
                    try:
                        await self.app.bot.send_message(chat, random.choice(RANDOM_PHRASES))
                    except Exception as e:
                        logger.error("idle send error: %s", e)

    # ---------- run ----------
    async def run_async(self):
        logger.info("Барашкин запущен!")
        asyncio.create_task(self._idle_loop())
        async with self.app:
            await self.app.start()
            await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await asyncio.Event().wait()

    def run(self):
        asyncio.run(self.run_async())

# ─────────── main ───────────
if __name__ == "__main__":
    BossBot().run()
