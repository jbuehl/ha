//////////////////////
// JSON Definitions //
//////////////////////
const char beaconJson[] = "[\"%s\", %d, %s, %d, \"%s\"]";
const char resourcesJson[] = "{\"name\": \"resources\", \"type\": \"collection\", \"class\": \"HACollection\", \"resources\": [ \"%s\", \"states\" ]}";
const char statesJson[] = "{\"name\": \"states\", \"interface\": \"None\", \"addr\": \"\", \"type\": \"sensor\", \"class\": \"ResourceStateSensor\", \"location\": null, \"group\": \"\"}";
const char statesStateJson[] = "{\"%s\": {\"%s\": %d}}";
const char stateNotifyJson[] = "{\"%s\": {\"%s\": %d}, \"hostname\": \"%s\", \"port\": %d}";
const char sensorJson[] = "{\"name\": \"%s\", \"interface\": \"None\", \"addr\": \"0\", \"type\": \"%s\", \"class\": \"HAControl\"}";
const char sensorStateJson[] = "{\"%s\": %d}";
const char wifiJson[] = "{\"ipaddr\": \"%s\", \"bssid\": \"%s\", \"channel\": %d, \"rssi\": %d}";

//////////////////////
// HTTP Definitions //
//////////////////////
String method;
String url;
String path;
String searchStr;
String keyword;
String value;
String statusCode = "200";

//////////////////////
// Global variables //
//////////////////////
MDNSResponder mdnsResponder;
WiFiServer server(restPort);
WiFiClient client;
WiFiUDP broadcast;
int beaconIntervalCount = 0;
int stateIntervalCount = 0;
int sensorIntervalCount = 0;
int fadeIntervalCount = 0;
int onIntervalCount = 0;
int inputHoldCount = 0;
int onState = 0;
int currentState = 0;
int lastInput = 1;
const int msgSize = 512;
char msg[msgSize];
IPAddress ipAddr;
unsigned char macAddr[6];
unsigned char bssid[6];
int channel;
int rssi = -999;
char serviceName[11];
char sensorName[14];
String sensorPath;
String sensorStatePath;
String sensorStateChangePath;

//////////////////////
// Utility routines //
//////////////////////
void blinkLed(int onTime, int offTime, int nTimes, int delayAfter) {
  if (blinkStatus) {
    for (int n=0; n<nTimes; n++) {
      digitalWrite(LED_PIN, HIGH);
      delay(onTime);
      digitalWrite(LED_PIN, LOW);
      delay(offTime);
    }
  }
  delay(delayAfter);
}

String ipAddrToChar(IPAddress ip) {
  char ipString[16];
  sprintf(ipString, "%d.%d.%d.%d\0", ip[0], ip[1], ip[2], ip[3]);
  return ipString;
}

String macAddrToChar(unsigned char* mac) {
  char macString[18];
  sprintf(macString, "%02x:%02x:%02x:%02x:%02x:%02x\0", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return macString;
}

////////////////////
// Setup routines //
////////////////////
void setupSerial() {
#ifdef DEBUG
  Serial.begin(115200);
  Serial.println();
  Serial.print("Starting...");
  Serial.println();
#endif
}

void setupHardware() {
  pinMode(LOAD_PIN, OUTPUT);
  pinMode(INPUT_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LOAD_PIN, LOW);
  if (dimmer) {
    onState = 100;
  }
  else {
    onState = 1;
  }
//  digitalWrite(LED_PIN, LOW);
}

void scanWifi() {
#ifdef DEBUG
  // scan for nearby networks:
  Serial.println("Scan Networks");
#endif
  byte numSsid = WiFi.scanNetworks();
  rssi = -999;
#ifdef DEBUG
  Serial.print("SSID List:");
  Serial.println(numSsid);
#endif
  for (int thisNet = 0; thisNet<numSsid; thisNet++) {
#ifdef DEBUG
    Serial.print(thisNet);
    Serial.print(") Network: ");
    Serial.println(WiFi.SSID(thisNet));
    Serial.print("   BSSID: ");
    Serial.print(macAddrToChar(WiFi.BSSID(thisNet)));
    Serial.print("   channel: ");
    Serial.print(WiFi.channel(thisNet));
    Serial.print("   strength: ");
    Serial.print(WiFi.RSSI(thisNet));
    Serial.print("   encryption type: ");
    Serial.println(WiFi.encryptionType(thisNet));
#endif
    if (!strcmp(WiFi.SSID(thisNet), ssid)) {
      if (WiFi.RSSI(thisNet) > rssi) {
        memcpy(bssid, WiFi.BSSID(thisNet), 6);
        channel = WiFi.channel(thisNet);
        rssi = WiFi.RSSI(thisNet);
      }
    }
  }
}

void setupWifi() {
  WiFi.mode(WIFI_STA);
#ifdef DEBUG
  Serial.print( "Connecting to ");
  Serial.print(ssid);
#endif
  if (rssi != -999) {
#ifdef DEBUG
    Serial.print(" channel ");
    Serial.print(channel);
    Serial.print(" BSSID ");
    Serial.println(macAddrToChar(bssid));
#endif
    WiFi.begin(ssid, psk, channel);
  }
  else {
#ifdef DEBUG
    Serial.println();
#endif
    WiFi.begin(ssid, psk);
  }
  while (WiFi.status() != WL_CONNECTED) {
    blinkLed(100, 100, 1, 0);
  }
  blinkLed(2000, 1000, 1, 0);
  ipAddr = WiFi.localIP();
  WiFi.macAddress(macAddr);
#ifdef DEBUG
  Serial.print( "Connected to ");
  Serial.print(ssid);
  Serial.print(" IP address ");
  Serial.print(ipAddr);
  Serial.println();
#endif
}

void setupNames() {
  sprintf(serviceName, "ESP-%02x%02x%02x\0", macAddr[3], macAddr[4], macAddr[5]);
  sprintf(sensorName, "ESP-%02x%02x%02x-00\0", macAddr[3], macAddr[4], macAddr[5]);
  sensorPath = "/resources/"+String(sensorName);
  sensorStatePath = "/resources/"+String(sensorName)+"/state";
  sensorStateChangePath = "/resources/"+String(sensorName)+"/stateChange";
}

void setupMdns() {
  if (mdns) {
    if (mdnsResponder.begin(serviceName, ipAddr)) {
      blinkLed(1000, 1000, 1, 0);
#ifdef DEBUG
      Serial.println("mDNS responder started");
#endif
    }
  }
}

void setupServer() {
  server.begin();
#ifdef DEBUG
  Serial.println("HTTP server started");
#endif
}

/////////////////////////
// Processing routines //
/////////////////////////
void setState(int state) {
#ifdef DEBUG
  Serial.print("setState:");
  Serial.println(state);
#endif
  currentState = state;
  if (dimmer) {
    analogWrite(LOAD_PIN, state*PWMRANGE/100);
  }
  else {
    digitalWrite(LOAD_PIN, state);
  }
}

void sendBeacon() {
  // send the beacon every beaconInterval secs
  if (beaconIntervalCount == 0) {
    if (beacon) {
      snprintf(msg, msgSize, beaconJson, serviceName, restPort, resourcesJson, 0, serviceName);
      broadcast.beginPacket(IPAddress(192,168,1,255), beaconPort);
      broadcast.write(msg, strlen(msg));
      broadcast.endPacket();
#ifdef DEBUG
      Serial.print("sendBeacon: ");
      Serial.println(msg);
#endif
    }
  }
  beaconIntervalCount++;
  if (beaconIntervalCount == beaconInterval*sampleRate) {
    beaconIntervalCount = 0;
  }
}

void sendState(bool force) {
  if (!state) {
    return;
  }
  if (force) {
      stateIntervalCount = 0;
  }
  // send the state every stateInterval secs
  if (stateIntervalCount == 0) {
    snprintf(msg, msgSize, stateNotifyJson, "state", sensorName, currentState, serviceName, restPort);
    broadcast.beginPacket(IPAddress(192,168,1,255), statePort);
    broadcast.write(msg, strlen(msg));
    broadcast.endPacket();
#ifdef DEBUG
    Serial.print("sendState: ");
    Serial.println(msg);
#endif
  }
  stateIntervalCount++;
  if (stateIntervalCount == stateInterval*sampleRate) {
    stateIntervalCount = 0;
  }
}

void checkInput() {
  if (irSensor) {    // process IR sensor timers
    if (sensorIntervalCount == sensorInterval*sampleRate) {    // done counting
      sensorIntervalCount = 0;
    }
    else if (sensorIntervalCount != 0) {    // still counting
      sensorIntervalCount++;
    }
    if (onIntervalCount == onInterval*sampleRate) {    // done counting
      onIntervalCount = 0;
      setState(0);
      sendState(true);
    }
    else if (onIntervalCount != 0) {    // still counting
      onIntervalCount++;
    }
  }
  int input = digitalRead(INPUT_PIN);
  if (irSensor) {
    if (input == 0) {
      if (sensorIntervalCount == 0) { // sensor timer is not counting
        if (currentState == 0) {      // turn on the light if it is off
          setState(onState);
          sendState(true);
        }
        sensorIntervalCount = 1;      // start the sensor timer
        onIntervalCount = 1;          // (re)start the timer to keep the light on
      }
    }
  }
  else {    // button input - toggle the state
    if (input != lastInput) {
#ifdef DEBUG
      Serial.print("input: ");
      Serial.print(input);
      Serial.print(" lastInput: ");
      Serial.println(lastInput);
#endif
      if (lastInput == 1) {    // change on the button being pressed (1->0)
        if (currentState == 0) {
          setState(onState);
        }
        else {
          setState(0);
        }
        sendState(true);
      }
      lastInput = input;
      inputHoldCount = 0;
    }
    else {  // button maybe is being held down
      if (input == 0) {
        inputHoldCount++;
        if (inputHoldCount > inputHoldConfig*sampleRate) {
#ifdef DEBUG
          Serial.print("inputHoldCount: ");
          Serial.println(inputHoldCount);
#endif
          blinkLed(100, 100, 5, 0);
        }
      }
    }
  }
}

void parseRequest() {
#ifdef DEBUG
  Serial.print("request from: ");
  Serial.print(ipAddrToChar(client.remoteIP()));
  Serial.print(" port: ");
  Serial.println(client.remotePort());
#endif
  // Read the first line of the request
  String req = client.readStringUntil('\r');
  client.readStringUntil('\n');

  // Retrieve the path by finding the spaces
  int pathStart = req.indexOf(' ');
  int pathEnd = req.indexOf(' ', pathStart + 1);
  if (pathStart == -1 || pathEnd == -1) {
    statusCode = "400";
  }

  method = req.substring(0, pathStart);
  path = req.substring(pathStart + 1, pathEnd);
  keyword = "";
  value = "";
  if (method == "POST" || method == "PUT") {
    // skip the headers
    while (1) {
      req = client.readStringUntil('\r');
      client.readStringUntil('\n');
      if (req == "") break; //no more headers
    }
    // parse the json
    // assume the exact form '{"keyword": value}'
    req = client.readStringUntil('\r');
    int colon = req.indexOf(':');
    int endBracket = req.indexOf('}');
    keyword = req.substring(2, colon-1);
    value = req.substring(colon+2, endBracket);
  }
  client.flush();
#ifdef DEBUG  
  Serial.print("method: ");
  Serial.println(method);
  Serial.print("path: ");
  Serial.println(path);
  Serial.print("keyword: ");
  Serial.println(keyword);
  Serial.print("value: ");
  Serial.println(value);
  Serial.println();
#endif
}

void handleStates() {
  snprintf(msg, msgSize, statesJson);
  statusCode = "200";
}

void handleResources() {
  snprintf(msg, msgSize, resourcesJson, sensorName);
  statusCode = "200";
}

void handleSensor() {
  String sensorType;
  if (dimmer) {
    sensorType = "dimmer";
  }
  else {
    sensorType = "light";
  }
  snprintf(msg, msgSize, sensorJson, sensorName, sensorType.c_str());
  statusCode = "200";
}

void handleStatesState() {
  snprintf(msg, msgSize, statesStateJson, "state", sensorName, currentState);
  statusCode = "200";
}

void handleSensorState() {
  if (keyword == "state") {
    int state = value.toInt();
    if (dimmer) {
      if ((state == 1) || (state > 100)) { // compatibility with 1 == On
        state = 100;
      }
    }
    if (state != 0) {
      onState = state;
    }
    setState(state);
    sendState(true);  // send the state notification immediately
  }
  snprintf(msg, msgSize, sensorStateJson, "state", currentState);
  statusCode = "200";
}

void handleStatesStateChange() {
  snprintf(msg, msgSize, statesStateJson, "stateChange", sensorName, currentState);
  statusCode = "501"; // not implemented
}

void handleSensorStateChange() {
  snprintf(msg, msgSize, sensorStateJson, "stateChange", currentState);
  statusCode = "501"; // not implemented
}

void handleWifi() {
  snprintf(msg, msgSize, wifiJson, ipAddrToChar(WiFi.localIP()).c_str(), macAddrToChar(WiFi.BSSID()).c_str(), WiFi.channel(), WiFi.RSSI());
  statusCode = "200";
}

void handleRequest() {
  // handle the request based on the path
  if      (path == "/resources") handleResources();
  else if (path == "/resources/states") handleStates();
  else if (path == sensorPath.c_str()) handleSensor();
  else if (path == "/resources/states/state") handleStatesState();
  else if (path == sensorStatePath.c_str()) handleSensorState();
  else if (path == "/resources/states/stateChange") handleStatesStateChange();
  else if (path == sensorStateChangePath.c_str()) handleSensorStateChange();
  else if (path == "/wifi") handleWifi();
  else statusCode = "404";
}

void sendResponse() {
  // Send the response to the client
  String response;
  if (statusCode == "200") {
    response = "HTTP/1.1 200 OK\r\n";
    response += "Content-Type: application/json\r\n\r\n";
    response += msg;
  }
  else {
    response = "HTTP/1.1 "+statusCode+"\r\n";
  }
#ifdef DEBUG
  Serial.println("Response:");
  Serial.println(response);
#endif
  client.print(response);
  delay(1);
}

void checkConnection()  {
  int wifiStatus = WiFi.status();
  if (wifiStatus != WL_CONNECTED) {
#ifdef DEBUG
    Serial.print("Lost connection status: ");
    Serial.print(wifiStatus);
    Serial.println();
#endif
    scanWifi();
    setupWifi();
  }
}

///////////////////
// Main routines //
///////////////////
void setup()  {
  setupSerial();
  setupHardware();
  scanWifi();
  setupWifi();
  setupMdns();
  setupNames();
  setupServer();
}

void loop()  {
  checkConnection();
  sendBeacon();
  sendState(false);
  checkInput();
  // Check if a client has connected
  client = server.available();
  if (client) {
    parseRequest();
    handleRequest();
    sendResponse();
  }
  delay(1000/sampleRate);
}

