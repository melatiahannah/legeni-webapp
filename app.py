"""Application fil rouge du cours DevOps B3."""
import os
import socket

from flask import Flask, jsonify, render_template_string

PAGE = """<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Legeni WebApp</title>
<style>
  body { font-family: sans-serif; margin: 0; background: #f4f6f8; }
  header { background: {{ color }}; color: #fff; padding: 2rem; }
  main { padding: 2rem; }
  td { padding: .3rem 1rem .3rem 0; }
</style></head>
<body>
  <header><h1>Legeni WebApp – B3</h1><p>Version {{ version }}</p></header>
  <main><table>
    <tr><td>Environnement</td><td><b>{{ env }}</b></td></tr>
    <tr><td>Servi par (hostname)</td><td><b>{{ hostname }}</b></td></tr>
    <tr><td>Nombre de visites</td><td><b>{{ visits }}</b></td></tr>
    <tr><td>Stockage du compteur</td><td><b>{{ backend }}</b></td></tr>
  </table></main>
</body></html>
"""


class MemoryCounter:
    name = "memoire"

    def __init__(self):
        self.value = 0

    def incr(self):
        self.value += 1
        return self.value

    def ping(self):
        return True


class RedisCounter:
    name = "redis"

    def __init__(self, host, port, password=None):
        import redis
        self.client = redis.Redis(host=host, port=port, password=password, socket_timeout=2)

    def incr(self):
        return int(self.client.incr("visits"))

    def ping(self):
        try:
            return bool(self.client.ping())
        except Exception:
            return False


def build_counter():
    host = os.getenv("REDIS_HOST")
    if host:
        return RedisCounter(
            host, int(os.getenv("REDIS_PORT", "6379")), os.getenv("REDIS_PASSWORD") or None
        )
    return MemoryCounter()


def create_app(counter=None):
    app = Flask(__name__)
    app.config["COUNTER"] = counter or build_counter()

    def info():
        return {
            "app": "legeni-webapp",
            "version": os.getenv("APP_VERSION", "dev"),
            "env": os.getenv("APP_ENV", "dev"),
            "hostname": socket.gethostname(),
        }

    @app.route("/")
    def index():
        counter = app.config["COUNTER"]
        data = info()
        return render_template_string(
            PAGE,
            color=os.getenv("APP_COLOR", "#8250df"),
            version=data["version"],
            env=data["env"],
            hostname=data["hostname"],
            visits=counter.incr(),
            backend=counter.name,
        )

    @app.route("/api/info")
    def api_info():
        return jsonify(info())

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.route("/ready")
    def ready():
        if app.config["COUNTER"].ping():
            return jsonify(status="ready")
        return jsonify(status="redis indisponible"), 503

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
