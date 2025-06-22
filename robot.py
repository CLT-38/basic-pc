#include <MotorDriver.h>
#include <ArduinoBLE.h>

// Utilisation des UUIDs standards Nordic UART Service (NUS)
BLEService nusService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E"); // Service UART Nordic

// RX: central -> périphérique (écriture + écriture sans réponse)
// TX: périphérique -> central (notification + lecture)
BLECharacteristic rxCharacteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLEWrite | BLEWriteWithoutResponse, 20);
BLECharacteristic txCharacteristic("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", BLENotify | BLERead, 20);

MotorDriver m;

void setup()
{
  Serial.begin(9600);
  if (!BLE.begin())
  {
    Serial.println("starting Bluetooth® Low Energy module failed!");
    while (1)
      ;
  }
  delay(5000);

  // set advertised local name and service UUID:
  BLE.setLocalName("CLTdemo-ArduinoBle");
  BLE.setAdvertisedService(nusService);

  // add the characteristics to the service
  nusService.addCharacteristic(rxCharacteristic);
  nusService.addCharacteristic(txCharacteristic);

  // add service
  BLE.addService(nusService);

  // Écriture initiale sur TX 
  uint8_t initMsg[1] = {0};
  txCharacteristic.writeValue(initMsg, 1);

  // start advertising
  BLE.advertise();
}

void loop()
{
  Serial.println("start program...");

  BLEDevice central = BLE.central();
  int instruction = 0;
  int lastInstruction = 0;
  unsigned long lastReceived = 0;
  const unsigned long timeout = 300; // ms

  if (central)
  {
    Serial.print("Connecting to central: ");
    Serial.println(central.address());
    Serial.print("Central local name: ");
    Serial.println(central.localName());
    Serial.print("Central advertised service UUIDs: ");
    for (int i = 0; i < central.advertisedServiceUuidCount(); i++)
    {
      Serial.print(central.advertisedServiceUuid(i));
      Serial.print(" ");
    }

    while (central.connected())
    {
      // Si le central écrit sur la caractéristique RX
      if (rxCharacteristic.written())
      {
        instruction = rxCharacteristic.value()[0];
        lastInstruction = instruction;
        lastReceived = millis();
        Serial.print(F("Valeur reçue: "));
        Serial.println(instruction);
      }

      // Si une instruction a été reçue récemment, on agit
      if (millis() - lastReceived < timeout)
      {
        switch (lastInstruction)
        {
        case 0:
          // Rien, stop
          m.motor(1, RELEASE, 0);
          m.motor(4, RELEASE, 0);
          m.motor(2, RELEASE, 0);
          m.motor(3, RELEASE, 0);
          break;
        case 8:
          m.motor(1, FORWARD, 128); // avant
          m.motor(4, BACKWARD, 128);
          m.motor(2, BACKWARD, 128);
          m.motor(3, FORWARD, 128);
          break;
        case 2:
          m.motor(1, BACKWARD, 128); // arrière
          m.motor(4, FORWARD, 128);
          m.motor(2, FORWARD, 128);
          m.motor(3, BACKWARD, 128);
          break;
        case 1:
          m.motor(1, BACKWARD, 128); // diagonal arrière vers la gauche
          m.motor(4, RELEASE, 0);
          m.motor(2, RELEASE, 0);
          m.motor(3, BACKWARD, 128);
          break;
        case 9:
          m.motor(1, FORWARD, 128); // diagonal avant vers la droite
          m.motor(4, RELEASE, 0);
          m.motor(2, RELEASE, 0);
          m.motor(3, FORWARD, 128);
          break;
        case 7:
          m.motor(1, RELEASE, 0); // diagonal avant vers la gauche
          m.motor(4, FORWARD, 128);
          m.motor(2, FORWARD, 128);
          m.motor(3, RELEASE, 0);
          break;
        case 3:
          m.motor(1, RELEASE, 0); // diagonal arrière vers la droite
          m.motor(4, BACKWARD, 128);
          m.motor(2, BACKWARD, 128);
          m.motor(3, RELEASE, 0);
          break;
        case 5:
          m.motor(1, RELEASE, 0); // Arrêter tous les moteurs
          m.motor(4, RELEASE, 0);
          m.motor(2, RELEASE, 0);
          m.motor(3, RELEASE, 0);
          break;
        default:
          Serial.println(F("Unexpected value"));
        }
      }
      else
      {
        // Timeout : arrêt sécurité
        m.motor(1, RELEASE, 0);
        m.motor(4, RELEASE, 0);
        m.motor(2, RELEASE, 0);
        m.motor(3, RELEASE, 0);
        lastInstruction = 0;
      }
      delay(5); // Petit délai pour éviter la saturation BLE
    }
  }
  Serial.print(F("Disconnected from central: "));
  Serial.println(central.address());

  m.motor(1, RELEASE, 0); // Stop all motors
  m.motor(4, RELEASE, 0);
  m.motor(2, RELEASE, 0);
  m.motor(3, RELEASE, 0);
  Serial.println("programme end...");
}
