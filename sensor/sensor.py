#!/usr/bin/env python
import rospy
import sys
from std_msgs.msg import Int32
from std_msgs.msg import Bool


# takes in the data
def callback(data):
	rospy.loginfo(data.data)

# parameters specify the data that is returned 
# Sensor = distance, Trigger = True / Flase
def listener(argv):
    rospy.init_node('listener', anonymous=True)

    for arg in argv:
        if arg == 'sensor':
            rospy.Subscriber("sensorData", Int32, callback) 
        if arg == 'trigger':
            rospy.Subscriber("triggerData", Bool, callback)  
            

    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

    

if __name__ == '__main__':
    listener(sys.argv)