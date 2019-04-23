const int trigPin = 8;
const int echoPin = 7;

bool isClose;
int distance;
long duration;
long lastCm, rangeThresh, rangeVariance, isCloseTimer, reactTime, noise;


void setup()
{
  // Threshold for the trigger (distance from sensor to person)
  rangeThresh = 90;
  // To elimit possible spikes in sensor data 
  rangeVariance = 15;
  // Counts the amount of spikes in row
  noise = 0;
  // Keep track of the duration of person standing in front of sensor (within the threshold, of course)
  isCloseTimer = 0;
  // Threshold for the isCloseTimer
  reactTime = 2;
  
  // Sets the trigPin as an Output
  pinMode(trigPin, OUTPUT);
  // Sets the echoPin as an Input
  pinMode(echoPin, INPUT);
  Serial.begin(9600);
}

void loop()
{
  // previous distance
  lastCm = distance;

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);

  // Calculating the distance
  distance = duration*0.034/2;
  
  if( (distance < lastCm+rangeVariance) && (distance > lastCm-rangeVariance) && (distance < rangeThresh) ){
    isCloseTimer ++;
    noise = 0;
  }
  else{
    noise++;
    if(noise > 2){
      isCloseTimer = 0;  
    }
   
  }
  if(isCloseTimer > reactTime*10){
    isClose = true;
  }
  else{
    isClose = false;
  }
  Serial.println(distance);


  delay(100);
}
