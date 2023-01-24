#include <LiquidCrystal.h>
#include <DHT.h>

const uint8_t DHT_PIN = 7, DHT_TYPE = DHT11;

const uint8_t RS = 12, EN = 11;
const uint8_t D4 = 2, D5 = 3, D6 = 4, D7 = 5;

LiquidCrystal lcd(RS, EN, D4, D5, D6, D7);
DHT dht(DHT_PIN, DHT_TYPE);

int counter = 0;

void setup() {
    lcd.begin(16, 12);    // colums, row
    dht.begin();
    Serial.begin(9600);
}

void loop() {
    delay(2000);
    lcd.clear();
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (isnan(t) || isnan(h)) {
        lcd.print("ERROR");
        return;
    }
    counter += 1;

    lcd.setCursor(0, 0);
    lcd.print("Humidity: ");lcd.print(h);
    lcd.setCursor(0, 1);
    lcd.print("Temp: ");lcd.print(t);

    // upload data every 5 minutes
    if (counter >= 150) {
        if (Serial.availableForWrite() > 12) {
            Serial.print(h);Serial.print(' ');
            Serial.println(t);
        }
        counter = 0;
    }
}
