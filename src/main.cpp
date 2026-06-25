#include <M5Stack.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// ===== WiFi =====
const char* ssid = "jikei-open-air";
const char* password = "open-wifi";

// ===== MQTT =====
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

const char* topic_sub = "m5stack/device_02/servo";

// ===== MQTT =====
WiFiClient espClient;
PubSubClient client(espClient);

// ===== Servo =====
Servo myServo;
int servoPin = 21;

// ===== MQTT受信 =====
void callback(char* topic, byte* payload, unsigned int length) {

    String json = "";

    for (int i = 0; i < length; i++) {
        json += (char)payload[i];
    }

    Serial.println("受信:");
    Serial.println(json);

    // JSON解析
    DynamicJsonDocument doc(256);

    DeserializationError error = deserializeJson(doc, json);

    if (error) {
        Serial.println("JSON解析失敗");
        return;
    }

    int angle = doc["angle"];
    int duration = doc["duration"];

    Serial.print("angle: ");
    Serial.println(angle);

    Serial.print("duration: ");
    Serial.println(duration);

    // ===== サーボ制御 =====
    myServo.write(angle);

    delay(duration);

    // 停止
    myServo.write(90);

    M5.Lcd.fillScreen(BLACK);

    M5.Lcd.setCursor(20, 20);

    M5.Lcd.printf("Angle: %d\n", angle);
    M5.Lcd.printf("Time: %d ms\n", duration);
}

// ===== MQTT再接続 =====
void reconnect() {

    while (!client.connected()) {

        Serial.println("MQTT connecting...");

        String clientId = "M5Client-";
        clientId += String(random(0xffff), HEX);

        if (client.connect(clientId.c_str())) {

            Serial.println("MQTT connected");

            client.subscribe(topic_sub);

        } else {

            Serial.print("failed: ");
            Serial.println(client.state());

            delay(5000);
        }
    }
}

// ===== setup =====
void setup() {

    M5.begin();

    Serial.begin(115200);

    M5.Lcd.setTextSize(2);

    // Servo
    myServo.attach(servoPin);

    // 停止位置
    myServo.write(90);

    // WiFi
    WiFi.begin(ssid, password);

    M5.Lcd.println("WiFi connecting...");

    while (WiFi.status() != WL_CONNECTED) {

        delay(500);
        Serial.print(".");
    }

    M5.Lcd.println("WiFi connected");

    // MQTT
    client.setServer(mqtt_server, mqtt_port);

    client.setCallback(callback);
}

// ===== loop =====
void loop() {

    if (!client.connected()) {
        reconnect();
    }

    client.loop();
}