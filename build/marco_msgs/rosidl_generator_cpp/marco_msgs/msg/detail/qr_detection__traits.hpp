// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from marco_msgs:msg/QrDetection.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__QR_DETECTION__TRAITS_HPP_
#define MARCO_MSGS__MSG__DETAIL__QR_DETECTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "marco_msgs/msg/detail/qr_detection__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'pose_in_camera'
#include "geometry_msgs/msg/detail/pose2_d__traits.hpp"

namespace marco_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const QrDetection & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: detected
  {
    out << "detected: ";
    rosidl_generator_traits::value_to_yaml(msg.detected, out);
    out << ", ";
  }

  // member: data
  {
    out << "data: ";
    rosidl_generator_traits::value_to_yaml(msg.data, out);
    out << ", ";
  }

  // member: pose_in_camera
  {
    out << "pose_in_camera: ";
    to_flow_style_yaml(msg.pose_in_camera, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: camera_frame
  {
    out << "camera_frame: ";
    rosidl_generator_traits::value_to_yaml(msg.camera_frame, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const QrDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: detected
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "detected: ";
    rosidl_generator_traits::value_to_yaml(msg.detected, out);
    out << "\n";
  }

  // member: data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "data: ";
    rosidl_generator_traits::value_to_yaml(msg.data, out);
    out << "\n";
  }

  // member: pose_in_camera
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pose_in_camera:\n";
    to_block_style_yaml(msg.pose_in_camera, out, indentation + 2);
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: camera_frame
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "camera_frame: ";
    rosidl_generator_traits::value_to_yaml(msg.camera_frame, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const QrDetection & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::msg::QrDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::msg::QrDetection & msg)
{
  return marco_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::msg::QrDetection>()
{
  return "marco_msgs::msg::QrDetection";
}

template<>
inline const char * name<marco_msgs::msg::QrDetection>()
{
  return "marco_msgs/msg/QrDetection";
}

template<>
struct has_fixed_size<marco_msgs::msg::QrDetection>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::msg::QrDetection>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::msg::QrDetection>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MARCO_MSGS__MSG__DETAIL__QR_DETECTION__TRAITS_HPP_
