from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import json
import threading
import atexit
import paho.mqtt.client as mqtt

app = Flask(__name__)

# ===== MQTT設定 =====
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 8884
MQTT_TOPIC = "m5stack/device_02/servo"

# MQTTクライアントを常時接続で使う
MQTT_CLIENT = None
MQTT_LOCK = threading.Lock()

# ===== DB設定 =====
DB_NAME = "logs.db"


# ===== DB初期化 =====
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_email TEXT,
            user_name TEXT,
            action TEXT NOT NULL,
            angle INTEGER,
            duration INTEGER,
            mqtt_topic TEXT,
            result TEXT,
            ip_address TEXT
        )
    """)

    # 既存DBに user_name カラムがない場合の自動追加
    cur.execute("PRAGMA table_info(access_logs)")
    columns = [row[1] for row in cur.fetchall()]

    if "user_name" not in columns:
        cur.execute("""
            ALTER TABLE access_logs
            ADD COLUMN user_name TEXT
        """)

    conn.commit()
    conn.close()


# ===== ログ保存 =====
def save_log(
    user_email,
    user_name,
    action,
    angle,
    duration,
    result,
    ip_address
):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # 日本時間で保存
    jst = datetime.timezone(datetime.timedelta(hours=9))
    timestamp = datetime.datetime.now(jst).isoformat(timespec="seconds")

    cur.execute("""
        INSERT INTO access_logs (
            timestamp,
            user_email,
            user_name,
            action,
            angle,
            duration,
            mqtt_topic,
            result,
            ip_address
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        user_email,
        user_name,
        action,
        angle,
        duration,
        MQTT_TOPIC,
        result,
        ip_address
    ))

    conn.commit()
    conn.close()


# ===== MQTT接続成功時 =====
def on_connect(client, userdata, flags, reason_code, properties):
    print("MQTT接続結果:", reason_code)


# ===== MQTT送信完了時 =====
def on_publish(client, userdata, mid, reason_code, properties):
    print("MQTT送信完了 mid:", mid, "reason_code:", reason_code)


# ===== MQTT初期化 =====
def init_mqtt():
    global MQTT_CLIENT

    MQTT_CLIENT = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        transport="websockets"
    )

    MQTT_CLIENT.on_connect = on_connect
    MQTT_CLIENT.on_publish = on_publish

    # wss://broker.hivemq.com:8884/mqtt 相当
    MQTT_CLIENT.tls_set()
    MQTT_CLIENT.ws_set_options(path="/mqtt")

    print("MQTT接続中...")
    MQTT_CLIENT.connect(MQTT_BROKER, MQTT_PORT, 60)

    # バックグラウンドでMQTT通信維持
    MQTT_CLIENT.loop_start()

    print("MQTT client started")


# ===== MQTT終了処理 =====
def close_mqtt():
    global MQTT_CLIENT

    if MQTT_CLIENT is not None:
        try:
            MQTT_CLIENT.loop_stop()
            MQTT_CLIENT.disconnect()
            print("MQTT client stopped")
        except Exception as e:
            print("MQTT終了時エラー:", e)


atexit.register(close_mqtt)


# ===== MQTT送信 =====
def publish_mqtt(angle, duration):
    global MQTT_CLIENT

    msg = {
        "angle": angle,
        "duration": duration
    }

    payload = json.dumps(msg, separators=(",", ":"))

    print("===== MQTT送信 =====")
    print("TOPIC:", MQTT_TOPIC)
    print("PAYLOAD:", payload)

    if MQTT_CLIENT is None:
        raise RuntimeError("MQTTクライアントが初期化されていません")

    # 複数リクエストが同時に来たときの競合防止
    with MQTT_LOCK:
        if not MQTT_CLIENT.is_connected():
            print("MQTTが切断されています。再接続します。")
            MQTT_CLIENT.reconnect()

        result = MQTT_CLIENT.publish(MQTT_TOPIC, payload, qos=0)
        result.wait_for_publish()

        print("publish rc:", result.rc)
        print("is_published:", result.is_published())

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed rc={result.rc}")

    return msg


# ===== トップページ =====
@app.route("/")
def index():
    return render_template("index.html")


# ===== サーボ操作API =====
@app.route("/api/servo", methods=["POST"])
def servo():
    data = request.get_json(silent=True) or {}

    # HTML側から送られてくるGoogleログイン情報
    user_email = data.get("email", "unknown-user")
    user_name = data.get("name", "unknown-name")

    action = str(data.get("action", "CUSTOM")).upper()

    try:
        angle = int(data.get("angle", 90))
        duration = int(data.get("duration", 500))
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "angle または duration が数値ではありません"
        }), 400

    # 安全制限
    angle = max(0, min(angle, 180))
    duration = max(0, min(duration, 5000))

    ip_address = request.remote_addr

    try:
        mqtt_message = publish_mqtt(angle, duration)

        save_log(
            user_email=user_email,
            user_name=user_name,
            action=action,
            angle=angle,
            duration=duration,
            result="sent",
            ip_address=ip_address
        )

        return jsonify({
            "status": "ok",
            "user_email": user_email,
            "user_name": user_name,
            "action": action,
            "mqtt_topic": MQTT_TOPIC,
            "mqtt_message": mqtt_message
        })

    except Exception as e:
        save_log(
            user_email=user_email,
            user_name=user_name,
            action=action,
            angle=angle,
            duration=duration,
            result=f"error: {str(e)}",
            ip_address=ip_address
        )

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ===== ログ取得 =====
@app.route("/logs")
def logs():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            timestamp,
            user_email,
            user_name,
            action,
            angle,
            duration,
            mqtt_topic,
            result,
            ip_address
        FROM access_logs
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


# ===== 動作確認用 =====
@app.route("/health")
def health():
    mqtt_status = False

    if MQTT_CLIENT is not None:
        mqtt_status = MQTT_CLIENT.is_connected()

    return jsonify({
        "status": "ok",
        "mqtt_connected": mqtt_status,
        "mqtt_broker": MQTT_BROKER,
        "mqtt_port": MQTT_PORT,
        "mqtt_topic": MQTT_TOPIC
    })


if __name__ == "__main__":
    init_db()
    init_mqtt()

    # debug=True だと自動リロードでMQTTクライアントが二重起動することがあるため、
    # 今回は debug=False 推奨
    app.run(host="0.0.0.0", port=5000, debug=False)