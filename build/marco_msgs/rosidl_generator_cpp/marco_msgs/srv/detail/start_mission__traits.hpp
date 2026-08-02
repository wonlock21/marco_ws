// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from marco_msgs:srv/StartMission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__START_MISSION__TRAITS_HPP_
#define MARCO_MSGS__SRV__DETAIL__START_MISSION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "marco_msgs/srv/detail/start_mission__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace marco_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const StartMission_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const StartMission_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const StartMission_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::srv::StartMission_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::srv::StartMission_Request & msg)
{
  return marco_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::srv::StartMission_Request>()
{
  return "marco_msgs::srv::StartMission_Request";
}

template<>
inline const char * name<marco_msgs::srv::StartMission_Request>()
{
  return "marco_msgs/srv/StartMission_Request";
}

template<>
struct has_fixed_size<marco_msgs::srv::StartMission_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<marco_msgs::srv::StartMission_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<marco_msgs::srv::StartMission_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace marco_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const StartMission_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: accepted
  {
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const StartMission_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: accepted
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const StartMission_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::srv::StartMission_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::srv::StartMission_Response & msg)
{
  return marco_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::srv::StartMission_Response>()
{
  return "marco_msgs::srv::StartMission_Response";
}

template<>
inline const char * name<marco_msgs::srv::StartMission_Response>()
{
  return "marco_msgs/srv/StartMission_Response";
}

template<>
struct has_fixed_size<marco_msgs::srv::StartMission_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::srv::StartMission_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::srv::StartMission_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<marco_msgs::srv::StartMission>()
{
  return "marco_msgs::srv::StartMission";
}

template<>
inline const char * name<marco_msgs::srv::StartMission>()
{
  return "marco_msgs/srv/StartMission";
}

template<>
struct has_fixed_size<marco_msgs::srv::StartMission>
  : std::integral_constant<
    bool,
    has_fixed_size<marco_msgs::srv::StartMission_Request>::value &&
    has_fixed_size<marco_msgs::srv::StartMission_Response>::value
  >
{
};

template<>
struct has_bounded_size<marco_msgs::srv::StartMission>
  : std::integral_constant<
    bool,
    has_bounded_size<marco_msgs::srv::StartMission_Request>::value &&
    has_bounded_size<marco_msgs::srv::StartMission_Response>::value
  >
{
};

template<>
struct is_service<marco_msgs::srv::StartMission>
  : std::true_type
{
};

template<>
struct is_service_request<marco_msgs::srv::StartMission_Request>
  : std::true_type
{
};

template<>
struct is_service_response<marco_msgs::srv::StartMission_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // MARCO_MSGS__SRV__DETAIL__START_MISSION__TRAITS_HPP_
