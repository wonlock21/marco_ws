// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:srv/AssignTask.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__BUILDER_HPP_
#define MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/srv/detail/assign_task__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::AssignTask_Request>()
{
  return ::marco_msgs::srv::AssignTask_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_AssignTask_Response_message
{
public:
  explicit Init_AssignTask_Response_message(::marco_msgs::srv::AssignTask_Response & msg)
  : msg_(msg)
  {}
  ::marco_msgs::srv::AssignTask_Response message(::marco_msgs::srv::AssignTask_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::AssignTask_Response msg_;
};

class Init_AssignTask_Response_dropoff_node
{
public:
  explicit Init_AssignTask_Response_dropoff_node(::marco_msgs::srv::AssignTask_Response & msg)
  : msg_(msg)
  {}
  Init_AssignTask_Response_message dropoff_node(::marco_msgs::srv::AssignTask_Response::_dropoff_node_type arg)
  {
    msg_.dropoff_node = std::move(arg);
    return Init_AssignTask_Response_message(msg_);
  }

private:
  ::marco_msgs::srv::AssignTask_Response msg_;
};

class Init_AssignTask_Response_pickup_node
{
public:
  explicit Init_AssignTask_Response_pickup_node(::marco_msgs::srv::AssignTask_Response & msg)
  : msg_(msg)
  {}
  Init_AssignTask_Response_dropoff_node pickup_node(::marco_msgs::srv::AssignTask_Response::_pickup_node_type arg)
  {
    msg_.pickup_node = std::move(arg);
    return Init_AssignTask_Response_dropoff_node(msg_);
  }

private:
  ::marco_msgs::srv::AssignTask_Response msg_;
};

class Init_AssignTask_Response_task_id
{
public:
  explicit Init_AssignTask_Response_task_id(::marco_msgs::srv::AssignTask_Response & msg)
  : msg_(msg)
  {}
  Init_AssignTask_Response_pickup_node task_id(::marco_msgs::srv::AssignTask_Response::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_AssignTask_Response_pickup_node(msg_);
  }

private:
  ::marco_msgs::srv::AssignTask_Response msg_;
};

class Init_AssignTask_Response_success
{
public:
  Init_AssignTask_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AssignTask_Response_task_id success(::marco_msgs::srv::AssignTask_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_AssignTask_Response_task_id(msg_);
  }

private:
  ::marco_msgs::srv::AssignTask_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::AssignTask_Response>()
{
  return marco_msgs::srv::builder::Init_AssignTask_Response_success();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__BUILDER_HPP_
