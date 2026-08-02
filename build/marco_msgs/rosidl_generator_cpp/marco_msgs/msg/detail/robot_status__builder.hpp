// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:msg/RobotStatus.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__BUILDER_HPP_
#define MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/msg/detail/robot_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace msg
{

namespace builder
{

class Init_RobotStatus_gate_permission_granted
{
public:
  explicit Init_RobotStatus_gate_permission_granted(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  ::marco_msgs::msg::RobotStatus gate_permission_granted(::marco_msgs::msg::RobotStatus::_gate_permission_granted_type arg)
  {
    msg_.gate_permission_granted = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_plc_connected
{
public:
  explicit Init_RobotStatus_plc_connected(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_gate_permission_granted plc_connected(::marco_msgs::msg::RobotStatus::_plc_connected_type arg)
  {
    msg_.plc_connected = std::move(arg);
    return Init_RobotStatus_gate_permission_granted(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_last_qr_data
{
public:
  explicit Init_RobotStatus_last_qr_data(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_plc_connected last_qr_data(::marco_msgs::msg::RobotStatus::_last_qr_data_type arg)
  {
    msg_.last_qr_data = std::move(arg);
    return Init_RobotStatus_plc_connected(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_dropoff_node
{
public:
  explicit Init_RobotStatus_dropoff_node(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_last_qr_data dropoff_node(::marco_msgs::msg::RobotStatus::_dropoff_node_type arg)
  {
    msg_.dropoff_node = std::move(arg);
    return Init_RobotStatus_last_qr_data(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_pickup_node
{
public:
  explicit Init_RobotStatus_pickup_node(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_dropoff_node pickup_node(::marco_msgs::msg::RobotStatus::_pickup_node_type arg)
  {
    msg_.pickup_node = std::move(arg);
    return Init_RobotStatus_dropoff_node(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_task_id
{
public:
  explicit Init_RobotStatus_task_id(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_pickup_node task_id(::marco_msgs::msg::RobotStatus::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_RobotStatus_pickup_node(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_obstacle_detected
{
public:
  explicit Init_RobotStatus_obstacle_detected(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_task_id obstacle_detected(::marco_msgs::msg::RobotStatus::_obstacle_detected_type arg)
  {
    msg_.obstacle_detected = std::move(arg);
    return Init_RobotStatus_task_id(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_cross_track_error
{
public:
  explicit Init_RobotStatus_cross_track_error(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_obstacle_detected cross_track_error(::marco_msgs::msg::RobotStatus::_cross_track_error_type arg)
  {
    msg_.cross_track_error = std::move(arg);
    return Init_RobotStatus_obstacle_detected(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_next_node
{
public:
  explicit Init_RobotStatus_next_node(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_cross_track_error next_node(::marco_msgs::msg::RobotStatus::_next_node_type arg)
  {
    msg_.next_node = std::move(arg);
    return Init_RobotStatus_cross_track_error(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_current_route_edge
{
public:
  explicit Init_RobotStatus_current_route_edge(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_next_node current_route_edge(::marco_msgs::msg::RobotStatus::_current_route_edge_type arg)
  {
    msg_.current_route_edge = std::move(arg);
    return Init_RobotStatus_next_node(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_position_covariance
{
public:
  explicit Init_RobotStatus_position_covariance(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_current_route_edge position_covariance(::marco_msgs::msg::RobotStatus::_position_covariance_type arg)
  {
    msg_.position_covariance = std::move(arg);
    return Init_RobotStatus_current_route_edge(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_localization_valid
{
public:
  explicit Init_RobotStatus_localization_valid(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_position_covariance localization_valid(::marco_msgs::msg::RobotStatus::_localization_valid_type arg)
  {
    msg_.localization_valid = std::move(arg);
    return Init_RobotStatus_position_covariance(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_pose
{
public:
  explicit Init_RobotStatus_pose(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_localization_valid pose(::marco_msgs::msg::RobotStatus::_pose_type arg)
  {
    msg_.pose = std::move(arg);
    return Init_RobotStatus_localization_valid(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_estop_active
{
public:
  explicit Init_RobotStatus_estop_active(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_pose estop_active(::marco_msgs::msg::RobotStatus::_estop_active_type arg)
  {
    msg_.estop_active = std::move(arg);
    return Init_RobotStatus_pose(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_manual_mode_enabled
{
public:
  explicit Init_RobotStatus_manual_mode_enabled(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_estop_active manual_mode_enabled(::marco_msgs::msg::RobotStatus::_manual_mode_enabled_type arg)
  {
    msg_.manual_mode_enabled = std::move(arg);
    return Init_RobotStatus_estop_active(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_mission_state
{
public:
  explicit Init_RobotStatus_mission_state(::marco_msgs::msg::RobotStatus & msg)
  : msg_(msg)
  {}
  Init_RobotStatus_manual_mode_enabled mission_state(::marco_msgs::msg::RobotStatus::_mission_state_type arg)
  {
    msg_.mission_state = std::move(arg);
    return Init_RobotStatus_manual_mode_enabled(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

class Init_RobotStatus_header
{
public:
  Init_RobotStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RobotStatus_mission_state header(::marco_msgs::msg::RobotStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_RobotStatus_mission_state(msg_);
  }

private:
  ::marco_msgs::msg::RobotStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::msg::RobotStatus>()
{
  return marco_msgs::msg::builder::Init_RobotStatus_header();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__BUILDER_HPP_
