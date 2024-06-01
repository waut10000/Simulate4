#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <security.h>

// define ultrasonic pins
#define trigPin D5
#define echoPin D7

// define sound speed in cm/uS
#define SOUND_SPEED 0.034

// variable ultrasonic 
long duration;
float distanceCm;
long procent;

// time for deepsleep
#define timeToSleep 60 // 15min - 900 sec
#define timeToSecond 1000000

// MQTT topic
const char *mqttPubTopic = "esp32/dept";

//
WiFiClient espClient;
PubSubClient client(espClient);
bool messageReceived = false;

const int networkCount = sizeof(networks) / sizeof(networks[0]);


int waitForConnectResult() {
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (millis() - start > 10000) { // 10-second timeout
            return WL_DISCONNECTED;
        }
    }
    return WL_CONNECTED;
}

void setup_wifi() {
    WiFi.mode(WIFI_STA); // Set WiFi to station mode
    WiFi.disconnect();   // Disconnect any previous connections
    delay(100);

    Serial.println("Scanning for networks...");
    int n = WiFi.scanNetworks(); // Scan for available networks
    if (n == 0) {
        Serial.println("No networks found.");
    } else {
        Serial.print(n);
        Serial.println(" networks found");
        for (int i = 0; i < n; ++i) {
            Serial.printf("%d: %s (%d)\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));
        }

        // Try to connect to each known network
        for (int i = 0; i < networkCount; i++) {
            for (int j = 0; j < n; j++) {
                if (WiFi.SSID(j) == networks[i][0]) {
                    Serial.printf("Trying to connect to SSID: %s\n", networks[i][0]);
                    WiFi.begin(networks[i][0], networks[i][1]);
                    if (waitForConnectResult() == WL_CONNECTED) {
                        Serial.printf("Successfully connected to %s\n", networks[i][0]);
                        return;
                    } else {
                        Serial.printf("Failed to connect to %s\n", networks[i][0]);
                    }
                }
            }
        }
        Serial.println("Failed to connect to any network.");
    }
}


void callbackSub(char *topic, byte *payload, unsigned int length)
{
  Serial.println("Received message on topic: " + String(topic));
  if (String(topic) == mqttPubTopic)
  {
    messageReceived = true;
  }
  // Handle incoming MQTT messages if needed
}

void reconnect()
{
  while (!client.connected())
  {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("ESP32EClient", mqttUser, mqttPassword))
    {
      Serial.println("Connected to MQTT broker");
      client.subscribe(mqttPubTopic);
    }
    else
    {
      Serial.println("Failed to connect to MQTT broker. Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200); // Starts the serial communication
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callbackSub);
  esp_sleep_enable_timer_wakeup(timeToSleep * timeToSecond); // wake up trigger by timer
  delay(1000);
}

void deepsleep() // start deepsleep
{
  Serial.println("Going to sleep now  Zzz..");
  delay(500);
  Serial.flush();
  esp_deep_sleep_start();
}

float MeasureDept(){
  //bron https://randomnerdtutorials.com/esp32-hc-sr04-ultrasonic-arduino/
  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  
  // Calculate the distance
  distanceCm = duration * SOUND_SPEED/2;
  
  // Prints the distance in the Serial Monitor
  Serial.print("Distance (cm): ");
  Serial.println(distanceCm);

  return distanceCm;
}

bool sendDeptToNodeRed(float dept)
{
  if (!client.connected())
  {
    reconnect();
  }
  client.loop();

  // Prepare the payload as a combination of the dept value, a delimiter, and the UUID
  char floatStr[10]; // Buffer for the float conversion
  dtostrf(dept, 4, 2, floatStr); // Convert float to string

  // Prepare the JSON payload. Make sure it's large enough to hold the complete JSON string.
  char payload[256]; // Increased size to accommodate JSON structure

  // Format the float and ID into a JSON string
  snprintf(payload, sizeof(payload), "{\"dept\":%.2f,\"uuid\":\"%s\"}", dept, ID);
  Serial.println(payload);

  messageReceived = false; // Reset messageReceived flag
  client.publish(mqttPubTopic, payload);
  Serial.println("Dept and ID sent!");

  unsigned long startAttemptTime = millis();

  // Wait for acknowledgment with a timeout
  while (!messageReceived && millis() - startAttemptTime < 5000)
  {
    client.loop();
    delay(100);
  }

  return messageReceived;
}

void loop() {
  float measured_dept = MeasureDept();
  bool success = false;
  int attempts = 0;
  while (!success && attempts < 3)
  {
    success = sendDeptToNodeRed(measured_dept);
    if (!success)
    {
      attempts++;
      Serial.println("Failed to send message, retrying...");
      delay(5000); // Wait before retrying
    }
  }

  if (!success)
  {
    Serial.println("Failed to send message after 3 attempts, going to deep sleep.");
    deepsleep();
  }
  deepsleep();
}
