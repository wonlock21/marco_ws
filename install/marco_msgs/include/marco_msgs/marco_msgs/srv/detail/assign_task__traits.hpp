// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from marco_msgs:srv/AssignTask.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__TRAITS_HPP_
#define MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "marco_msgs/srv/detail/assign_task__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace marco_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const AssignTask_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AssignTask_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AssignTask_Request & msg, bool use_flow_style = false)
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
  const marco_msgs::srv::AssignTask_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::srv::AssignTask_Request & msg)
{
  return marco_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::srv::AssignTask_Request>()
{
  return "marco_msgs::srv::AssignTask_Request";
}

template<>
inline const char * name<marco_msgs::srv::AssignTask_Request>()
{
  return "marco_msgs/srv/AssignTask_Request";
}

template<>
struct has_fixed_size<marco_msgs::srv::AssignTask_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<marco_msgs::srv::AssignTask_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<marco_msgs::srv::AssignTask_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace marco_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const AssignTask_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: task_id
  {
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << ", ";
  }

  // member: pickup_node
  {
    out << "pickup_node: ";
    rosidl_generator_traits::value_to_yaml(msg.pickup_node, out);
    out << ", ";
  }

  // member: dropoff_node
  {
    out << "dropoff_node: ";
    rosidl_generator_traits::value_to_yaml(msg.dropoff_node, out);
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
  const AssignTask_Response & msg,
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

  // member: task_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << "\n";
  }

  // member: pickup_node
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pickup_node: ";
    rosidl_generator_traits::value_to_yaml(msg.pickup_node, out);
    out << "\n";
  }

  // member: dropoff_node
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dropoff_node: ";
    rosidl_generator_traits::value_to_yaml(msg.dropoff_node, out);
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

inline std::string to_yaml(const AssignTask_Response & msg, bool use_flow_style = false)
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
  const marco_msgs::srv::AssignTask_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  marco_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use marco_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const marco_msgs::srv::AssignTask_Response & msg)
{
  return marco_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<marco_msgs::srv::AssignTask_Response>()
{
  return "marco_msgs::srv::AssignTask_Response";
}

template<>
inline const char * name<marco_msgs::srv::AssignTask_Response>()
{
  return "marco_msgs/srv/AssignTask_Response";
}

template<>
struct has_fixed_size<marco_msgs::srv::AssignTask_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<marco_msgs::srv::AssignTask_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<marco_msgs::srv::AssignTask_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<marco_msgs::srv::AssignTask>()
{
  return "marco_msgs::srv::AssignTask";
}

template<>
inline const char * name<marco_msgs::srv::AssignTask>()
{
  return "marco_msgs/srv/AssignTask";
}

template<>
struct has_fixed_size<marco_msgs::srv::AssignTask>
  : std::integral_constant<
    bool,
    has_fixed_size<marco_msgs::srv::AssignTask_Request>::value &&
    has_fixed_size<marco_msgs::srv::AssignTask_Response>::value
  >
{
};

template<>
struct has_bounded_size<marco_msgs::srv::AssignTask>
  : std::integral_constant<
    bool,
    has_bounded_size<marco_msgs::srv::AssignTask_Request>::value &&
    has_bounded_size<marco_msgs::srv::AssignTask_Response>::value
  >
{
};

template<>
struct is_service<marco_msgs::srv::AssignTask>
  : std::true_type
{
};

template<>
struct is_service_request<marco_msgs::srv::AssignTask_Request>
  : std::true_type
{
};

template<>
struct is_service_response<marco_msgs::srv::AssignTask_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__TRAITS_HPP_
