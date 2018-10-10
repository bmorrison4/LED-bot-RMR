/**
 * Let's Robot LED bot controller code.
 * This handles all serial inputs from the Raspberry Pi.
 * Current hard coded signals to avoid:
 * f, b, l, r, s, t, o, p
 * 
 * Presently accepted signals:
 * y  red up
 * h  red down
 * u  green up
 * j  green down
 * i  blue up
 * k  blue down
 * n  all on
 * m  all off
 * z  test on
 * x  test off
 */

const int redPin = 3;
const int greenPin = 5;
const int bluePin = 6;

//String red = "red: ";
//String green = "green: ";
//String blue = "blue: ";

boolean debug = false;

int redVal = 0;
int greenVal = 0;
int blueVal = 0;
int brightnessStep = 25;

void setup() {
  Serial.begin(9600);
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  pinMode(13, OUTPUT);
  Serial.println("ready");
}

void loop() {
  if (Serial.available()) {
    char input = Serial.read();
    if (debug) {
      Serial.print("found command: ");
      Serial.println(input);
    }
    switch (input) {
      case 'y':
        redVal += brightnessStep;
        if (redVal > 255) { redVal = 255; }
        break;
      case 'h':
        redVal -= brightnessStep;
        if (redVal < 0) { redVal = 0; }
        break;
      case 'u':
        greenVal += brightnessStep;
        if (greenVal > 255) { greenVal = 255; }
        break;
      case 'j':
        greenVal -= brightnessStep;
        if (greenVal < 0) { greenVal = 0; }
        break;
      case 'i':
        blueVal += brightnessStep;
        if (blueVal > 255) { blueVal = 255; }
        break;
      case 'k':
        blueVal -= brightnessStep;
        if (blueVal < 0) { blueVal = 0; }
        break;
      case 'n':
        redVal = 255;
        greenVal = 255;
        blueVal = 255;
        break;
      case 'm':
        redVal = 0;
        greenVal = 0;
        blueVal = 0;
        break;
      case 'z':
        digitalWrite(13, HIGH);
        break;
      case 'x':
        digitalWrite(13, LOW);
        break;
      case 'd':
        debug = !debug;
        break;
      default:
        break;
    }

    if (debug) {
      Serial.print(redVal);
      Serial.print('\t');
      Serial.print(greenVal);
      Serial.print('\t');
      Serial.println(blueVal);
    }
 
    analogWrite(redPin, redVal);
    analogWrite(greenPin, greenVal);
    analogWrite(bluePin, blueVal);
  }


}


