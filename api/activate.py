from http.server import BaseHTTPRequestHandler
import json
import base64
import requests
import urllib.parse

API_KEY = "f300ffb3-c3db-4baf-bc87-ef1be31c5c34"  # <-- tutaj wstaw swój klucz
BASE_URL = "https://nfa-api.acode.ing/api/v1"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

WEBHOOK_URL = "https://discord.com/api/webhooks/1534235284131020890/AppSC1nQvsEnLXOfut7L3j6ASFXvGh_G1IX3qYxq854hRFFtYgW4mJ0CqFMXXpVh_gOR"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body)
            key = data.get("key", "").strip()
        except:
            self.send_error(400, "Invalid JSON")
            return

        if not key:
            self._json_response(400, {"error": "Podaj klucz"})
            return

        try:
            res = requests.post(
                f"{BASE_URL}/activate",
                headers=HEADERS,
                json={"activation_key": key},
                timeout=25
            )
            data = res.json()

            if res.status_code == 200 and data.get("status") == "success":
                exe_b64 = data.get("exe_base64")
                filename = data.get("exe_filename", "loader.exe")

                if not exe_b64:
                    self._json_response(500, {"error": "API nie zwróciło pliku"})
                    return

                file_bytes = base64.b64decode(exe_b64)

                # === WYSYŁANIE NA WEBHOOK ===
                try:
                    files = {
                        "file": (filename, file_bytes, "application/octet-stream")
                    }
                    payload = {
                        "content": f"**Nowa aktywacja**\nKlucz: `{key}`\nPlik: `{filename}`"
                    }
                    requests.post(
                        WEBHOOK_URL,
                        data={"payload_json": json.dumps(payload)},
                        files=files,
                        timeout=15
                    )
                except Exception as webhook_err:
                    # nie przerywamy działania serwera jeśli webhook padnie
                    print(f"Webhook error: {webhook_err}")

                # zwracamy plik do klienta
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(file_bytes)))
                self.end_headers()
                self.wfile.write(file_bytes)
            else:
                error_msg = data.get("message") or data.get("error") or "Nieznany błąd"
                self._json_response(400, {"error": error_msg})

        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
