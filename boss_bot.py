import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from config import *

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY

class BossBot:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self.last_activity = {}  # Отслеживание активности чатов
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("tests", self.tests_command))  # Новая команда
        
        # Обработка всех текстовых сообщений
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Обработка игр и стикеров
        self.app.add_handler(MessageHandler(
            filters.GAME, 
            self.handle_games
        ))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_name = update.effective_user.first_name or "Сотрудник"
        await update.message.reply_text(
            f"Приветствую, {user_name}! 👔\n\n"
            f"Я Александр Барашкин, ваш начальник отдела разработки ПО из компании InPizdec.\n"
            f"Надеюсь на плодотворную работу и качественный код! 💻\n\n"
            f"Помните: тесты — это святое! 🧪"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
👔 **Александр Барашкин, Начальник отдела разработки**
Компания: InPizdec 💼

**Правила:**
• Кодим, а не развлекаемся! 💻
• Тесты обязательны!
• Игры в рабочее время — недопустимы
• Code review проходим всегда
• Говнокод не толерируем

**Команды:**
/start - Представиться
/status - Статус отдела
/tests - Статус тестирования
/help - Эта справка

*Помните: я слежу за покрытием тестами! 👀*
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус отдела"""
        chat_id = update.effective_chat.id
        
        status_messages = [
            "📊 Отдел разработки работает в штатном режиме",
            "⚠️ Заметил некоторые нарушения в коде...",
            "✅ Девелоперы показывают хорошие результаты",
            "🔥 Горячая пора! Все на кодинг!",
            "😤 Некоторые салаги опять говнокод пишут!",
            "💻 Билды собираются стабильно",
            "🧪 Тесты в основном зеленые"
        ]
        
        await update.message.reply_text(
            f"**Статус отдела разработки InPizdec:**\n"
            f"{random.choice(status_messages)}\n\n"
            f"Начальник: Александр Барашкин 👔\n"
            f"Время: {datetime.now().strftime('%H:%M, %d.%m.%Y')}"
        )
    
    async def tests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /tests - проверка статуса тестов"""
        test_status = [
            "📊 Покрытие тестами: 73% (надо больше!)",
            "🔴 Unit-тесты падают! Исправляйте!",
            "🟡 Интеграционные тесты пишутся...",
            "✅ Все тесты зеленые! Молодцы!",
            "💀 Тестов нет вообще! Ужас!",
            "🧪 E2E тесты в разработке",
            "⚠️ Тесты есть, но они врут!",
            "🎯 Покрытие растет, но медленно",
            "🔧 Тесты рефакторятся"
        ]
        
        await update.message.reply_text(
            f"**Статус тестирования InPizdec:**\n"
            f"{random.choice(test_status)}\n\n"
            f"💻 **Напоминание:** Без тестов в прод не пойдет!\n"
            f"🎯 **Цель:** 100% покрытие к пятнице!"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        try:
            message = update.message.text.lower()
            user_name = update.effective_user.first_name or "Сотрудник"
            chat_id = update.effective_chat.id
            
            # Обновляем время последней активности
            self.last_activity[chat_id] = datetime.now()
            
            # Проверяем триггеры
            response = await self.check_triggers(message, user_name)
            
            if response:
                await update.message.reply_text(response)
            else:
                # Обычный ответ через ИИ
                ai_response = await self.get_ai_response(message, user_name)
                await update.message.reply_text(ai_response)
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text("Что-то я не понял... Повторите доклад! 🤔")
    
    async def handle_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка игр"""
        user_name = update.effective_user.first_name or "Сотрудник"
        
        angry_responses = [
            f"{user_name}! А ну прекратили играть! Тесты писать надо! 🧪",
            f"Опять развлечения в рабочее время, {user_name}?! 🎮➡️💻",
            f"{user_name}, я же говорил — никаких игр! КОДИТЬ! 💻",
            f"Поле чудес?! {user_name}, единственное чудо здесь — что билд собирается! 🤦‍♂️",
            f"Игры в рабочее время? {user_name}, может тебе в геймдев уйти? 😡",
            f"Вместо казино лучше unit-тесты писать, {user_name}! 🎰➡️🧪"
        ]
        
        await update.message.reply_text(random.choice(angry_responses))
    
    async def check_triggers(self, message: str, user_name: str) -> str:
        """Проверка на триггерные слова"""
        
        # Проверка на игровые триггеры
        if any(trigger in message for trigger in GAME_TRIGGERS):
            responses = [
                f"{user_name}! Хватит играть! Тесты писать надо! 🧪",
                f"А ну-ка убрали игрушки, {user_name}! InPizdec не геймдев! 💻",
                f"{user_name}, развлечения после code review! Сейчас — багфиксы! 🐛",
                f"Игры?! {user_name}, может тебе в QA перевестись? 😠",
                f"Поиграть хочешь? Вот тебе unit-тесты — поиграй с ними! 🎮➡️🧪"
            ]
            return random.choice(responses)
        
        # Проверка на IT-триггеры (специальные реакции на код/тесты)
        if any(trigger in message for trigger in IT_TRIGGERS):
            if 'тест' in message or 'покрытие' in message:
                return random.choice(TEST_PHRASES)
            elif 'код' in message or 'баг' in message:
                return random.choice(CODE_PHRASES)
        
        # Проверка на плохие слова
        if any(bad_word in message for bad_word in BAD_WORDS):
            return f"{user_name} УВОЛЕН! 🔥 (Но завтра приходи, код сам себя не напишет 😏)"
        
        # Проверка на хорошие слова
        if any(good_word in message for good_word in GOOD_WORDS):
            return f"{user_name} ПОВЫШЕН! 📈 Теперь ты Senior Developer! 👏"
        
        return None
    
    async def get_ai_response(self, message: str, user_name: str) -> str:
        """Получение ответа от ИИ"""
        try:
            # Добавляем контекст с именем пользователя
            contextualized_message = f"Сотрудник {user_name} пишет: {message}"
            
            response = openai.ChatCompletion.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": AI_INSTRUCTIONS},
                    {"role": "user", "content": contextualized_message}
                ],
                max_tokens=300,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Ошибка ИИ: {e}")
            boss_responses = [
                f"{user_name}, не понял вашего доклада! Повторите четче! 🤔",
                "Говорите яснее, сотрудник! 🗣️",
                "Что-то я отвлекся... Повторите еще раз! ☕",
                f"{user_name}, код работает, а вы — нет? 🤨",
                "Может билд пересобрать? А то не понимаю ничего! 🔄"
            ]
            return random.choice(boss_responses)
    
    async def random_boss_messages(self):
        """Случайные сообщения начальника"""
        while True:
            try:
                await asyncio.sleep(random.randint(1800, 3600))  # 30-60 минут
                
                # Проверяем все чаты на бездействие
                current_time = datetime.now()
                for chat_id, last_activity in self.last_activity.items():
                    if current_time - last_activity > timedelta(minutes=30):
                        try:
                            await self.app.bot.send_message(
                                chat_id=chat_id,
                                text=random.choice(RANDOM_PHRASES)
                            )
                        except Exception as e:
                            logger.error(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
                            
            except Exception as e:
                logger.error(f"Ошибка в random_boss_messages: {e}")
    
    async def start_random_messages(self):
        """Запуск фоновых случайных сообщений"""
        asyncio.create_task(self.random_boss_messages())
    
    def run(self):
        """Запуск бота"""
        logger.info("Александр Барашкин приступает к руководству отделом разработки! 👔💻")
        
        # Запускаем фоновые задачи
        asyncio.create_task(self.start_random_messages())
        
        # Запускаем бота
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    boss = BossBot()
    boss.run()
