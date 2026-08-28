cmake_minimum_required(VERSION 3.8)
project(marco_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# ros2 run ile cagrilabilmesi icin share/ degil lib/ altina kurulmali.
install(PROGRAMS
  scripts/kayit_al.sh
  scripts/check_vehicle_contract.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(vehicle_contract test/test_vehicle_contract.py)
endif()

ament_package()
