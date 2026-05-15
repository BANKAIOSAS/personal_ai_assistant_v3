import json
import socket
import sqlite3
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


class AiManagerMaster:
    def __init__(self):
        self.lm_url = "http://localhost:1234/v1/chat/completions"
        self.ai_port = 1234
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

    def check_server_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(('localhost', self.ai_port))
            sock.close()
            return True
        except socket.error:
            return False

    def ask_ai(self, user_text):
        if not self.check_server_socket():
            return "Server Offline: LM Studio is not running!"

        profile = self.get_profile_data()
        context = ", ".join([f"{r[0]}: {r[1]}" for r in profile]) if profile else "No data"

        try:
            payload = {
                "model": "local",
                "messages": [
                    {"role": "system", "content": f"User info: {context}. Be concise."},
                    {"role": "user", "content": user_text}
                ],
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
            user_text = data.get('text', '')
            ai_response = ai_god.ask_ai(user_text)
            ai_god.save_log(user_text, ai_response)
            return JsonResponse({"answer": ai_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "POST required"}, status=405)

