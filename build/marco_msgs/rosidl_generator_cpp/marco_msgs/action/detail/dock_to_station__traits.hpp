// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__TRAITS_HPP_
#define MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "marco_msgs/action/detail/dock_to_station__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_Goal & msg,
  std::ostream & out)
{
  out << "{";
  // member: station_id
  {
    out << "station_id: ";
    rosidl_generator_traits::value_to_yaml(msg.station_id, out);
    out << ", ";
  }

  // member: position_tolerance
  {
    out << "position_tolerance: ";
    rosidl_generator_traits::value_to_yaml(msg.position_tolerance, out);
    out << ", ";
  }

  // member: yaw_tolerance
  {
    out << "yaw_tolerance: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw_tolerance, out);
    out << ", ";
  }

  // member: approach_type
  {
    out << "approach_type: ";
    rosidl_generator_traits::value_to_yaml(msg.approach_type, out);
    out << ", ";
  }

  // member: timeout
  {
    out << "timeout: ";
    rosidl_generator_traits::value_to_yaml(msg.timeout, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_Goal & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: station_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "station_id: ";
    rosidl_generator_traits::value_to_yaml(msg.station_id, out);
    out << "\n";
  }

  // member: position_tolerance
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_tolerance: ";
    rosidl_generator_traits::value_to_yaml(msg.position_tolerance, out);
    out << "\n";
  }

  // member: yaw_tolerance
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "yaw_tolerance: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw_tolerance, out);
    out << "\n";
  }

  // member: approach_type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "approach_type: ";
    rosidl_generator_traits::value_to_yaml(msg.approach_type, out);
    out << "\n";
  }

  // member: timeout
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "timeout: ";
    rosidl_generator_traits::value_to_yaml(msg.timeout, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_Goal & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_Goal & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_Goal & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_Goal>()
{
  return "marco_msgs::action::DockToStation_Goal";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_Goal>()
{
  return "marco_msgs/action/DockToStation_Goal";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_Goal>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_Goal>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::action::DockToStation_Goal>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_Result & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: final_position_error
  {
    out << "final_position_error: ";
    rosidl_generator_traits::value_to_yaml(msg.final_position_error, out);
    out << ", ";
  }

  // member: final_yaw_error
  {
    out << "final_yaw_error: ";
    rosidl_generator_traits::value_to_yaml(msg.final_yaw_error, out);
    out << ", ";
  }

  // member: result_code
  {
    out << "result_code: ";
    rosidl_generator_traits::value_to_yaml(msg.result_code, out);
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
  const DockToStation_Result & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: final_position_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "final_position_error: ";
    rosidl_generator_traits::value_to_yaml(msg.final_position_error, out);
    out << "\n";
  }

  // member: final_yaw_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "final_yaw_error: ";
    rosidl_generator_traits::value_to_yaml(msg.final_yaw_error, out);
    out << "\n";
  }

  // member: result_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "result_code: ";
    rosidl_generator_traits::value_to_yaml(msg.result_code, out);
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

inline std::string to_yaml(const DockToStation_Result & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_Result & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_Result & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_Result>()
{
  return "marco_msgs::action::DockToStation_Result";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_Result>()
{
  return "marco_msgs/action/DockToStation_Result";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_Result>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_Result>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::action::DockToStation_Result>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_Feedback & msg,
  std::ostream & out)
{
  out << "{";
  // member: phase
  {
    out << "phase: ";
    rosidl_generator_traits::value_to_yaml(msg.phase, out);
    out << ", ";
  }

  // member: position_error
  {
    out << "position_error: ";
    rosidl_generator_traits::value_to_yaml(msg.position_error, out);
    out << ", ";
  }

  // member: yaw_error
  {
    out << "yaw_error: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw_error, out);
    out << ", ";
  }

  // member: distance_remaining
  {
    out << "distance_remaining: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_remaining, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_Feedback & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: phase
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "phase: ";
    rosidl_generator_traits::value_to_yaml(msg.phase, out);
    out << "\n";
  }

  // member: position_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_error: ";
    rosidl_generator_traits::value_to_yaml(msg.position_error, out);
    out << "\n";
  }

  // member: yaw_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "yaw_error: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw_error, out);
    out << "\n";
  }

  // member: distance_remaining
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "distance_remaining: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_remaining, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_Feedback & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_Feedback & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_Feedback & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_Feedback>()
{
  return "marco_msgs::action::DockToStation_Feedback";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_Feedback>()
{
  return "marco_msgs/action/DockToStation_Feedback";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_Feedback>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_Feedback>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::action::DockToStation_Feedback>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"
// Member 'goal'
#include "marco_msgs/action/detail/dock_to_station__traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_SendGoal_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
    out << ", ";
  }

  // member: goal
  {
    out << "goal: ";
    to_flow_style_yaml(msg.goal, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_SendGoal_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }

  // member: goal
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal:\n";
    to_block_style_yaml(msg.goal, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_SendGoal_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_SendGoal_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_SendGoal_Request & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_SendGoal_Request>()
{
  return "marco_msgs::action::DockToStation_SendGoal_Request";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_SendGoal_Request>()
{
  return "marco_msgs/action/DockToStation_SendGoal_Request";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_SendGoal_Request>
  : std::integral_constant<bool, has_fixed_size<marco_msgs::action::DockToStation_Goal>::value && has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_SendGoal_Request>
  : std::integral_constant<bool, has_bounded_size<marco_msgs::action::DockToStation_Goal>::value && has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<marco_msgs::action::DockToStation_SendGoal_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_SendGoal_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: accepted
  {
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << ", ";
  }

  // member: stamp
  {
    out << "stamp: ";
    to_flow_style_yaml(msg.stamp, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_SendGoal_Response & msg,
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

  // member: stamp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "stamp:\n";
    to_block_style_yaml(msg.stamp, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_SendGoal_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_SendGoal_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_SendGoal_Response & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_SendGoal_Response>()
{
  return "marco_msgs::action::DockToStation_SendGoal_Response";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_SendGoal_Response>()
{
  return "marco_msgs/action/DockToStation_SendGoal_Response";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_SendGoal_Response>
  : std::integral_constant<bool, has_fixed_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_SendGoal_Response>
  : std::integral_constant<bool, has_bounded_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct is_message<marco_msgs::action::DockToStation_SendGoal_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<marco_msgs::action::DockToStation_SendGoal>()
{
  return "marco_msgs::action::DockToStation_SendGoal";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_SendGoal>()
{
  return "marco_msgs/action/DockToStation_SendGoal";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_SendGoal>
  : std::integral_constant<
    bool,
    has_fixed_size<marco_msgs::action::DockToStation_SendGoal_Request>::value &&
    has_fixed_size<marco_msgs::action::DockToStation_SendGoal_Response>::value
  >
{
};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_SendGoal>
  : std::integral_constant<
    bool,
    has_bounded_size<marco_msgs::action::DockToStation_SendGoal_Request>::value &&
    has_bounded_size<marco_msgs::action::DockToStation_SendGoal_Response>::value
  >
{
};

template<>
struct is_service<marco_msgs::action::DockToStation_SendGoal>
  : std::true_type
{
};

template<>
struct is_service_request<marco_msgs::action::DockToStation_SendGoal_Request>
  : std::true_type
{
};

template<>
struct is_service_response<marco_msgs::action::DockToStation_SendGoal_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_GetResult_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_GetResult_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_GetResult_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_GetResult_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_GetResult_Request & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_GetResult_Request>()
{
  return "marco_msgs::action::DockToStation_GetResult_Request";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_GetResult_Request>()
{
  return "marco_msgs/action/DockToStation_GetResult_Request";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_GetResult_Request>
  : std::integral_constant<bool, has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_GetResult_Request>
  : std::integral_constant<bool, has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<marco_msgs::action::DockToStation_GetResult_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'result'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_GetResult_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: result
  {
    out << "result: ";
    to_flow_style_yaml(msg.result, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_GetResult_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: result
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "result:\n";
    to_block_style_yaml(msg.result, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_GetResult_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_GetResult_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_GetResult_Response & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_GetResult_Response>()
{
  return "marco_msgs::action::DockToStation_GetResult_Response";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_GetResult_Response>()
{
  return "marco_msgs/action/DockToStation_GetResult_Response";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_GetResult_Response>
  : std::integral_constant<bool, has_fixed_size<marco_msgs::action::DockToStation_Result>::value> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_GetResult_Response>
  : std::integral_constant<bool, has_bounded_size<marco_msgs::action::DockToStation_Result>::value> {};

template<>
struct is_message<marco_msgs::action::DockToStation_GetResult_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<marco_msgs::action::DockToStation_GetResult>()
{
  return "marco_msgs::action::DockToStation_GetResult";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_GetResult>()
{
  return "marco_msgs/action/DockToStation_GetResult";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_GetResult>
  : std::integral_constant<
    bool,
    has_fixed_size<marco_msgs::action::DockToStation_GetResult_Request>::value &&
    has_fixed_size<marco_msgs::action::DockToStation_GetResult_Response>::value
  >
{
};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_GetResult>
  : std::integral_constant<
    bool,
    has_bounded_size<marco_msgs::action::DockToStation_GetResult_Request>::value &&
    has_bounded_size<marco_msgs::action::DockToStation_GetResult_Response>::value
  >
{
};

template<>
struct is_service<marco_msgs::action::DockToStation_GetResult>
  : std::true_type
{
};

template<>
struct is_service_request<marco_msgs::action::DockToStation_GetResult_Request>
  : std::true_type
{
};

template<>
struct is_service_response<marco_msgs::action::DockToStation_GetResult_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"
// Member 'feedback'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__traits.hpp"

namespace marco_msgs
{

namespace action
{

inline void to_flow_style_yaml(
  const DockToStation_FeedbackMessage & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
    out << ", ";
  }

  // member: feedback
  {
    out << "feedback: ";
    to_flow_style_yaml(msg.feedback, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DockToStation_FeedbackMessage & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }

  // member: feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "feedback:\n";
    to_block_style_yaml(msg.feedback, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DockToStation_FeedbackMessage & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_generator_traits
{

[[deprecated("use marco_msgs::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const marco_msgs::action::DockToStation_FeedbackMessage & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::action::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::action::DockToStation_FeedbackMessage & msg)
{
  return marco_msgs::action::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::action::DockToStation_FeedbackMessage>()
{
  return "marco_msgs::action::DockToStation_FeedbackMessage";
}

template<>
inline const char * name<marco_msgs::action::DockToStation_FeedbackMessage>()
{
  return "marco_msgs/action/DockToStation_FeedbackMessage";
}

template<>
struct has_fixed_size<marco_msgs::action::DockToStation_FeedbackMessage>
  : std::integral_constant<bool, has_fixed_size<marco_msgs::action::DockToStation_Feedback>::value && has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<marco_msgs::action::DockToStation_FeedbackMessage>
  : std::integral_constant<bool, has_bounded_size<marco_msgs::action::DockToStation_Feedback>::value && has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<marco_msgs::action::DockToStation_FeedbackMessage>
  : std::true_type {};

}  // namespace rosidl_generator_traits


namespace rosidl_generator_traits
{

template<>
struct is_action<marco_msgs::action::DockToStation>
  : std::true_type
{
};

template<>
struct is_action_goal<marco_msgs::action::DockToStation_Goal>
  : std::true_type
{
};

template<>
struct is_action_result<marco_msgs::action::DockToStation_Result>
  : std::true_type
{
};

template<>
struct is_action_feedback<marco_msgs::action::DockToStation_Feedback>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits


#endif  // MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__TRAITS_HPP_
