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
  "msg/ActiveField.msg"
  "msg/DemoStatus.msg"
  "msg/FieldEdge.msg"
  "msg/FieldInfo.msg"
  "msg/FieldNode.msg"
  "msg/FieldPackageStatus.msg"
  "msg/LaneOffset.msg"
  "msg/LocalizationStatus.msg"
  "msg/MapPixelPose.msg"
  "msg/MappingStatus.msg"
  "msg/QrDetection.msg"
  "msg/QrReaderDetection.msg"
  "msg/RobotStatus.msg"
  "msg/StationApproachConfig.msg"
  "action/DockToStation.action"
  "action/LiftLoad.action"
  "srv/ActivateField.srv"
  "srv/ArchiveField.srv"
  "srv/AssignTask.srv"
  "srv/DeleteFieldEdge.srv"
  "srv/DeleteFieldNode.srv"
  "srv/GatePermission.srv"
  "srv/GetActiveField.srv"
  "srv/GetFieldGraph.srv"
  "srv/GetStationApproachConfigs.srv"
  "srv/ListFields.srv"
  "srv/PixelToMap.srv"
  "srv/SaveCurrentPoseNode.srv"
  "srv/SaveFieldEdge.srv"
  "srv/SaveFieldNode.srv"
  "srv/SaveStationApproachConfig.srv"
  "srv/TaskComplete.srv"
  "srv/StartMission.srv"
  "srv/SubmitManualTask.srv"
  "srv/SubmitMission.srv"
  "srv/CancelMission.srv"
  "srv/ResetMissionSafety.srv"
  "srv/SaveMapping.srv"
  "srv/SaveDemoPoint.srv"
  "srv/SaveDemoRoutePoint.srv"
  "srv/ClearDemoRoute.srv"
  "srv/StartLocalization.srv"
  "srv/StartDemoScenario.srv"
  "srv/StartMapping.srv"
  "srv/ValidateField.srv"
  DEPENDENCIES std_msgs geometry_msgs
)

ament_package()
