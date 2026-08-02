cmake_minimum_required(VERSION 3.8)
project(marco_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/LaneOffset.msg"
  "msg/QrDetection.msg"
  "msg/RobotStatus.msg"
  "action/DockToStation.action"
  "srv/AssignTask.srv"
  "srv/GatePermission.srv"
  "srv/TaskComplete.srv"
  "srv/StartMission.srv"
  DEPENDENCIES std_msgs geometry_msgs
)

ament_package()
