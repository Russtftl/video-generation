
---

# 🎬 AI Video Generator (Sora-2)

Проект для генерации видео через модель **sora-2** с использованием OpenAI API (через proxyapi).

Поддерживает 3 режима работы:

* 🌐 Web API (Flask)
* 🤖 Telegram Bot
* 🖥 CLI (консольный запуск)

---

# 🚀 Возможности

* Генерация видео по текстовому описанию
* Отслеживание прогресса генерации
* Асинхронная обработка задач (через threading)
* Автоматическое скачивание готового видео
* Прогресс-бар в Telegram
* REST API для интеграций

---

# 🏗 Архитектура проекта

```
project/
│
├── app.py            # Flask API сервер
├── bot.py            # Telegram бот
├── request.py        # CLI-скрипт генерации
├── requirements.txt
├── videos/           # Папка для сохранения видео (создаётся автоматически)
└── .env              # Переменные окружения
```

---

# ⚙️ Установка

## 1️⃣ Клонирование проекта

```bash
git clone <repo_url>
cd project
```

## 2️⃣ Установка зависимостей

```bash
pip install -r requirements.txt
```

Содержимое зависимостей:


---

# 🔐 Настройка переменных окружения

Создайте файл `.env`:

```env
API_KEY=your_openai_api_key
BOT_TOKEN=your_telegram_bot_token
```

Используется:

* `API_KEY` — ключ OpenAI API
* `BOT_TOKEN` — токен Telegram-бота

---

# 🌐 Запуск Flask API

Файл: 

```bash
python app.py
```

Сервер запустится на:

```
http://127.0.0.1:5000
```

---

## 📌 API endpoints

### POST `/generate`

Создание задачи генерации.

```json
{
  "prompt": "Крупный план чашки кофе на столе"
}
```

Ответ:

```json
{
  "task_id": "uuid"
}
```

---

### GET `/status/<task_id>`

Получение статуса задачи.

Ответ:

```json
{
  "status": "in_progress",
  "progress": 45,
  "message": "Обработка",
  "video_id": "..."
}
```

---

### GET `/download/<task_id>`

Скачивание готового видео.

Видео сохраняется в папку:

```
/videos/video_<task_id>.mp4
```

---

# 🤖 Telegram Bot

Файл: 

## Запуск:

```bash
python bot.py
```

После запуска:

* Отправьте боту текстовое описание
* Получите прогресс-бар
* После завершения — видео автоматически отправится в чат

### Особенности

* Один активный рендер на пользователя
* Автоматическое удаление файла после отправки
* Прогресс-бар с emoji

---

# 🖥 CLI режим

Файл: 

```bash
python request.py
```

Или изменить prompt внутри файла.

Вывод в консоли:

```
Обработка: [=======-------] 45.0%
```

После завершения:

```
video.mp4 сохранён
```

---

# 🧠 Используемая модель

```
model="sora-2"
seconds="4"
```

Видео длительностью 4 секунды.

---

# 🛠 Технические детали

### Flask API

* Потокобезопасное хранилище задач
* Асинхронная генерация через threading
* Автоматическое создание папки videos/
* Отдача файла через send_file()

### Telegram Bot

* pyTelegramBotAPI
* Редактирование сообщения для отображения прогресса
* Автоудаление видео после отправки

---

# ⚠️ Ограничения

* Хранилище задач in-memory (перезапуск сервера очищает задачи)
* Не предназначено для high-load production
* Для production рекомендуется:

  * Redis вместо dict
  * Celery или RQ вместо threading
  * Gunicorn + Nginx

---

# 📦 Production рекомендации

```bash
pip install gunicorn
gunicorn app:app
```

Рекомендуется:

* Добавить rate limiting
* Добавить логирование
* Настроить хранение видео в S3
* Очистку старых файлов

---

# 📝 Пример prompt

```
Minimalist 3D logo animation. Text 'VITAJEDI' in clean sans-serif font centered below a translucent DNA helix slowly rotating on a horizontal axis. Lighting blends emerald green and scientific blue. Clean white background, studio lighting.
```

---

# 📄 Лицензия

Проект предназначен для образовательных и демонстрационных целей.

---

