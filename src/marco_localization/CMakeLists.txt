cmake_minimum_required(VERSION 3.8)
project(marco_localization)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

# Betikler lib/ altina kurulur; ros2 run yalnizca orayi arar.
install(PROGRAMS
  scripts/odometry_check.py
  scripts/odometry_paths.py
  scripts/harita_kaydet.sh
  scripts/baslangic_poz.sh
  scripts/amcl_poz_kaydet.py
  scripts/fake_imu.py
  scripts/slam_test_drive.py
  scripts/slam_acceptance.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
