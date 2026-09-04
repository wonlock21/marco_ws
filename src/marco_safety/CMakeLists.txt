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

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(
    test_safety_supervisor
    test/test_safety_supervisor.py
    TIMEOUT 30
  )
endif()

ament_package()
