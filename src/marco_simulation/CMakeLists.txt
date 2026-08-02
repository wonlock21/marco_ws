cmake_minimum_required(VERSION 3.8)
project(marco_simulation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY worlds models launch config urdf
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/visual_test_drive.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
