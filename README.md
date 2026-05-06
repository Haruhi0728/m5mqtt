# m5mqtt

M5Stack Coreを使用した、MQTT通信の学習・デモ用プロジェクトです。  
Wi-Fi経由でMQTTブローカーに接続し、M5StackデバイスとWebブラウザ間での相互通信を行います。

## 機能

- M5Stack デバイス機能:
    - MQTTメッセージ受信 (Subscribe): 
        - 受信したメッセージ（`red`, `green`, `blue`）に応じて画面色を変更します。その他の文字列はテキストとして画面に表示されます。
    - MQTTメッセージ送信 (Publish): 
        - 3つの物理ボタン（A, B, C）を押すと、それぞれのボタンに応じたメッセージを送信します。
- Webコントローラー (`web/index.html`):
    - 動的なトピック設定: ブラウザ上で送信先・受信先のトピック名を自由に変更できます。
    - 双方向通信: 画面上のボタン（赤/緑/青）やテキスト入力（Enterキー送信対応）でM5Stackを操作できます。
    - リアルタイムログ: M5Stackからのメッセージ受信やシステムの状態をログとして表示します。

## ハードウェア要件

- M5Stack Core (Basic / Gray / Fire 等)
- USB Type-C ケーブル

## ソフトウェア要件

- [PlatformIO](https://platformio.org/)
- [Visual Studio Code](https://code.visualstudio.com/) + [PlatformIO IDE](https://platformio.org/platformio-ide) 拡張機能でも利用可能ですが、CLIでの利用を推奨します。

## セットアップ手順

1.  Wi-Fi設定ファイルの作成
    - `lib/env.h.example` をコピーして `lib/env.h` を作成します。
    - `lib/env.h` に自身のWi-Fi情報（SSID/パスワード）を入力します。
2.  M5Stackへの書き込み
    - PlatformIOを使用して `src/main.cpp` をビルド・書き込みします。
    - シリアルモニターの通信速度は 115200bps に設定されています（`platformio.ini` 内の `monitor_speed` で設定済み）。
3.  Webコントローラーの起動
    - `web/index.html` をブラウザで開きます（ファイルをブラウザにドラッグ＆ドロップするだけで動作します）。
    - もし Node.js がインストールされていれば、`npx serve web` などでローカルサーバーを立てて実行することも可能です。

## 使い方

### M5Stack からの操作
- ボタンA / B / C: 押すとMQTTトピック（デフォルト：`m5stack/device_01/status`）へメッセージを送信します。Webコントローラーのログエリアに「Button A Pressed!」などのメッセージが表示されます。

### Webブラウザ からの操作
- トピック設定: 画面上部の「設定」エリアでトピック名を変更し「設定を更新」を押すと、動的に通信先を切り替えられます。
- 色ボタン (赤/緑/青): クリックするとM5Stackの画面色が即座に変わります。
- テキスト送信: 入力フォームに文字を入れて「テキスト送信」ボタンを押すか、Enterキー を押すと、M5Stackの画面にその文字が表示されます。

## 技術仕様

- MQTTブローカー: [HiveMQ](https://www.hivemq.com/public-mqtt-broker/) (public broker)
- プロトコル: 
    - M5Stack: MQTT over TCP (Port 1883)
    - Web: MQTT over WebSockets (Port 8884)
- デフォルトトピック:
    - `m5stack/device_01/status` (M5Stack -> Web)
    - `m5stack/device_01/command` (Web -> M5Stack)

## 使用ライブラリ

- [M5Stack](https://github.com/m5stack/M5Stack)
- [PubSubClient](https://github.com/knolleary/pubsubclient)
- [MQTT.js](https://github.com/mqttjs/MQTT.js) (Web側)
- [Tailwind CSS](https://tailwindcss.com/) (Web側)
