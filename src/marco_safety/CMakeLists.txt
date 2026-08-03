cmake_minimum_required(VERSION 3.8)
project(marco_safety)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/safety_supervisor.py
  scripts/phase8_acceptance.py
  scripts/nav_action_obstacle_acceptance.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
