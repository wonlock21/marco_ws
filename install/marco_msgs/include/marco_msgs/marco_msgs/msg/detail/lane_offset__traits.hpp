// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from marco_msgs:msg/LaneOffset.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__TRAITS_HPP_
#define MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "marco_msgs/msg/detail/lane_offset__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace marco_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const LaneOffset & msg,
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

  // member: lateral_offset
  {
    out << "lateral_offset: ";
    rosidl_generator_traits::value_to_yaml(msg.lateral_offset, out);
    out << ", ";
  }

  // member: heading_error
  {
    out << "heading_error: ";
    rosidl_generator_traits::value_to_yaml(msg.heading_error, out);
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
  const LaneOffset & msg,
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

  // member: lateral_offset
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lateral_offset: ";
    rosidl_generator_traits::value_to_yaml(msg.lateral_offset, out);
    out << "\n";
  }

  // member: heading_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "heading_error: ";
    rosidl_generator_traits::value_to_yaml(msg.heading_error, out);
    out << "\n";
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

inline std::string to_yaml(const LaneOffset & msg, bool use_flow_style = false)
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
  const marco_msgs::msg::LaneOffset & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::msg::LaneOffset & msg)
{
  return marco_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::msg::LaneOffset>()
{
  return "marco_msgs::msg::LaneOffset";
}

template<>
inline const char * name<marco_msgs::msg::LaneOffset>()
{
  return "marco_msgs/msg/LaneOffset";
}

template<>
struct has_fixed_size<marco_msgs::msg::LaneOffset>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::msg::LaneOffset>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::msg::LaneOffset>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__TRAITS_HPP_
