#include <M5Stack.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "../include/env.h"
#include <ESP32Servo.h>
#include <ArduinoJson.h>  // ★追加：JSONパース用

Servo myServo;
int servoPin = 21;

// --- MQTT設定 ---
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

const char* topic_publish   = "m5stack/device_02/status";
const char* topic_subscribe = "m5stack/device_02/servo";  // ★変更

WiFiClient espClient;
PubSubClient client(espClient);

int x = 0;  // 角度（0 or 180）
int y = 0;  // 時間（ミリ秒）

void initScreen() {
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(10, 10);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  M5.Lcd.println("MQTT communication");
  M5.Lcd.println("Waiting for connect...");
}

void moveMotor(int angle, int duration_ms) {
  Serial.print("angle: ");
  Serial.print(angle);
  Serial.print(", duration: ");
  Serial.println(duration_ms);

  myServo.write(angle);
  delay(duration_ms);
  myServo.write(90);  // 停止
  Serial.println("停止");
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  // ★JSONをパースしてangleとdurationを取り出す
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("JSONパースエラー: ");
    Serial.println(error.c_str());
    return;
  }

  x = doc["angle"];     // 角度
  y = doc["duration"];  // ミリ秒

  moveMotor(x, y);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "M5StackClient-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      M5.Lcd.fillScreen(BLACK);
      M5.Lcd.setCursor(10, 10);
      M5.Lcd.println("MQTT Connected!");
      client.subscribe(topic_subscribe);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(10000);
    }
  }
}

void setup() {
  M5.begin();
  initScreen();
  myServo.attach(servoPin);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    M5.Lcd.print(".");
  }
  Serial.println("\nWiFi connected");

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  M5.update();

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}