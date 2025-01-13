import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class ObstacleAvoidingBot(Node):
    def __init__(self):
        super().__init__('obstacle_avoiding_bot')
        self.publisher = self.create_publisher(Twist, 'dolly2/cmd_vel', 40)
        self.subscription = self.create_subscription(LaserScan, 'dolly2/scan', self.get_scan_values, 40)
        self.timer = self.create_timer(0.2, self.send_cmd_vel)
        self.linear_vel = 0.22
        self.regions = {'right': 100, 'front': 100, 'left': 100}
        self.velocity = Twist()

    def get_scan_values(self, scan_data):
        self.regions = {
            'right': min(min(scan_data.ranges[0:120]), 100),
            'front': min(min(scan_data.ranges[120:240]), 100),
            'left': min(min(scan_data.ranges[240:360]), 100)
        }
        print("Lidar Data:\t", self.regions['left'],
              "\t", self.regions['front'],
              "\t", self.regions['right'])

    def send_cmd_vel(self):
        self.velocity.linear.x = self.linear_vel
        
        if all(self.regions[region] > 4 for region in ['left', 'front', 'right']):
            self.velocity.angular.z = 0.0
            print("going straight")
        elif self.regions['left'] > 4 and self.regions['front'] > 4 and self.regions['right'] <= 4:
            self.velocity.angular.z = 1.57
            print("turning left")
        elif self.regions['left'] <= 4 and self.regions['front'] > 4 and self.regions['right'] > 4:
            self.velocity.angular.z = -1.57
            print("turning right")
        elif (all(self.regions[region] <= 4 for region in ['left', 'front', 'right']) or 
            (self.regions['left'] > 4 and self.regions['front'] <= 4 and self.regions['right'] > 4)):
            self.velocity.angular.z = 3.14
            self.velocity.linear.x = -self.linear_vel
            print("turning around")
        
        self.publisher.publish(self.velocity)

def main():
    rclpy.init(args=None)
    bot = ObstacleAvoidingBot()

    try:
        rclpy.spin(bot)
    except KeyboardInterrupt:
        pass
    finally:
        bot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

