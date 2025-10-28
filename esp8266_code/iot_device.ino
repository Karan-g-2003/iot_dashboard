#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// WiFi credentials
const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";

// API endpoints
const char *server = "http://your-server-ip:8000"; // Replace with your server IP
const char *telemetryEndpoint = "/api/telemetry/";
const char *commandEndpoint = "/api/devices/001/command/"; // Device ID: 001

// DHT sensor setup
#define DHTPIN 2      // DHT sensor pin (GPIO2/D4)
#define DHTTYPE DHT22 // DHT22 (AM2302)
DHT dht(DHTPIN, DHTTYPE);

// Relay pin
#define RELAY_PIN 5 // GPIO5/D1

// Timing
unsigned long lastReadingTime = 0;
const long interval = 15000; // 15 seconds

void setup()
{
    Serial.begin(115200);

    // Initialize pins
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);

    // Initialize DHT sensor
    dht.begin();

    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected");
}

void loop()
{
    unsigned long currentTime = millis();

    if (currentTime - lastReadingTime >= interval)
    {
        // Read sensor data
        float humidity = dht.readHumidity();
        float temperature = dht.readTemperature();

        if (!isnan(humidity) && !isnan(temperature))
        {
            // Send telemetry
            sendTelemetry(temperature, humidity);
        }

        // Get command from server
        getCommand();

        lastReadingTime = currentTime;
    }
}

void sendTelemetry(float temperature, float humidity)
{
    if (WiFi.status() == WL_CONNECTED)
    {
        WiFiClient client;
        HTTPClient http;

        // Create JSON payload
        StaticJsonDocument<200> doc;
        doc["device_id"] = "001";
        doc["temperature"] = temperature;
        doc["humidity"] = humidity;

        String jsonString;
        serializeJson(doc, jsonString);

        http.begin(client, String(server) + telemetryEndpoint);
        http.addHeader("Content-Type", "application/json");

        int httpCode = http.POST(jsonString);
        if (httpCode > 0)
        {
            Serial.printf("HTTP Response code: %d\n", httpCode);
        }
        else
        {
            Serial.printf("HTTP Request failed: %s\n", http.errorToString(httpCode).c_str());
        }

        http.end();
    }
}

void getCommand()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        WiFiClient client;
        HTTPClient http;

        http.begin(client, String(server) + commandEndpoint);

        int httpCode = http.GET();
        if (httpCode > 0)
        {
            String payload = http.getString();
            StaticJsonDocument<200> doc;
            deserializeJson(doc, payload);

            bool relayState = doc["relay"];
            digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
            Serial.printf("Relay state updated to: %s\n", relayState ? "ON" : "OFF");
        }

        http.end();
    }
}