import threading
import time
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main import attend_bot
from telegram_bot import telegram_bot

# Создаем новый event loop для Telegram в отдельном потоке
telegram_loop = None

def run_telegram_loop():
    global telegram_loop
    telegram_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(telegram_loop)
    telegram_loop.run_forever()

# Запускаем Telegram loop в отдельном потоке
telegram_thread = threading.Thread(target=run_telegram_loop, daemon=True)
telegram_thread.start()

def run_async(coro):
    """Запустить async функцию в Telegram loop"""
    future = asyncio.run_coroutine_threadsafe(coro, telegram_loop)
    return future.result(timeout=10)

app = FastAPI()

# Глобальные переменные для отслеживания состояния бота
bot_status = {"running": False, "last_check": None, "error": None, "timeout_count": 0, "restart_count": 0}
bot_thread = None
bot_credentials = {"username": None, "password": None}
MAX_TIMEOUTS_BEFORE_RESTART = 3  # Количество таймаутов перед перезапуском


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Attendance Bot API", "status": bot_status}


@app.get("/health")
async def health():
    return {"status": "healthy", "bot_running": bot_status["running"]}


@app.get("/attend")
async def attend(username: str, password: str):
    global bot_thread, bot_status, bot_credentials
    
    bot_credentials["username"] = username
    bot_credentials["password"] = password
    
    if bot_status["running"]:
        return {"message": "Bot is already running", "status": bot_status}
    
    try:
        bot_status["running"] = True
        bot_status["error"] = None
        bot_status["timeout_count"] = 0
        bot_status["restart_count"] = 0
        
        def run_bot():
            global bot_status, bot_credentials
            try:
                attend_bot(bot_credentials["username"], bot_credentials["password"])
            except Exception as e:
                bot_status["error"] = str(e)
                bot_status["running"] = False
                
                # Отправляем уведомление об ошибке в Telegram
                try:
                    run_async(telegram_bot.send_error(str(e)))
                except Exception as telegram_error:
                    print(f"Telegram error: {telegram_error}")
                
                # Проверяем на таймауты
                if "timeout" in str(e).lower() or "таймаут" in str(e).lower():
                    bot_status["timeout_count"] += 1
                    try:
                        run_async(telegram_bot.send_timeout_warning(bot_status["timeout_count"]))
                    except Exception as telegram_error:
                        print(f"Telegram error: {telegram_error}")
                    
                    if bot_status["timeout_count"] >= MAX_TIMEOUTS_BEFORE_RESTART:
                        bot_status["restart_count"] += 1
                        bot_status["timeout_count"] = 0
                        print(f"Таймаут достиг лимита. Перезапуск бота (#{bot_status['restart_count']})...")
                        try:
                            run_async(telegram_bot.send_bot_restarted(bot_status["restart_count"]))
                        except Exception as telegram_error:
                            print(f"Telegram error: {telegram_error}")
                        time.sleep(5)  # Небольшая пауза перед перезапуском
                        bot_status["running"] = True
                        bot_status["error"] = None
                        try:
                            run_async(telegram_bot.send_bot_started())
                        except Exception as telegram_error:
                            print(f"Telegram error: {telegram_error}")
                        # Рекурсивный перезапуск
                        run_bot()
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Отправляем уведомление о запуске в Telegram
        try:
            run_async(telegram_bot.send_bot_started())
        except Exception as telegram_error:
            print(f"Telegram error on start: {telegram_error}")
        
        return {"message": "Bot started successfully", "status": bot_status}
    except Exception as e:
        bot_status["running"] = False
        bot_status["error"] = str(e)
        return {"message": f"Error starting bot: {e}", "status": bot_status}


@app.get("/status")
async def status():
    return {"status": bot_status}


@app.get("/restart")
async def restart_bot():
    global bot_status, bot_thread, bot_credentials
    
    if not bot_credentials["username"] or not bot_credentials["password"]:
        return {"message": "No credentials stored. Please start bot first with /attend", "status": bot_status}
    
    # Останавливаем текущий бот
    was_running = bot_status["running"]
    bot_status["running"] = False
    
    if was_running:
        # Ждем немного пока остановится
        await asyncio.sleep(2)
    
    # Перезапускаем бот
    return await attend(bot_credentials["username"], bot_credentials["password"])


@app.get("/reset_timeout")
async def reset_timeout():
    global bot_status
    bot_status["timeout_count"] = 0
    return {"message": "Timeout count reset", "status": bot_status}


@app.get("/telegram_status")
async def send_telegram_status():
    """Отправить статус бота в Telegram"""
    try:
        run_async(telegram_bot.send_bot_status(bot_status))
        return {"message": "Status sent to Telegram", "status": bot_status}
    except Exception as e:
        return {"message": f"Error sending to Telegram: {e}", "status": bot_status}


@app.get("/set_chat_id")
async def set_chat_id(chat_id: str):
    """Установить Telegram chat ID для уведомлений"""
    telegram_bot.chat_id = chat_id
    try:
        run_async(telegram_bot.send_message("✅ Chat ID установлен! Теперь вы будете получать уведомления от Attendance Bot."))
        return {"message": f"Chat ID set to {chat_id}", "chat_id": chat_id}
    except Exception as e:
        return {"message": f"Error setting chat ID: {e}", "chat_id": chat_id}


@app.get("/test_telegram")
async def test_telegram():
    """Тестовая отправка сообщения в Telegram"""
    try:
        success = run_async(telegram_bot.send_message("🔔 Тестовое сообщение от Attendance Bot - все работает!"))
        if success:
            return {"message": "Test message sent successfully"}
        else:
            return {"message": "Failed to send test message - check chat ID"}
    except Exception as e:
        return {"message": f"Error sending test message: {e}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
