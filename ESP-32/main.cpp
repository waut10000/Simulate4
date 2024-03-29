#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <security.h>

// define ultrasonic pins
#define trigPin D5
#define echoPin D7

//define sound speed in cm/uS
#define SOUND_SPEED 0.034

//variable ultrasonic 
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

void setup_wifi()
{
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void callbackSub(char *topic, byte *payload, unsigned int length)
{
  Serial.println("Received message on topic: " + String(topic));
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
  delay(1000);
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

void sendDeptToNodeRed(float dept)
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

  client.publish(mqttPubTopic, payload);
  Serial.println("Dept and ID sent!");
}


void loop() {
  
  float measured_dept = MeasureDept();
  sendDeptToNodeRed(measured_dept);

  delay(20000);
}
