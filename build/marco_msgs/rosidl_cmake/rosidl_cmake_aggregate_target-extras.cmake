# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target marco_msgs::marco_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${marco_msgs_TARGETS}.
if(marco_msgs_TARGETS AND NOT TARGET marco_msgs::marco_msgs)
  add_library(marco_msgs::marco_msgs INTERFACE IMPORTED)
  set_target_properties(marco_msgs::marco_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${marco_msgs_TARGETS}")
endif()
