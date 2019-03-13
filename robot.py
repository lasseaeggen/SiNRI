#!/usr/bin/env python
import rospy
import sys
from std_msgs.msg import Int32
from std_msgs.msg import Bool
from std_msgs.msg import String



class Robot():
    def __init__ (self):
        self.distance = 0

        self.Trigger = False

        self.response = False

        self.lastResponse = False

        self.loop_rate = rospy.Rate(10)
        
        #Subscriber for the distance from utrasound
        rospy.Subscriber("sensorData", Int32, self.callbackDist)
        #Subscriber for trigger from ultrasound. (3seconds+ in front of the ultrasound within 30cm)
        rospy.Subscriber("triggerData", Bool, self.callbackTrig)

        self.pub = rospy.Publisher("/cyborg_controller/register_event", String, queue_size=10)


    # takes in the data
    def callbackDist(self, data):
        self.distance = data.data
        rospy.loginfo(self.distance)

    def callbackTrig(self, data):
        self.trigger = data.data
        rospy.loginfo(self.trigger)

    def run(self):
        while not rospy.is_shutdown():
            if(self.distance < 20):
                self.lastResponse = self.response
                self.response = True
            
            else:
                self.lastResponse = self.response
                self.response = False
            if(self.response and not self.lastResponse):
                self.pub.publish("obstructionEvent")
            self.loop_rate.sleep()


if __name__ == '__main__':
    rospy.init_node("robotNode", anonymous = True)
    robot = Robot()
    robot.run()