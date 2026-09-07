cmake_minimum_required(VERSION 3.8)
project(marco_navigation)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_core REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(std_msgs REQUIRED)

add_library(marco_obstacle_aware_progress_checker SHARED
  src/obstacle_aware_progress_checker.cpp
)
target_include_directories(marco_obstacle_aware_progress_checker PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(marco_obstacle_aware_progress_checker
  geometry_msgs
  nav2_core
  pluginlib
  rclcpp
  rclcpp_lifecycle
  std_msgs
)
pluginlib_export_plugin_description_file(
  nav2_core marco_navigation_plugins.xml
)

install(TARGETS marco_obstacle_aware_progress_checker
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY config launch behavior_trees maps graphs
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/rota_hesapla.py
  scripts/nav2_test_goals.py
  scripts/nav2_acceptance.py
  scripts/simulation_scan_gate.py
  scripts/route_graph_validator.py
  scripts/route_graph_visualizer.py
  scripts/route_acceptance.py
  scripts/route_test_mission.py
  scripts/phase7_final_acceptance.py
  scripts/rpp_calibrate.py
  scripts/abs_speed_limit_proof.py
  scripts/speed_limit_manager.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
