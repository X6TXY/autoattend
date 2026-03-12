# kbtu-attendance-bot

## Описание

Бот для автоматической отметки посещаемости на порталах KBTU:  
- **pge.kbtu.kz** — магистратура  
- **wsp.kbtu.kz** — бакалавриат  
Работает на Python + Selenium WebDriver.

---

## Функции

- Вход на портал с помощью логина и пароля
- Выбор портала при запуске (`pge` или `wsp`)
- Поиск и отметка по всем найденным дисциплинам
- Логирование результата для каждого предмета
- Постоянный цикл: ждет появления новых дисциплин, сам не выключается

---

## Важно
- Скрипт продолжает работу даже если нет дисциплин для отметки — просто ждет и пробует снова.
- Скрипт перезапускается автоматически при критической ошибке (внутренний watchdog в `main.py`).
- Ошибки отправляются в Sentry (DSN уже задан в коде, при необходимости можно переопределить через `SENTRY_DSN`).

---

## Установка

1. Клонируйте проект:
    ```bash
    git clone https://github.com/gabdylgaziz/kbtu-attendance-bot.git
    cd kbtu-attendance-bot
    ```

2. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```
    > Для работы нужен установленный [Google Chrome](https://www.google.com/chrome/) и [ChromeDriver](https://chromedriver.chromium.org/downloads) (ВАЖНО: версия браузера и драйвера должна быть совместимой, например: Google Chrome: 145.0.7632.46 и chromedriver: 145.0.7632.45)

3. Укажите логин и пароль (KBTU):
    - Создайте файл `.env`:
      ```
      KBTU_LOGIN=ваш_логин
      KBTU_PASSWORD=ваш_пароль
      PORTAL=wsp
      SENTRY_DSN=
      RESTART_DELAY_SEC=5
      RESTART_MAX_DELAY_SEC=60
      ```
      > `PORTAL` может быть `wsp` (бакалавриат) или `pge` (магистратура). По умолчанию используется `wsp`.
      > Можно переопределить `SENTRY_DSN` своим DSN или выключить Sentry значением `SENTRY_DSN=off`.
      > `RESTART_DELAY_SEC` и `RESTART_MAX_DELAY_SEC` управляют задержкой между перезапусками.
    - **ИЛИ** экспортируйте переменные окружения:
      ```bash
      export KBTU_LOGIN=ваш_логин
      export KBTU_PASSWORD=ваш_пароль
      export PORTAL=wsp
      export SENTRY_DSN=ваш_dsn
      export RESTART_DELAY_SEC=5
      export RESTART_MAX_DELAY_SEC=60
      ```

---

## Запуск

```bash
python main.py
```

## Запуск на Railway

1. Убедитесь, что в проекте есть `Dockerfile` (он уже добавлен).
2. Запушьте репозиторий в GitHub.
3. В Railway создайте проект через **Deploy from GitHub Repo**.
4. В `Variables` добавьте:
   - `KBTU_LOGIN`
   - `KBTU_PASSWORD`
   - `PORTAL` (`wsp` или `pge`)
   - `SENTRY_DSN` (опционально, для мониторинга ошибок)
   - `RESTART_DELAY_SEC` (опционально, по умолчанию `5`)
   - `RESTART_MAX_DELAY_SEC` (опционально, по умолчанию `60`)
5. Railway соберет Docker-образ и запустит бота как worker-процесс.
6. Проверяйте работу в логах Railway (появятся строки с предметами/статусами).
7. В Service Settings включите `Restart policy: On Failure` (или `Always`, если доступно на вашем плане).

> Публичный домен не нужен, так как бот не поднимает веб-сервер.
---

## Выбор портала

- Укажите `PORTAL=wsp` для бакалавриата.
- Укажите `PORTAL=pge` для магистратуры.
- Бот автоматически выполнит вход и начнет отмечать предметы.

## Структура проекта
```
main.py
config.py
handlers/
└── attend_handler.py
models/
└── card.py
services/
└── selenium.py
requirements.txt
```

## Пример вывода
```
----------------------------------------
Предмет: Основы машинного обучения
Преподаватель: Иванов И.И.
Время: 14:00 - 15:30
Статус: Успешно нажата
----------------------------------------
Нет доступных дисциплин для отметки

```
