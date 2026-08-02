// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:srv/StartMission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__START_MISSION__BUILDER_HPP_
#define MARCO_MSGS__SRV__DETAIL__START_MISSION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/srv/detail/start_mission__struct.hpp"
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
auto build<::marco_msgs::srv::StartMission_Request>()
{
  return ::marco_msgs::srv::StartMission_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace srv
{

namespace builder
{

class Init_StartMission_Response_message
{
public:
  explicit Init_StartMission_Response_message(::marco_msgs::srv::StartMission_Response & msg)
  : msg_(msg)
  {}
  ::marco_msgs::srv::StartMission_Response message(::marco_msgs::srv::StartMission_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::srv::StartMission_Response msg_;
};

class Init_StartMission_Response_accepted
{
public:
  Init_StartMission_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartMission_Response_message accepted(::marco_msgs::srv::StartMission_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_StartMission_Response_message(msg_);
  }

private:
  ::marco_msgs::srv::StartMission_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::srv::StartMission_Response>()
{
  return marco_msgs::srv::builder::Init_StartMission_Response_accepted();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__START_MISSION__BUILDER_HPP_
