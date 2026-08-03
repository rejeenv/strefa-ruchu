from http.server import BaseHTTPRequestHandler
import json
import requests

API_KEY = "TWÓJ_API_KEY"  # ten sam co w activate.py
BASE_URL = "https://nfa-api.acode.ing/api/v1"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body)
            key = data.get("key", "").strip()
        except:
            self._json(400, {"error": "Invalid JSON"})
            return

        if not key:
            self._json(400, {"error": "Podaj klucz"})
            return

        try:
            res = requests.post(
                f"{BASE_URL}/check_account",
                headers=HEADERS,
                json={"activation_key": key},
                timeout=20
            )
            data = res.json()

            if res.status_code == 200:
                status = data.get("result") or data.get("status")
                msg = data.get("message", "")

                if status == "valid":
                    self._json(200, {
                        "status": "valid",
                        "message": msg or "Konto działa poprawnie"
                    })
                elif status == "replaced":
                    self._json(200, {
                        "status": "replaced",
                        "replacement_key": data.get("replacement_key", "N/A"),
                        "message": msg
                    })
                else:
                    self._json(200, {
                        "status": status or "unknown",
                        "message": msg or "Nieznany status"
                    })
            else:
                error_msg = data.get("message") or data.get("error") or "Błąd API"
                self._json(400, {"error": error_msg})

        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
