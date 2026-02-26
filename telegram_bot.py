import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8356016044:AAF78UsyXUZ9roY5AbsKIpJMPUlzl2wL9NA")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "478833721")  # Ваш Chat ID

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID
        
    async def send_message(self, message):
        """Отправить сообщение в Telegram"""
        if not self.chat_id:
            print("Telegram chat ID не установлен. Используйте /set_chat_id для установки.")
            return False
            
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except TelegramError as e:
            print(f"Ошибка отправки сообщения в Telegram: {e}")
            return False
    
    async def send_bot_status(self, status):
        """Отправить статус бота"""
        if not status:
            message = "❌ Бот не работает"
        else:
            running = "🟢 Работает" if status.get("running") else "🔴 Остановлен"
            timeouts = f"⏱ Таймауты: {status.get('timeout_count', 0)}"
            restarts = f"🔄 Перезапуски: {status.get('restart_count', 0)}"
            error = f"❌ Ошибка: {status.get('error', 'Нет')}" if status.get('error') else ""
            
            message = f"""📊 Статус Attendance Bot:
{running}
{timeouts}
{restarts}
{error}"""
        
        await self.send_message(message)
    
    async def send_bot_started(self):
        """Отправить уведомление о запуске"""
        await self.send_message("🚀 Attendance Bot запущен!")
    
    async def send_bot_stopped(self):
        """Отправить уведомление об остановке"""
        await self.send_message("🛑 Attendance Bot остановлен")
    
    async def send_timeout_warning(self, timeout_count):
        """Отправить предупреждение о таймауте"""
        await self.send_message(f"⚠️ Таймаут #{timeout_count}. Бот пытается переподключиться...")
    
    async def send_bot_restarted(self, restart_count):
        """Отправить уведомление о перезапуске"""
        await self.send_message(f"🔄 Бот перезапущен (#{restart_count}) из-за таймаутов")
    
    async def send_attendance_success(self, count):
        """Отправить уведомление об успешной отметке"""
        await self.send_message(f"✅ ✅ ✅ Успешно отмечено: {count} кноп(ки/ок)!")
    
    async def send_error(self, error_message):
        """Отправить уведомление об ошибке"""
        await self.send_message(f"❌ Ошибка: {error_message}")

# Глобальный экземпляр бота
telegram_bot = TelegramBot()

async def test_telegram():
    """Тестовая функция для проверки работы бота"""
    if telegram_bot.chat_id:
        await telegram_bot.send_message("🔔 Тестовое сообщение от Attendance Bot")
        return True
    return False