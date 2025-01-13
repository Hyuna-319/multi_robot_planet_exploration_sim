#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
import random

class DollyExplorer(Node):
    def __init__(self, robot_name):
        super().__init__(f'{robot_name}_explorer')
        self.robot_name = robot_name
        self.velocity_publisher = self.create_publisher(Twist, f'/{robot_name}/cmd_vel', 10)
        self.scan_subscriber = self.create_subscription(LaserScan, f'/{robot_name}/scan', self.scan_callback, 10)
        self.odom_subscriber = self.create_subscription(Odometry, f'/{robot_name}/odom', self.odom_callback, 10)
        self.joint_states_subscriber = self.create_subscription(JointState, f'/{robot_name}/joint_states', self.joint_states_callback, 10)

        self.timer = self.create_timer(0.1, self.explore)

        self.obstacle_detected = False
        self.current_position = [0.0, 0.0]
        self.explored_area = set()

        self.obstacle_ranges = []  # LaserScan 거리 값 저장
        self.wheel_speeds = {}  # 바퀴 속도 저장 ("wheel_name": speed)

    def scan_callback(self, msg):
        self.obstacle_ranges = msg.ranges
        min_distance = min(self.obstacle_ranges)

        if min_distance < 0.5:  # 장애물이 가까운 경우
            self.obstacle_detected = True
        else:
            self.obstacle_detected = False

    def odom_callback(self, msg):
        self.current_position = [
            msg.pose.pose.position.x,
            msg.pose.pose.position.y
        ]
        # 현재 위치를 탐색된 영역으로 기록
        self.explored_area.add((round(self.current_position[0], 1), round(self.current_position[1], 1)))

    def joint_states_callback(self, msg):
        for i, name in enumerate(msg.name):
            self.wheel_speeds[name] = msg.velocity[i]

    def explore(self):
        twist = Twist()

        if self.obstacle_detected:
            # 장애물이 있는 방향을 피하기 위해 바퀴 속도 차이를 조정하여 회전
            left_distance = min(self.obstacle_ranges[45:135])  # 왼쪽 범위 (45도 ~ 135도)
            right_distance = min(self.obstacle_ranges[225:315])  # 오른쪽 범위 (225도 ~ 315도)

            if left_distance < right_distance:
                # 왼쪽 장애물이 더 가깝다면 오른쪽 바퀴만 움직임
                twist.linear.x = 0.0
                twist.angular.z = 2.0
            elif right_distance < left_distance:
                # 오른쪽 장애물이 더 가깝다면 왼쪽 바퀴만 움직임
                twist.linear.x = 0.0
                twist.angular.z = -2.0
            else:
                # 두 장애물이 비슷하다면 랜덤으로 회전
                twist.linear.x = 0.0
                twist.angular.z = random.uniform(-2.0, 2.0)
        else:
            # 장애물이 없으면 부드럽게 전진
            twist.linear.x = 0.2
            twist.angular.z = random.uniform(-0.5, 0.5)

        # 실제 제어 신호를 생성하고 퍼블리시합니다.
        self.velocity_publisher.publish(twist)

        # 탐색 진행 상황 로깅
        self.get_logger().info(f'{self.robot_name} position: ({self.current_position[0]:.2f}, {self.current_position[1]:.2f}), Explored area: {len(self.explored_area)}')
        self.get_logger().info(f'{self.robot_name} wheel speeds: {self.wheel_speeds}')


def main(args=None):
    rclpy.init(args=args)

    dolly1_explorer = DollyExplorer('dolly1')
    dolly2_explorer = DollyExplorer('dolly2')

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(dolly1_explorer)
    executor.add_node(dolly2_explorer)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        dolly1_explorer.destroy_node()
        dolly2_explorer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

