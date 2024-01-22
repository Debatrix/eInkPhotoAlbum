#include <WiFi.h>
#include <Arduino.h>
#include <esp_sleep.h>
#include <HTTPClient.h>
#include <stdlib.h>
#include <string.h>

#include "config.h"
#include "EInk.h"

#define HASH_SIZE 33
#define MAX_WIFI_CONNECT_RETRY 10
#define DEFAULT_TIME_TO_SLEEP 60 * 60 * 1

RTC_DATA_ATTR char lastHash[HASH_SIZE] = {0};
#define uS_TO_S_FACTOR 1000000 /* Conversion factor for micro seconds to seconds */

int hashCheck(char *hash)
{
    int flag = 0;
    String req = (String)host + "/hash";
    HTTPClient http;
    http.begin(req);
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK)
    {
        String payload = http.getString();
        payload.toCharArray(hash, HASH_SIZE);
    }
    else
    {
        flag = -1;
    }
    http.end();
    return flag;
}

void sendInfo(String infoType, String message)
{
    String req = (String)host + "/info?" + infoType + "=" + message;
    HTTPClient http;
    http.begin(req);
    int httpCode = http.GET();
    http.end();
}

int getWakeupTime()
{
    int time = DEFAULT_TIME_TO_SLEEP;
    String req = (String)host + "/wakeup";
    HTTPClient http;
    http.begin(req);
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK)
    {
        String payload = http.getString();
        time = payload.toInt();
    }
    http.end();
    return time;
}

int getNextImage()
{
    String req = (String)host + "/next";
    HTTPClient http;
    http.begin(req);
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK)
    {
        Serial.println("OK");
    }
    http.end();
    return httpCode;
}

int updateEInk()
{
    int flag = 0;
    String req = (String)host + "/bytes";
    HTTPClient http;
    http.begin(req);
    int httpCode = http.GET();
    int len = http.getSize();
    if (httpCode == HTTP_CODE_OK && len == IMAGE_SIZE)
    {
        DEV_Module_Init();
        EPD_5IN65F_Init();
        delay(10);
        EPD_5IN65F_Display_begin();
        uint8_t temp_buff[TEMP_BUFF_SIZE] = {0};
        int offset = 0;
        WiFiClient *stream = http.getStreamPtr();
        while (http.connected() && (offset < IMAGE_SIZE))
        {
            size_t size = stream->available();
            if (size)
            {
                int c = stream->readBytes(temp_buff, ((size > sizeof(temp_buff)) ? sizeof(temp_buff) : size));
                for (int i = 0; i < c; i++)
                {
                    EPD_5IN65F_SendData(temp_buff[i]); // Send received data
                }
                offset += c;
                Serial.println("received: " + (String)offset + "/" + (String)IMAGE_SIZE);
                delay(10);
            }
        }
        delay(100);
        EPD_5IN65F_Display_end();
        EPD_5IN65F_Sleep();
        Serial.println("update E-Ink done");
    }
    else
    {
        flag = -1;
        Serial.println("update E-Ink failed");
    }
    http.end();
    return flag;
}

void setup()
{
    Serial.begin(115200);
    delay(10);
    pinMode(ButtonPin, INPUT);
    pinMode(LedPin, OUTPUT);

    int time_to_sleep = DEFAULT_TIME_TO_SLEEP;
    int nextImageFlag = 0;
    int ledFlag = 0;
    int buttonState;

    // get wakeup reason
    esp_sleep_wakeup_cause_t wakeup_reason;
    wakeup_reason = esp_sleep_get_wakeup_cause();

    if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0)
    {
        Serial.println("Wakeup caused by external signal using RTC_IO");
        ledFlag = 1;
        digitalWrite(LedPin, HIGH);
        delay(500);
        // check if button is pressed
        buttonState = digitalRead(ButtonPin);
        if (buttonState == HIGH)
        {
            digitalWrite(LedPin, LOW);
            delay(200);
            digitalWrite(LedPin, HIGH);
        }
        buttonState = digitalRead(ButtonPin);
        if (buttonState == HIGH)
        {
            nextImageFlag = 1;
        }
    }

    // connect to wifi
    int wifi_connect_try = 0;
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED && wifi_connect_try < MAX_WIFI_CONNECT_RETRY)
    {
        delay(500);
        Serial.println("Connecting to WiFi...");
        wifi_connect_try++;
    }

    // update
    if ((WiFi.status() == WL_CONNECTED))
    {
        Serial.print("Connected, IP address: ");
        Serial.println(WiFi.localIP());
        delay(200);

        // get next image
        if (nextImageFlag == 1)
        {
            getNextImage();
            delay(200);
        }

        // check new image
        int newImageFlag = 0;
        char newHash[HASH_SIZE] = {0};
        newImageFlag = hashCheck(newHash);

        if (strcmp(lastHash, newHash) && (newImageFlag == 0))
        {
            // update E-Ink
            Serial.println("updating...");
            newImageFlag = updateEInk();

            // update hash
            if (newImageFlag == 0)
            {
                strncpy(lastHash, newHash, HASH_SIZE);
                sendInfo("info", "EinkUpdated");
                Serial.println("EinkUpdated");
            }
        }
        else
        {
            Serial.println("no needed");
        }
    }

    // close led
    if (ledFlag == 1)
    {
        delay(LedTime);
        digitalWrite(LedPin, LOW);
    }

    // get wakeup time
    if ((WiFi.status() == WL_CONNECTED))
    {
        time_to_sleep = getWakeupTime();
    }

    // go to sleep
    WiFi.disconnect();
    esp_sleep_enable_ext0_wakeup(ButtonPin, 1);
    esp_sleep_enable_timer_wakeup((uint64_t)time_to_sleep * uS_TO_S_FACTOR);
    Serial.println("ESP32 will wake up in " + String(time_to_sleep) + " seconds");
    esp_deep_sleep_start();
}

void loop()
{
}
