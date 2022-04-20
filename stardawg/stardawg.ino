
/*  (c) 2022 Bly Lee d.b.a. WonderGap, LLC
 *  This code is licensed under MIT license
 *  Solely intended for use at Science Gallery: Hooked in ATL, GA in 2022
 */

/*  The following program assumes 36 marbles per drop. Considering an equal distribution of questsions answered (i.e. everyone who does the experience must answer all 9 questions to complete the
 *  experience), that leaves 4 marbles per question (36/9=4). With that in mind, there are 5 different scenarios per question per drop.
 *  
 *  Scenario 1: 25% of respondants answered YES, 75% of respondants answered no
 *  Scenario 2: 75% of respondants answered YES, 25% of respondants answered no
 *  Scenario 3: 50% of respondants answered YES, 50% of respondants answered no
 *  Scenario 4: 100% of respondants answered YES, 0% of respondants answered no
 *  Scenario 5: 0% of respondants answered YES, 100% of respondants answered no
 *  
 *  With the current software architecture, real-time tracking from the RPi is not available at this time. However, the following solution should still provide a fantastic experience and ensure the
 *  data remains accurate even if the sample size from the community survery remains too small to be statistically accurate.
 *  
 *  To alter the drop scenario for each question, please edit the switch statement in the void loop() function (line 193 at the time of documentation). The scenarios can be changed by swapping the
 *  last argument in each drop(int relayYes, int relayNo, int instance) function call.
*/

//define GPIO pins for solenoid relays
int relay1 = 22; 
int relay2 = 23;
int relay3 = 24;
int relay4 = 25; 
int relay5 = 26;
int relay6 = 27;
int relay7 = 28; 
int relay8 = 29;
int relay9 = 30;
int relay10 = 31; 
int relay11 = 32;
int relay12 = 33;
int relay13 = 34; 
int relay14 = 35;
int relay15 = 36;
int relay16 = 37; 
int relay17 = 38;
int relay18 = 39;

//helper function to quickly power off all relays
void drop(int relayYes, int relayNo, int instance) 
{
    switch (instance) {
      //distribution of yes:no is 1:3
      case 1:
        //turn on all solenoid relays as needed
        digitalWrite(relayYes, HIGH);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        break;
      //distribution of yes:no is 3:1
      case 2:
        //turn on all solenoid relays as needed
        digitalWrite(relayYes, HIGH);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        break;
      //distribution of yes:no is 2:2
      case 3:
        //turn on all solenoid relays as needed
        digitalWrite(relayYes, HIGH);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        digitalWrite(relayNo, LOW);
        break;
      //distribution of yes:no is 4:0
      case 4:
        //turn on all solenoid relays as needed
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        delay(500);
        digitalWrite(relayYes, HIGH);
        delay(500);
        digitalWrite(relayYes, LOW);
        break;
      //distribution of yes:no is 0:4
      case 5:
        //turn on all solenoid relays as needed
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        delay(500);
        digitalWrite(relayNo, HIGH);
        delay(500);
        digitalWrite(relayNo, LOW);
        break;
    }

}

//helper function to quickly power off all relays
void powerOffAllRelays()
{
    digitalWrite(relay1, LOW);
    digitalWrite(relay2, LOW);
    digitalWrite(relay3, LOW);
    digitalWrite(relay4, LOW);
    digitalWrite(relay5, LOW);
    digitalWrite(relay6, LOW);
    digitalWrite(relay7, LOW);
    digitalWrite(relay8, LOW);
    digitalWrite(relay9, LOW);
    digitalWrite(relay10, LOW);
    digitalWrite(relay11, LOW);
    digitalWrite(relay12, LOW);
    digitalWrite(relay13, LOW);
    digitalWrite(relay14, LOW);
    digitalWrite(relay15, LOW);
    digitalWrite(relay16, LOW);
    digitalWrite(relay17, LOW);
    digitalWrite(relay18, LOW);
}

void setup() {
  //set baud rate
  Serial.begin(9600);

  //define output for relay pins
  pinMode(relay1, OUTPUT);
  pinMode(relay2, OUTPUT);
  pinMode(relay3, OUTPUT);
  pinMode(relay4, OUTPUT);
  pinMode(relay5, OUTPUT);
  pinMode(relay6, OUTPUT);
  pinMode(relay7, OUTPUT);
  pinMode(relay8, OUTPUT);
  pinMode(relay9, OUTPUT);
  pinMode(relay10, OUTPUT);
  pinMode(relay11, OUTPUT);
  pinMode(relay12, OUTPUT);
  pinMode(relay13, OUTPUT);
  pinMode(relay14, OUTPUT);
  pinMode(relay15, OUTPUT);
  pinMode(relay16, OUTPUT);
  pinMode(relay17, OUTPUT);
  pinMode(relay18, OUTPUT);

  //ensure all power is off
  powerOffAllRelays();
}

void loop() {
  if (Serial.available() > 0) {
    //store the serial value and subtract 0 to convert from byte to int
    int message = Serial.read() - '0';
    
    switch (message) {
      //serial message recieved from pi does NOT indicate a drop is needed
      case 0:
        break;
      //serial message recieved from pi indicates a DROP is needed
      case 1:
        //marble release
        drop(relay1, relay2, 1); //question 1
        drop(relay3, relay4, 3); //question 2
        drop(relay5, relay6, 5); //question 3
        drop(relay7, relay8, 2); //question 4
        drop(relay9, relay10, 4); //question 5
        drop(relay11, relay12, 1); //question 6
        drop(relay13, relay14, 3); //question 7
        drop(relay15, relay16, 2); //question 8
        drop(relay17, relay18, 2); //question 9
        powerOffAllRelays();
        break;
    }
  }
}
