from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# --------------------------
# Paths / storage
# --------------------------
BASE_DIR = Path(__file__).resolve().parent
VIDEO_DIR = BASE_DIR / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

# In-memory task store (для прода лучше Redis/DB)
tasks: Dict[str, Dict[str, Any]] = {}
tasks_lock = threading.Lock()


def video_file_path(task_id: str) -> Path:
    return VIDEO_DIR / f"video_{task_id}.mp4"


def set_task(task_id: str, **updates: Any) -> None:
    """Потокобезопасное обновление задачи."""
    with tasks_lock:
        if task_id not in tasks:
            tasks[task_id] = {}
        tasks[task_id].update(updates)


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with tasks_lock:
        task = tasks.get(task_id)
        return dict(task) if task else None


# --------------------------
# Video generation worker
# --------------------------
def generate_video_with_progress(prompt: str, task_id: str) -> None:
    client = OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url="https://api.proxyapi.ru/openai/v1",
    )

    try:
        set_task(
            task_id,
            status="started",
            progress=0,
            message="Генерация видео началась",
            video_id=None,
        )

        video = client.videos.create(
            model="sora-2",
            prompt=str(prompt),
            seconds="4",
        )

        set_task(task_id, video_id=video.id)

        # Poll status
        while getattr(video, "status", None) in ("in_progress", "queued"):
            status = getattr(video, "status", "in_progress")
            progress = getattr(video, "progress", 0) or 0
            status_text = "В очереди" if status == "queued" else "Обработка"

            set_task(
                task_id,
                status=status,
                progress=progress,
                message=status_text,
                video_id=video.id,
            )

            time.sleep(10)
            video = client.videos.retrieve(video.id)

        # Final state
        if getattr(video, "status", None) == "failed":
            err = getattr(video, "error", None)
            message = getattr(err, "message", "Генерация видео не удалась")
            set_task(
                task_id,
                status="failed",
                progress=100,
                message=message,
                video_id=video.id,
            )
            return

        # Download content
        set_task(
            task_id,
            status="downloading",
            progress=95,
            message="Скачивание видео...",
            video_id=video.id,
        )

        content = client.videos.download_content(video.id, variant="video")

        path = video_file_path(task_id)
        content.write_to_file(str(path))

        if not path.exists():
            raise RuntimeError("Файл не был создан после сохранения")

        set_task(
            task_id,
            status="completed",
            progress=100,
            message="Генерация завершена",
            video_id=video.id,
            video_path=str(path),  # абсолютный/нормализованный путь
        )

    except Exception as e:
        set_task(
            task_id,
            status="error",
            progress=0,
            message=f"Ошибка: {e}",
        )


# --------------------------
# Routes
# --------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Промпт не может быть пустым"}), 400

    task_id = str(uuid.uuid4())

    set_task(
        task_id,
        status="queued",
        progress=0,
        message="Задача поставлена в очередь",
        video_id=None,
    )

    thread = threading.Thread(target=generate_video_with_progress, args=(prompt, task_id), daemon=True)
    thread.start()

    return jsonify({"task_id": task_id})


@app.route("/status/<task_id>")
def status(task_id: str):
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    return jsonify(task)


@app.route("/download/<task_id>")
def download(task_id: str):
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404

    video_path = task.get("video_path")

    # fallback: ищем по стандартному имени в VIDEO_DIR
    if not video_path:
        possible = video_file_path(task_id)
        if possible.exists():
            video_path = str(possible)
            set_task(task_id, video_path=video_path)

    if not video_path:
        return jsonify(
            {
                "error": "Путь к видео не найден",
                "status": task.get("status"),
                "message": task.get("message", "Ожидание..."),
            }
        ), 400

    path = Path(video_path)
    if not path.exists():
        return jsonify(
            {
                "error": "Файл не найден на диске",
                "video_path": str(path),
                "status": task.get("status"),
            }
        ), 404

    # Если файл существует — отдаём его, даже если статус ещё 'downloading'
    return send_file(str(path), as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    app.run(host = '0.0.0.0',debug = True, port = 5000)