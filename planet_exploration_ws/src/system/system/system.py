import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge
import cv2
import threading
import yaml
import numpy as np
from time import sleep

class ROS2Node(Node):
    def __init__(self):
        super().__init__('control_gui_node')
        self.bridge = CvBridge()
        self.camera1_sub = self.create_subscription(Image, '/turtlebot3_1/camera/image_raw', self.camera1_callback, 10)
        self.camera2_sub = self.create_subscription(Image, '/turtlebot3_2/camera/image_raw', self.camera2_callback, 10)
        self.robot1_log_sub = self.create_subscription(String, '/turtlebot3_1/log', self.robot1_log_callback, 10)
        self.robot2_log_sub = self.create_subscription(String, '/turtlebot3_2/log', self.robot2_log_callback, 10)
        self.turtlebot1_odom_sub = self.create_subscription(Odometry, '/turtlebot3_1/odom', self.turtlebot1_odom_callback, 10)
        self.turtlebot2_odom_sub = self.create_subscription(Odometry, '/turtlebot3_2/odom', self.turtlebot2_odom_callback, 10)
        self.turtlebot3_odom_sub = self.create_subscription(Odometry, '/turtlebot3_3/odom', self.turtlebot3_odom_callback, 10)
        self.robot1_status_sub = self.create_subscription(String, 'turtlebot3_1_status', self.robot1_status_callback, 10)
        self.robot2_status_sub = self.create_subscription(String, 'turtlebot3_2_status', self.robot2_status_callback, 10)

        self.robot3_status = False  # "미확인 생명체 발견" 상태를 추적
        
        self.alien_alert_shown = False  # 팝업창이 이미 뜬 여부를 추적

        self.camera1_frame = None
        self.camera2_frame = None
        self.camera3_frame = None
        self.robot1_log = ""
        self.robot2_log = ""
        self.robot3_log = ""
        self.turtlebot1_position = None
        self.turtlebot2_position = None
        self.turtlebot3_position = None
        self.robot1_logs = []
        self.robot2_logs = []

    def camera1_callback(self, msg):
        self.camera1_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def camera2_callback(self, msg):
        self.camera2_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def robot1_log_callback(self, msg):
        self.robot1_log = msg.data

    def robot2_log_callback(self, msg):
        self.robot2_log = msg.data

    def robot1_status_callback(self, msg):
        self.robot1_log = msg.data
        if len(self.robot1_logs) > 100:  # 최대 100개의 로그 유지
            self.robot1_logs.pop(0)
        if msg.data == "미확인 생명체 발견":
            self.robot3_status = True  # 미확인 생명체 발견 시 로봇 3의 위치 표시
            self.show_alert() 
    def robot2_status_callback(self, msg):
        self.robot2_log = msg.data
        if len(self.robot2_logs) > 100: 
            self.robot2_logs.pop(0)
        if msg.data == "미확인 생명체 발견":
            self.robot3_status = True  # 미확인 생명체 발견 시 로봇 3의 위치 표시
            self.show_alert()  

    def turtlebot1_odom_callback(self, msg):
        position = msg.pose.pose.position
        self.turtlebot1_position = (position.x, position.y)

    def turtlebot2_odom_callback(self, msg):
        position = msg.pose.pose.position
        self.turtlebot2_position = (position.x, position.y)

    def turtlebot3_odom_callback(self, msg):
        position = msg.pose.pose.position
        self.turtlebot3_position = (position.x, position.y)
    
    def show_alert(self):
        if not self.alien_alert_shown: 
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Alien!!")
            msg_box.setText("미확인 생명체 발견!")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)

            
            msg_box.setText("<h1>미확인 생명체 발견!</h1>")  
            
            
            msg_box.setStyleSheet("QMessageBox { min-width: 400px; min-height: 200px; }")
            
            msg_box.exec_()
            self.alien_alert_shown = True  # 팝업을 띄운 상태로 표시
            

class ControlGUI(QMainWindow):
    def __init__(self, ros_node):
        super().__init__()
        self.setWindowTitle("우주선 관제 시스템")
        self.setGeometry(100, 100, 1200, 800)
        self.ros_node = ros_node
        self.load_map()
        self.initUI()
        self.update_timer()

    def load_map(self):
        # yaml 파일 경로
        yaml_path = "/home/hyuna/test3_ws/map.yaml"
        with open(yaml_path, 'r') as file:
            map_data = yaml.safe_load(file)

        # pgm 파일 경로
        map_image = cv2.imread("/home/hyuna/test3_ws/map.pgm", cv2.IMREAD_GRAYSCALE)

      
        edges = cv2.Canny(map_image, 50, 150, apertureSize=3)

        # 경계의 중심 찾기
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea)

        # 경계의 중심을 기준으로 회전할 각도 계산
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]

        # 이미지 회전
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90

        rotation_matrix = cv2.getRotationMatrix2D((map_image.shape[1] // 2, map_image.shape[0] // 2), angle, 1)
        rotated_map = cv2.warpAffine(map_image, rotation_matrix, (map_image.shape[1], map_image.shape[0]))

        # 경계 찾기
        edges_rotated = cv2.Canny(rotated_map, 50, 150, apertureSize=3)
        contours_rotated, _ = cv2.findContours(edges_rotated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour_rotated = max(contours_rotated, key=cv2.contourArea)

        # 경계의 최소 외접 사각형 찾기
        x, y, w, h = cv2.boundingRect(largest_contour_rotated)

        # 경계를 기준으로 이미지 크롭
        cropped_map = rotated_map[y:y+h, x:x+w]

        # 크롭된 이미지를 RGB로 변환
        cropped_map_rgb = cv2.cvtColor(cropped_map, cv2.COLOR_GRAY2RGB)

        # 시계방향으로 90도 회전
        self.map_image = cv2.rotate(cropped_map_rgb, cv2.ROTATE_90_CLOCKWISE)
        self.original_map_image = self.map_image.copy()

    def initUI(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # top
        top_layout = QHBoxLayout()
        self.map_label = QLabel(self)

        
        height, width = self.map_image.shape[:2]
        bytes_per_line = 3 * width
        q_img = QImage(self.map_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # 맵 크기 
        self.map_label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio))
        self.map_label.setFixedHeight(515)
        self.map_label.setFixedWidth(600)
        self.map_label.setStyleSheet("background-color: black; color: white; border: 2px solid white;")

        log_layout = QVBoxLayout()
        self.robot1_log = QTextEdit("로봇 1 로그")
        self.robot2_log = QTextEdit("로봇 2 로그")
        self.robot1_log.setReadOnly(True)
        self.robot2_log.setReadOnly(True)
        log_layout.addWidget(QLabel("로봇 1 로그"))
        log_layout.addWidget(self.robot1_log)
        log_layout.addWidget(QLabel("로봇 2 로그"))
        log_layout.addWidget(self.robot2_log)

        top_layout.addWidget(self.map_label, 2)
        top_layout.addLayout(log_layout, 1)

        # bottom
        bottom_layout = QHBoxLayout()
        self.camera1_label = QLabel("로봇 1 카메라")
        self.camera2_label = QLabel("로봇 2 카메라")
        self.camera1_label.setStyleSheet("background-color: black;")
        self.camera2_label.setStyleSheet("background-color: black;")
        self.camera1_label.setFixedSize(600, 240)
        self.camera2_label.setFixedSize(600, 240)
        bottom_layout.addWidget(self.camera1_label)
        bottom_layout.addWidget(self.camera2_label)

        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E2E; }
            QLabel { color: white; font-size: 14px; border: 1px solid #44475A; }
            QTextEdit { background-color: #282A36; color: #F8F8F2; border: 1px solid #44475A; }
        """)

    def update_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(100)

    def update_display(self):
        if self.ros_node.camera1_frame is not None:
            resized_frame = cv2.resize(self.ros_node.camera1_frame, (600, 240))
            self.camera1_label.setPixmap(self.cv_to_pixmap(resized_frame))
        if self.ros_node.camera2_frame is not None:
            resized_frame = cv2.resize(self.ros_node.camera2_frame, (600, 240))
            self.camera2_label.setPixmap(self.cv_to_pixmap(resized_frame))

        self.map_image = self.original_map_image.copy()
        height, width = self.map_image.shape[:2]
        bytes_per_line = 3 * width
        q_img = QImage(self.map_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.map_label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio))
        
        # turtlebot 위치 업데이트
        if self.ros_node.turtlebot1_position:
            self.update_turtlebot_position(self.ros_node.turtlebot1_position, 'turtlebot1')
        if self.ros_node.turtlebot2_position:
            self.update_turtlebot_position(self.ros_node.turtlebot2_position, 'turtlebot2')
        if self.ros_node.robot3_status and self.ros_node.turtlebot3_position:
            self.update_turtlebot_position(self.ros_node.turtlebot3_position, 'turtlebot3')

        if self.ros_node.robot1_log:
            self.robot1_log.append(f"{self.ros_node.robot1_log}")
            self.robot1_log.verticalScrollBar().setValue(self.robot1_log.verticalScrollBar().maximum())

        if self.ros_node.robot2_log:
            self.robot2_log.append(f"{self.ros_node.robot2_log}")
            self.robot2_log.verticalScrollBar().setValue(self.robot2_log.verticalScrollBar().maximum())

    def update_turtlebot_position(self, position, turtlebot_name):
        pixmap = self.map_label.pixmap()
        painter = QPainter(pixmap)
        
        # 로봇 색상 설정 (turtlebot3_3은 파란색, 나머지는 빨간색)
        if turtlebot_name == "turtlebot3":
            painter.setPen(QColor(0, 0, 255))  # 파란색
            painter.setBrush(QColor(0, 0, 255))  
            display_name = "alien"  # turtlebot3_3은 "alien"으로 표시
        else:
            painter.setPen(QColor(255, 0, 0))  # 빨간색
            painter.setBrush(QColor(255, 0, 0)) 
            display_name = turtlebot_name  # 다른 로봇 이름 그대로 표시

        # 맵 크기 가져오기
        map_width = self.map_label.width()
        map_height = self.map_label.height()

        # Gazebo 좌표계에서 GUI 좌표계로 변환
        x_orig = (position[0] - (3.725180 - 18.38/2)) * map_width / 18.38
        y_orig = (position[1] - (0.274876 - 15.48/2)) * map_height / 15.48

        # 반시계 방향으로 90도 회전
        x = y_orig
        y = map_width - x_orig

        # 점대칭 적용 (맵의 중심을 기준으로)
        x = map_width - x

        # 오프셋 적용 (위치 조정)
        point = QPoint(int(x) - 25, int(y) - 45)

       
        painter.drawEllipse(point, 10, 10)  

        # 로봇 이름 표시
        font = QFont()
        font.setPointSize(8)  
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))  
        painter.drawText(point.x() + 12, point.y() + 5, display_name)  

        painter.end()
        self.map_label.setPixmap(pixmap)

    def cv_to_pixmap(self, frame):
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)
    
    def turtlebot3_status_callback(self, msg):
        if msg.data == "미확인 생명체 발견":
            self.show_alert()



def main():
    rclpy.init()
    ros_node = ROS2Node()
    app = QApplication(sys.argv)
    gui = ControlGUI(ros_node)
    gui.show()

    
    def ros_spin():
        rclpy.spin(ros_node)

    
    ros_thread = threading.Thread(target=ros_spin)
    ros_thread.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

