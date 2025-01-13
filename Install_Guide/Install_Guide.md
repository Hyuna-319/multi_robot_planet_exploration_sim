# Install Guide



<br>

```
cd turtlebot3_ws
colcon build --symlink-install
```
**1. alien.dae** 

```
cp alien.dae /turtlebot3_ws/install/turtlebot3_gazebo/share/turtlebot3_gazebo/models/turtlebot3_common/meshes
```


**2. turtlebot3_alien**
```
cp -r turtlebot3_alien /turtlebot3_ws/install/turtlebot3_gazebo/share/turtlebot3_gazebo/models
```

**3. turtlebot3_alien.urdf**
```
cp turtlebot3_alien.urdf /turtlebot3_ws/install/turtlebot3_gazebo/share/turtlebot3_gazebo/urdf
```

**4. Execution**
```
cd planet_exploration_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install

```
```
ros2 run system system
ros2 launch urdf_tutorial muti_robots.launch.py
```
