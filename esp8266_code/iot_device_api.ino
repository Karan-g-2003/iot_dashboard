#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// WiFi Configuration
const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";

// API Configuration
const char *serverAddress = "http://your-server-ip:8000"; // Replace with your server IP
const char *deviceId = "001";                             // Unique device ID

// API Endpoints
String telemetryEndpoint = String(serverAddress) + "/api/telemetry/";
String commandEndpoint = String(serverAddress) + "/api/device/" + deviceId + "/command/";

// Pin Configuration
#define DHTPIN 2      // DHT sensor connected to GPIO2 (D4)
#define DHTTYPE DHT22 // DHT22 (AM2302) sensor type
#define RELAY_PIN 5   // Relay connected to GPIO5 (D1)

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// Timing configuration
unsigned long lastSensorRead = 0;
const long sensorInterval = 15000; // 15 seconds between readings

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
    Serial.print("Connecting to WiFi");

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nConnected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

void loop()
{
    unsigned long currentMillis = millis();

    // Read and send sensor data every interval
    if (currentMillis - lastSensorRead >= sensorInterval)
    {
        lastSensorRead = currentMillis;

        // Read sensor data
        float humidity = dht.readHumidity();
        float temperature = dht.readTemperature();

        if (!isnan(humidity) && !isnan(temperature))
        {
            // Send telemetry data
            sendTelemetry(temperature, humidity);

            // Get and apply command
            getCommand();
        }
        else
        {
            Serial.println("Failed to read from DHT sensor!");
        }
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
        doc["device_id"] = deviceId;
        doc["temperature"] = temperature;
        doc["humidity"] = humidity;

        String jsonString;
        serializeJson(doc, jsonString);

        // Send POST request
        http.begin(client, telemetryEndpoint);
        http.addHeader("Content-Type", "application/json");

        int httpCode = http.POST(jsonString);

        if (httpCode > 0)
        {
            Serial.printf("HTTP Response code: %d\n", httpCode);
            String payload = http.getString();
            Serial.println(payload);
        }
        else
        {
            Serial.printf("Error on sending POST: %s\n", http.errorToString(httpCode).c_str());
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

        // Send GET request
        http.begin(client, commandEndpoint);

        int httpCode = http.GET();

        if (httpCode > 0)
        {
            if (httpCode == HTTP_CODE_OK)
            {
                String payload = http.getString();

                // Parse JSON response
                StaticJsonDocument<200> doc;
                DeserializationError error = deserializeJson(doc, payload);

                if (!error)
                {
                    bool relayState = doc["relay"];
                    digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);

                    Serial.print("Relay state set to: ");
                    Serial.println(relayState ? "ON" : "OFF");
                }
            }
        }
        else
        {
            Serial.printf("Error on getting command: %s\n", http.errorToString(httpCode).c_str());
        }

        http.end();
    }
}