import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import math
from time import sleep
from launch.actions import ExecuteProcess  
import subprocess

class DistanceMonitor(Node):
    def __init__(self):
        super().__init__('distance_monitor')
        
       
        self.subscription_1 = self.create_subscription(
            Odometry,
            '/turtlebot3_1/odom',
            self.odom_callback_1,
            10
        )
        self.subscription_2 = self.create_subscription(
            Odometry,
            '/turtlebot3_2/odom',
            self.odom_callback_2,
            10
        )
        self.subscription_3 = self.create_subscription(
            Odometry,
            '/turtlebot3_3/odom',
            self.odom_callback_3,
            10
        )
        
       
        self.publisher_1 = self.create_publisher(String, 'turtlebot3_1_status', 10)
        self.publisher_2 = self.create_publisher(String, 'turtlebot3_2_status', 10)
        
       
        self.pos_1 = None
        self.pos_2 = None
        self.pos_3 = None
        self.robot1_started = False
        self.robot2_started = False

        
        self.distance_threshold = 10  

        self.robot3_drive_active = False

    def odom_callback_1(self, msg):
        if not self.robot1_started:
            self.publish_start_status(1)
            self.robot1_started = True
        self.pos_1 = msg.pose.pose.position
        self.check_distance()

    def odom_callback_2(self, msg):
        if not self.robot2_started:
            self.publish_start_status(2)
            self.robot2_started = True
        self.pos_2 = msg.pose.pose.position
        self.check_distance()

    def odom_callback_3(self, msg):
        self.pos_3 = msg.pose.pose.position
        self.check_distance()

    def publish_start_status(self, robot_num):
        # "탐색 시작" 메시지 발행
        msg = String()
        msg.data = f'로봇{robot_num} 탐색 시작'
        if robot_num == 1:
            self.publisher_1.publish(msg)
        elif robot_num == 2:
            self.publisher_2.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')

        
        sleep(2)
        msg.data = f'로봇{robot_num} 탐색 중'
        if robot_num == 1:
            self.publisher_1.publish(msg)
        elif robot_num == 2:
            self.publisher_2.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')

    def check_distance(self):
        if self.pos_1 is not None and self.pos_3 is not None:
            dist_1_to_3 = self.calculate_distance(self.pos_1, self.pos_3)
            if dist_1_to_3 <= self.distance_threshold:
                self.get_logger().info('alien!')
                self.publish_alien_detection(1)
                if not self.robot3_drive_active: 
                    self.activate_robot3_drive()

        if self.pos_2 is not None and self.pos_3 is not None:
            dist_2_to_3 = self.calculate_distance(self.pos_2, self.pos_3)
            if dist_2_to_3 <= self.distance_threshold:
                self.get_logger().info('alien!')
                self.publish_alien_detection(2)
                if not self.robot3_drive_active: 
                    self.activate_robot3_drive()

    def calculate_distance(self, pos1, pos2):
        return math.sqrt((pos2.x - pos1.x) ** 2 + (pos2.y - pos1.y) ** 2)

    def publish_alien_detection(self, robot_num):
        msg = String()
        msg.data = "미확인 생명체 발견"
        if robot_num == 1:
            self.publisher_1.publish(msg)
        elif robot_num == 2:
            self.publisher_2.publish(msg)
        self.get_logger().info(f'Published to turtlebot3_{robot_num}_status: {msg.data}')
    
    def activate_robot3_drive(self):
        # Launch Robot 3's drive node dynamically using subprocess
        try:
            subprocess.Popen(['ros2', 'run', 'turtlebot3_gazebo', 'turtlebot3_drive', '--ros-args', '-r', '__ns:=/turtlebot3_3'])
            self.get_logger().info("Robot 3 drive activated.")
            self.robot3_drive_active = True  # Set flag to prevent reactivation
        except Exception as e:
            self.get_logger().error(f"Failed to activate robot 3 drive: {e}")


def main(args=None):
    rclpy.init(args=args)
    distance_monitor = DistanceMonitor()

    rclpy.spin(distance_monitor)

    distance_monitor.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
