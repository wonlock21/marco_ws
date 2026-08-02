// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:msg/RobotStatus.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_HPP_
#define MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"
// Member 'pose'
#include "geometry_msgs/msg/detail/pose_with_covariance_stamped__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__msg__RobotStatus __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__msg__RobotStatus __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct RobotStatus_
{
  using Type = RobotStatus_<ContainerAllocator>;

  explicit RobotStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init),
    pose(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->mission_state = 0;
      this->manual_mode_enabled = false;
      this->estop_active = false;
      this->localization_valid = false;
      this->position_covariance = 0.0f;
      this->current_route_edge = "";
      this->next_node = "";
      this->cross_track_error = 0.0f;
      this->obstacle_detected = false;
      this->task_id = "";
      this->pickup_node = "";
      this->dropoff_node = "";
      this->last_qr_data = "";
      this->plc_connected = false;
      this->gate_permission_granted = false;
    }
  }

  explicit RobotStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    pose(_alloc, _init),
    current_route_edge(_alloc),
    next_node(_alloc),
    task_id(_alloc),
    pickup_node(_alloc),
    dropoff_node(_alloc),
    last_qr_data(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->mission_state = 0;
      this->manual_mode_enabled = false;
      this->estop_active = false;
      this->localization_valid = false;
      this->position_covariance = 0.0f;
      this->current_route_edge = "";
      this->next_node = "";
      this->cross_track_error = 0.0f;
      this->obstacle_detected = false;
      this->task_id = "";
      this->pickup_node = "";
      this->dropoff_node = "";
      this->last_qr_data = "";
      this->plc_connected = false;
      this->gate_permission_granted = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _mission_state_type =
    uint8_t;
  _mission_state_type mission_state;
  using _manual_mode_enabled_type =
    bool;
  _manual_mode_enabled_type manual_mode_enabled;
  using _estop_active_type =
    bool;
  _estop_active_type estop_active;
  using _pose_type =
    geometry_msgs::msg::PoseWithCovarianceStamped_<ContainerAllocator>;
  _pose_type pose;
  using _localization_valid_type =
    bool;
  _localization_valid_type localization_valid;
  using _position_covariance_type =
    float;
  _position_covariance_type position_covariance;
  using _current_route_edge_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _current_route_edge_type current_route_edge;
  using _next_node_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _next_node_type next_node;
  using _cross_track_error_type =
    float;
  _cross_track_error_type cross_track_error;
  using _obstacle_detected_type =
    bool;
  _obstacle_detected_type obstacle_detected;
  using _task_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_id_type task_id;
  using _pickup_node_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _pickup_node_type pickup_node;
  using _dropoff_node_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _dropoff_node_type dropoff_node;
  using _last_qr_data_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _last_qr_data_type last_qr_data;
  using _plc_connected_type =
    bool;
  _plc_connected_type plc_connected;
  using _gate_permission_granted_type =
    bool;
  _gate_permission_granted_type gate_permission_granted;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__mission_state(
    const uint8_t & _arg)
  {
    this->mission_state = _arg;
    return *this;
  }
  Type & set__manual_mode_enabled(
    const bool & _arg)
  {
    this->manual_mode_enabled = _arg;
    return *this;
  }
  Type & set__estop_active(
    const bool & _arg)
  {
    this->estop_active = _arg;
    return *this;
  }
  Type & set__pose(
    const geometry_msgs::msg::PoseWithCovarianceStamped_<ContainerAllocator> & _arg)
  {
    this->pose = _arg;
    return *this;
  }
  Type & set__localization_valid(
    const bool & _arg)
  {
    this->localization_valid = _arg;
    return *this;
  }
  Type & set__position_covariance(
    const float & _arg)
  {
    this->position_covariance = _arg;
    return *this;
  }
  Type & set__current_route_edge(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->current_route_edge = _arg;
    return *this;
  }
  Type & set__next_node(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->next_node = _arg;
    return *this;
  }
  Type & set__cross_track_error(
    const float & _arg)
  {
    this->cross_track_error = _arg;
    return *this;
  }
  Type & set__obstacle_detected(
    const bool & _arg)
  {
    this->obstacle_detected = _arg;
    return *this;
  }
  Type & set__task_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_id = _arg;
    return *this;
  }
  Type & set__pickup_node(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->pickup_node = _arg;
    return *this;
  }
  Type & set__dropoff_node(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->dropoff_node = _arg;
    return *this;
  }
  Type & set__last_qr_data(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->last_qr_data = _arg;
    return *this;
  }
  Type & set__plc_connected(
    const bool & _arg)
  {
    this->plc_connected = _arg;
    return *this;
  }
  Type & set__gate_permission_granted(
    const bool & _arg)
  {
    this->gate_permission_granted = _arg;
    return *this;
  }

  // constant declarations
  static constexpr uint8_t STATE_IDLE =
    0u;
  static constexpr uint8_t STATE_TASK_RECEIVED =
    1u;
  static constexpr uint8_t STATE_MOVING_UNLOADED =
    2u;
  static constexpr uint8_t STATE_MOVING_LOADED =
    3u;
  static constexpr uint8_t STATE_WAITING_PLC =
    4u;
  static constexpr uint8_t STATE_RETURNING =
    5u;
  static constexpr uint8_t STATE_ERROR =
    6u;
  static constexpr uint8_t STATE_ESTOP =
    7u;

  // pointer types
  using RawPtr =
    marco_msgs::msg::RobotStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::msg::RobotStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::msg::RobotStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::msg::RobotStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__msg__RobotStatus
    std::shared_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__msg__RobotStatus
    std::shared_ptr<marco_msgs::msg::RobotStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RobotStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->mission_state != other.mission_state) {
      return false;
    }
    if (this->manual_mode_enabled != other.manual_mode_enabled) {
      return false;
    }
    if (this->estop_active != other.estop_active) {
      return false;
    }
    if (this->pose != other.pose) {
      return false;
    }
    if (this->localization_valid != other.localization_valid) {
      return false;
    }
    if (this->position_covariance != other.position_covariance) {
      return false;
    }
    if (this->current_route_edge != other.current_route_edge) {
      return false;
    }
    if (this->next_node != other.next_node) {
      return false;
    }
    if (this->cross_track_error != other.cross_track_error) {
      return false;
    }
    if (this->obstacle_detected != other.obstacle_detected) {
      return false;
    }
    if (this->task_id != other.task_id) {
      return false;
    }
    if (this->pickup_node != other.pickup_node) {
      return false;
    }
    if (this->dropoff_node != other.dropoff_node) {
      return false;
    }
    if (this->last_qr_data != other.last_qr_data) {
      return false;
    }
    if (this->plc_connected != other.plc_connected) {
      return false;
    }
    if (this->gate_permission_granted != other.gate_permission_granted) {
      return false;
    }
    return true;
  }
  bool operator!=(const RobotStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RobotStatus_

// alias to use template instance with default allocator
using RobotStatus =
  marco_msgs::msg::RobotStatus_<std::allocator<void>>;

// constant definitions
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_IDLE;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_TASK_RECEIVED;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_MOVING_UNLOADED;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_MOVING_LOADED;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_WAITING_PLC;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_RETURNING;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_ERROR;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t RobotStatus_<ContainerAllocator>::STATE_ESTOP;
#endif  // __cplusplus < 201703L

}  // namespace msg

}  // namespace marco_msgs

#endif  // MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_HPP_
