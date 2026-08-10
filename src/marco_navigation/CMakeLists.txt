cmake_minimum_required(VERSION 3.8)
project(marco_navigation)

find_package(ament_cmake REQUIRED)

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
