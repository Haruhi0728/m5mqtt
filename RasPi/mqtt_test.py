import time
import paho.mqtt.client as mqtt

# 1. 接続成功時のコールバック
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("【成功】パブリックブローカーに接続しました！")
        # M5からの状態報告を受信待機
        client.subscribe("m5stack/device_02/status")
        print("M5Stackからの入力を待っています...\n")
    else:
        print(f"接続失敗: {rc}")

# 2. メッセージ受信時のコールバック
def on_message(client, userdata, msg):
    print(f"\n【M5から受信】 {msg.payload.decode()}")
    print("送信するコマンドを入力してください (LOCK / OPEN / exit): ", end="", flush=True)

# 3. クライアントの初期化
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

# 4. ブローカーに接続
client.connect("broker.hivemq.com", 1883, 60)

# 通信ループをバックグラウンドで開始
client.loop_start()

# 5. メインループ（キーボード入力を監視して送信）
try:
    # 接続が完了するまで少し待つ
    time.sleep(1)

    while True:
        # 画面から文字の入力を受け付ける
        cmd = input("送信するコマンドを入力してください (LOCK / OPEN / exit): ")

        # exit と打ったらプログラムを終了