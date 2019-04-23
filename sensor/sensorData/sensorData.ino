#include <ros.h>
#include <std_msgs/String.h>
#include <std_msgs/Int32.h>
#include <std_msgs/Bool.h>


ros::NodeHandle  nh;

std_msgs::Int32 str_msg;
std_msgs::Bool trigger;

ros::Publisher sensorChatter("sensorData", &str_msg);
ros::Publisher triggerChatter("triggerData", &trigger);

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

  // Initiate ROS node
  nh.initNode();
  // Topics
  nh.advertise(sensorChatter);
  nh.advertise(triggerChatter);
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
  
  // Adds the current values to publishers
  trigger.data = isClose;
  str_msg.data = distance;

  // publish to topic
  sensorChatter.publish( &str_msg );
  triggerChatter.publish( &trigger );

  nh.spinOnce();

  delay(100);
}
