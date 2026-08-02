// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:srv/TaskComplete.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__BUILDER_HPP_
#define MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/srv/detail/task_complete__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_TaskComplete_Request_message
{
public:
  explicit Init_TaskComplete_Request_message(::marco_msgs::srv::TaskComplete_Request & msg)
  : msg_(msg)
  {}
  ::marco_msgs::srv::TaskComplete_Request message(::marco_msgs::srv::TaskComplete_Request::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::TaskComplete_Request msg_;
};

class Init_TaskComplete_Request_success
{
public:
  explicit Init_TaskComplete_Request_success(::marco_msgs::srv::TaskComplete_Request & msg)
  : msg_(msg)
  {}
  Init_TaskComplete_Request_message success(::marco_msgs::srv::TaskComplete_Request::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_TaskComplete_Request_message(msg_);
  }

private:
  ::marco_msgs::srv::TaskComplete_Request msg_;
};

class Init_TaskComplete_Request_task_id
{
public:
  Init_TaskComplete_Request_task_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskComplete_Request_success task_id(::marco_msgs::srv::TaskComplete_Request::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_TaskComplete_Request_success(msg_);
  }

private:
  ::marco_msgs::srv::TaskComplete_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::TaskComplete_Request>()
{
  return marco_msgs::srv::builder::Init_TaskComplete_Request_task_id();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_TaskComplete_Response_acknowledged
{
public:
  Init_TaskComplete_Response_acknowledged()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::marco_msgs::srv::TaskComplete_Response acknowledged(::marco_msgs::srv::TaskComplete_Response::_acknowledged_type arg)
  {
    msg_.acknowledged = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::TaskComplete_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::TaskComplete_Response>()
{
  return marco_msgs::srv::builder::Init_TaskComplete_Response_acknowledged();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__BUILDER_HPP_
