#include <Servo.h>

Servo servoX;
Servo servoY;
Servo servoFire;

int angleX = 90;
int angleY = 90;
int targetX = 90;
int targetY = 90;

const int firePin = 11;  
const int fireRest = 90;  
const int fireShoot = 60; 

unsigned long lastUpdate = 0;
const int updateInterval = 15; 
const int moveSpeed = 1;       

bool fireCommand = false;     
unsigned long fireTime = 0;
const int fireDuration = 300;  

void setup() {
  Serial.begin(115200);

  servoX.attach(9);
  servoY.attach(10);
  servoFire.attach(firePin);

  servoX.write(angleX);
  servoY.write(angleY);
  servoFire.write(fireRest);

  delay(500);
}

void loop() {
  
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int c1 = data.indexOf(',');
    int c2 = data.indexOf(',', c1 + 1);

    if (c1 > 0 && c2 > 0) {
      targetX = data.substring(0, c1).toInt();
      targetY = data.substring(c1 + 1, c2).toInt();
      fireCommand = data.substring(c2 + 1).toInt() == 1;
    }
  }
  
  if (millis() - lastUpdate >= updateInterval) {
    lastUpdate = millis();

    if (angleX < targetX) angleX += moveSpeed;
    else if (angleX > targetX) angleX -= moveSpeed;

    if (angleY < targetY) angleY += moveSpeed;
    else if (angleY > targetY) angleY -= moveSpeed;

    servoX.write(angleX);
    servoY.write(angleY);
  }
  
  if (fireCommand) {
    servoFire.write(fireShoot);
    fireTime = millis();
    fireCommand = false;
  }

  if (millis() - fireTime > fireDuration) {
    servoFire.write(fireRest);
  }
}
