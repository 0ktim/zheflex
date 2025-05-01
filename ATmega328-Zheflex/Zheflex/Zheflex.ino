const int brakeButtonPin = 2;    // бутон спирачка (активен LOW)
const int gasButtonPin   = 3;    // бутон газ (активен HIGH)
const int ledPin         = 13;   // LED индикация

bool testStarted    = false;
bool gasReleased    = false;
unsigned long ledOnTime      = 0;
unsigned long gasReleaseTime = 0;
unsigned long brakePressTime = 0;

void setup() {
  pinMode(gasButtonPin, INPUT_PULLUP);
  pinMode(brakeButtonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // 1) Прочитаме командата от Python GUI, ако има такава
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'S') {
      // Start Test: включваме LED и инициализираме теста
      digitalWrite(ledPin, HIGH);
      ledOnTime    = millis();
      testStarted  = true;
      gasReleased  = false;
    }
    else if (cmd == 'T') {
      // Stop Test (при нужда): изгасваме LED
      digitalWrite(ledPin, LOW);
      testStarted  = false;
      gasReleased  = false;
    }
  }

  // 2) Ако тестът е стартиран, следим газта
  if (testStarted && !gasReleased) {
    // бутонът за газ е wired към PULLUP, затова HIGH = натиснат
    if (digitalRead(gasButtonPin) == HIGH) {
      gasReleaseTime = millis();
      gasReleased    = true;
    }
  }

  // 3) Ако газът е освободен, следим спирачката
  if (testStarted && gasReleased) {
    if (digitalRead(brakeButtonPin) == LOW) {
      brakePressTime = millis();

      unsigned long reactionTime = gasReleaseTime - ledOnTime;
      unsigned long moveTime     = brakePressTime - gasReleaseTime;

      // Изпращаме двата времена във формат CSV (точно това, което Python чака)
      Serial.print(reactionTime);
      Serial.print(",");
      Serial.println(moveTime);

      // рестарт на състоянията и изгасване на LED
      digitalWrite(ledPin, LOW);
      testStarted = false;
      gasReleased = false;

      delay(1000);  // пауза преди следващ тест
    }
  }
}
