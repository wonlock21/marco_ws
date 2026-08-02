// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:msg/QrDetection.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__QR_DETECTION__BUILDER_HPP_
#define MARCO_MSGS__MSG__DETAIL__QR_DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/msg/detail/qr_detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace msg
{

namespace builder
{

class Init_QrDetection_camera_frame
{
public:
  explicit Init_QrDetection_camera_frame(::marco_msgs::msg::QrDetection & msg)
  : msg_(msg)
  {}
  ::marco_msgs::msg::QrDetection camera_frame(::marco_msgs::msg::QrDetection::_camera_frame_type arg)
  {
    msg_.camera_frame = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

class Init_QrDetection_confidence
{
public:
  explicit Init_QrDetection_confidence(::marco_msgs::msg::QrDetection & msg)
  : msg_(msg)
  {}
  Init_QrDetection_camera_frame confidence(::marco_msgs::msg::QrDetection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_QrDetection_camera_frame(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

class Init_QrDetection_pose_in_camera
{
public:
  explicit Init_QrDetection_pose_in_camera(::marco_msgs::msg::QrDetection & msg)
  : msg_(msg)
  {}
  Init_QrDetection_confidence pose_in_camera(::marco_msgs::msg::QrDetection::_pose_in_camera_type arg)
  {
    msg_.pose_in_camera = std::move(arg);
    return Init_QrDetection_confidence(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

class Init_QrDetection_data
{
public:
  explicit Init_QrDetection_data(::marco_msgs::msg::QrDetection & msg)
  : msg_(msg)
  {}
  Init_QrDetection_pose_in_camera data(::marco_msgs::msg::QrDetection::_data_type arg)
  {
    msg_.data = std::move(arg);
    return Init_QrDetection_pose_in_camera(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

class Init_QrDetection_detected
{
public:
  explicit Init_QrDetection_detected(::marco_msgs::msg::QrDetection & msg)
  : msg_(msg)
  {}
  Init_QrDetection_data detected(::marco_msgs::msg::QrDetection::_detected_type arg)
  {
    msg_.detected = std::move(arg);
    return Init_QrDetection_data(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

class Init_QrDetection_header
{
public:
  Init_QrDetection_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_QrDetection_detected header(::marco_msgs::msg::QrDetection::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_QrDetection_detected(msg_);
  }

private:
  ::marco_msgs::msg::QrDetection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::msg::QrDetection>()
{
  return marco_msgs::msg::builder::Init_QrDetection_header();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__MSG__DETAIL__QR_DETECTION__BUILDER_HPP_
