// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:srv/GatePermission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__BUILDER_HPP_
#define MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/srv/detail/gate_permission__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_GatePermission_Request_node_id
{
public:
  Init_GatePermission_Request_node_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::marco_msgs::srv::GatePermission_Request node_id(::marco_msgs::srv::GatePermission_Request::_node_id_type arg)
  {
    msg_.node_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::GatePermission_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::GatePermission_Request>()
{
  return marco_msgs::srv::builder::Init_GatePermission_Request_node_id();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_GatePermission_Response_message
{
public:
  explicit Init_GatePermission_Response_message(::marco_msgs::srv::GatePermission_Response & msg)
  : msg_(msg)
  {}
  ::marco_msgs::srv::GatePermission_Response message(::marco_msgs::srv::GatePermission_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::GatePermission_Response msg_;
};

class Init_GatePermission_Response_granted
{
public:
  Init_GatePermission_Response_granted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GatePermission_Response_message granted(::marco_msgs::srv::GatePermission_Response::_granted_type arg)
  {
    msg_.granted = std::move(arg);
    return Init_GatePermission_Response_message(msg_);
  }

private:
  ::marco_msgs::srv::GatePermission_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::GatePermission_Response>()
{
  return marco_msgs::srv::builder::Init_GatePermission_Response_granted();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__BUILDER_HPP_
