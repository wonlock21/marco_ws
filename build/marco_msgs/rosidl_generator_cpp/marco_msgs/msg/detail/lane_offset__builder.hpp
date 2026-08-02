// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:msg/LaneOffset.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__BUILDER_HPP_
#define MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/msg/detail/lane_offset__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace msg
{

namespace builder
{

class Init_LaneOffset_camera_frame
{
public:
  explicit Init_LaneOffset_camera_frame(::marco_msgs::msg::LaneOffset & msg)
  : msg_(msg)
  {}
  ::marco_msgs::msg::LaneOffset camera_frame(::marco_msgs::msg::LaneOffset::_camera_frame_type arg)
  {
    msg_.camera_frame = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

class Init_LaneOffset_confidence
{
public:
  explicit Init_LaneOffset_confidence(::marco_msgs::msg::LaneOffset & msg)
  : msg_(msg)
  {}
  Init_LaneOffset_camera_frame confidence(::marco_msgs::msg::LaneOffset::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_LaneOffset_camera_frame(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

class Init_LaneOffset_heading_error
{
public:
  explicit Init_LaneOffset_heading_error(::marco_msgs::msg::LaneOffset & msg)
  : msg_(msg)
  {}
  Init_LaneOffset_confidence heading_error(::marco_msgs::msg::LaneOffset::_heading_error_type arg)
  {
    msg_.heading_error = std::move(arg);
    return Init_LaneOffset_confidence(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

class Init_LaneOffset_lateral_offset
{
public:
  explicit Init_LaneOffset_lateral_offset(::marco_msgs::msg::LaneOffset & msg)
  : msg_(msg)
  {}
  Init_LaneOffset_heading_error lateral_offset(::marco_msgs::msg::LaneOffset::_lateral_offset_type arg)
  {
    msg_.lateral_offset = std::move(arg);
    return Init_LaneOffset_heading_error(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

class Init_LaneOffset_detected
{
public:
  explicit Init_LaneOffset_detected(::marco_msgs::msg::LaneOffset & msg)
  : msg_(msg)
  {}
  Init_LaneOffset_lateral_offset detected(::marco_msgs::msg::LaneOffset::_detected_type arg)
  {
    msg_.detected = std::move(arg);
    return Init_LaneOffset_lateral_offset(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

class Init_LaneOffset_header
{
public:
  Init_LaneOffset_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_LaneOffset_detected header(::marco_msgs::msg::LaneOffset::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_LaneOffset_detected(msg_);
  }

private:
  ::marco_msgs::msg::LaneOffset msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::msg::LaneOffset>()
{
  return marco_msgs::msg::builder::Init_LaneOffset_header();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__BUILDER_HPP_
