cmake_minimum_required(VERSION 3.8)
project(marco_localization)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch simulation_test_maps
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
  scripts/ground_truth_pose.py
  scripts/amcl_initial_pose.py
  scripts/amcl_test_drive.py
  scripts/amcl_acceptance.py
  scripts/map_preview.py
  scripts/localization_manager.py
  scripts/mapping_manager.py
  scripts/buzzer_driver.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_mapping_localization_managers
    test/test_mapping_localization_managers.py
  )
endif()

ament_package()
