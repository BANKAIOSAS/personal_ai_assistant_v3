import os
from dotenv import load_dotenv
import json
import socket
import sqlite3
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

load_dotenv()

class AiManagerMaster:
    def __init__(self):
        self.lm_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1/chat/completions')
        self.ai_port = int(os.getenv('LM_STUDIO_PORT', 1234))
        self.db = 'db.sqlite3'
        self._init_table()

    def _init_table(self):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chat_logs (user_msg TEXT, ai_msg TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_profile (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, day TEXT, discipline TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, name TEXT, status BOOLEAN)")
        conn.commit()
        conn.close()

    def _run_select(self, query):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_profile_data(self):
        return self._run_select("SELECT key, value FROM user_profile")

    def get_tasks_data(self):
        return self._run_select("SELECT name, status FROM tasks")

    def get_schedule_data(self):
        return self._run_select("SELECT day, discipline FROM schedule ORDER BY id")

    def add_task(self, name):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (name, status) VALUES (?, 0)", (name, ))
        conn.commit()
        conn.close()

    def complete_task(self, name):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 1 WHERE name LIKE ?", (f'%{name}%',))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def set_profile(self, key, value):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO user_profiles VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def add_schedule(self, day, discipline):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schedule (day, discipline) VALUES (?, ?)", (day, discipline))
        conn.commit()
        conn.close()

    def clear_table(self, table_name):
        allowed = {'tasks', 'user_profile', 'schedule', 'chat_logs'}
        if table_name not in allowed:
            return False
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
        conn.close()
        return True

    def check_server_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(('localhost', self.ai_port))
            sock.close()
            return True
        except socket.error:
            return False

    def get_chat_history(self, limit = 5):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("SELECT user_msg, ai_msg FROM chat_logs ORDER BY rowid DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return list(reversed(rows))

    def ask_ai(self, user_text):
        if not self.check_server_socket():
            return "Server Offline: LM Studio is not running!"

        profile = self.get_profile_data()
        context = ", ".join([f"{r[0]}: {r[1]}" for r in profile]) if profile else "No data"

        history = self.get_chat_history(limit=5)
        messages = [{"role": "system", "content": f"User info: {context}. Be concise."}]

        for user_msg, ai_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_msg})

        messages.append({"role": "user", "content": user_text})

        try:
            payload = {
                "model": "local",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150
            }
            response = requests.post(self.lm_url, json=payload, timeout=1000)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"AI Error: {e}"

    def save_log(self, text, response):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_logs VALUES (?, ?)", (text, response))
        conn.commit()
        conn.close()


ai_god = AiManagerMaster()


def chat_page(request):
    return render(request, 'chat.html')


@csrf_exempt
def api_get_answer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_text = data.get('text', '').strip()

            if not user_text:
                return JsonResponse({"error": "Empty Message"}, status=400)

            ai_response = ai_god.ask_ai(user_text)
            ai_god.save_log(user_text, ai_response)
            return JsonResponse({"answer": ai_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "POST required"}, status=405)

