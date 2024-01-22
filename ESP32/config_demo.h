const char *ssid = "[YOUR_SSID]";
const char *password = "[YPOUR_WIFI_PASSWORD]";
const char *host = "[YOUR_SERVER_IP:PORT]";

#define IMAGE_SIZE 134400 // For 5IN65F
#define TEMP_BUFF_SIZE 2048

#define ButtonPin GPIO_NUM_33
#define LedPin GPIO_NUM_23
#define LedTime 30 * 1000 // 30 seconds