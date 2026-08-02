// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_HPP_
#define MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_Goal __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_Goal __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_Goal_
{
  using Type = DockToStation_Goal_<ContainerAllocator>;

  explicit DockToStation_Goal_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->station_id = "";
      this->position_tolerance = 0.0f;
      this->yaw_tolerance = 0.0f;
      this->approach_type = 0;
      this->timeout = 0.0f;
    }
  }

  explicit DockToStation_Goal_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : station_id(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->station_id = "";
      this->position_tolerance = 0.0f;
      this->yaw_tolerance = 0.0f;
      this->approach_type = 0;
      this->timeout = 0.0f;
    }
  }

  // field types and members
  using _station_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _station_id_type station_id;
  using _position_tolerance_type =
    float;
  _position_tolerance_type position_tolerance;
  using _yaw_tolerance_type =
    float;
  _yaw_tolerance_type yaw_tolerance;
  using _approach_type_type =
    uint8_t;
  _approach_type_type approach_type;
  using _timeout_type =
    float;
  _timeout_type timeout;

  // setters for named parameter idiom
  Type & set__station_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->station_id = _arg;
    return *this;
  }
  Type & set__position_tolerance(
    const float & _arg)
  {
    this->position_tolerance = _arg;
    return *this;
  }
  Type & set__yaw_tolerance(
    const float & _arg)
  {
    this->yaw_tolerance = _arg;
    return *this;
  }
  Type & set__approach_type(
    const uint8_t & _arg)
  {
    this->approach_type = _arg;
    return *this;
  }
  Type & set__timeout(
    const float & _arg)
  {
    this->timeout = _arg;
    return *this;
  }

  // constant declarations
  static constexpr uint8_t APPROACH_PICKUP =
    0u;
  static constexpr uint8_t APPROACH_DROPOFF =
    1u;

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_Goal_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_Goal_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Goal_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Goal_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_Goal
    std::shared_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_Goal
    std::shared_ptr<marco_msgs::action::DockToStation_Goal_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_Goal_ & other) const
  {
    if (this->station_id != other.station_id) {
      return false;
    }
    if (this->position_tolerance != other.position_tolerance) {
      return false;
    }
    if (this->yaw_tolerance != other.yaw_tolerance) {
      return false;
    }
    if (this->approach_type != other.approach_type) {
      return false;
    }
    if (this->timeout != other.timeout) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_Goal_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_Goal_

// alias to use template instance with default allocator
using DockToStation_Goal =
  marco_msgs::action::DockToStation_Goal_<std::allocator<void>>;

// constant definitions
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Goal_<ContainerAllocator>::APPROACH_PICKUP;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Goal_<ContainerAllocator>::APPROACH_DROPOFF;
#endif  // __cplusplus < 201703L

}  // namespace action

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_Result __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_Result __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_Result_
{
  using Type = DockToStation_Result_<ContainerAllocator>;

  explicit DockToStation_Result_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->final_position_error = 0.0f;
      this->final_yaw_error = 0.0f;
      this->result_code = 0;
      this->message = "";
    }
  }

  explicit DockToStation_Result_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->final_position_error = 0.0f;
      this->final_yaw_error = 0.0f;
      this->result_code = 0;
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _final_position_error_type =
    float;
  _final_position_error_type final_position_error;
  using _final_yaw_error_type =
    float;
  _final_yaw_error_type final_yaw_error;
  using _result_code_type =
    uint8_t;
  _result_code_type result_code;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__final_position_error(
    const float & _arg)
  {
    this->final_position_error = _arg;
    return *this;
  }
  Type & set__final_yaw_error(
    const float & _arg)
  {
    this->final_yaw_error = _arg;
    return *this;
  }
  Type & set__result_code(
    const uint8_t & _arg)
  {
    this->result_code = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations
  static constexpr uint8_t RESULT_OK =
    0u;
  static constexpr uint8_t RESULT_QR_MISMATCH =
    1u;
  static constexpr uint8_t RESULT_LANE_LOST =
    2u;
  static constexpr uint8_t RESULT_TIMEOUT =
    3u;
  static constexpr uint8_t RESULT_OBSTACLE =
    4u;
  static constexpr uint8_t RESULT_ABORTED =
    5u;

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_Result_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_Result_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Result_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Result_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_Result
    std::shared_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_Result
    std::shared_ptr<marco_msgs::action::DockToStation_Result_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_Result_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->final_position_error != other.final_position_error) {
      return false;
    }
    if (this->final_yaw_error != other.final_yaw_error) {
      return false;
    }
    if (this->result_code != other.result_code) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_Result_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_Result_

// alias to use template instance with default allocator
using DockToStation_Result =
  marco_msgs::action::DockToStation_Result_<std::allocator<void>>;

// constant definitions
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_OK;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_QR_MISMATCH;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_LANE_LOST;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_TIMEOUT;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_OBSTACLE;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t DockToStation_Result_<ContainerAllocator>::RESULT_ABORTED;
#endif  // __cplusplus < 201703L

}  // namespace action

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_Feedback __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_Feedback __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_Feedback_
{
  using Type = DockToStation_Feedback_<ContainerAllocator>;

  explicit DockToStation_Feedback_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->phase = "";
      this->position_error = 0.0f;
      this->yaw_error = 0.0f;
      this->distance_remaining = 0.0f;
    }
  }

  explicit DockToStation_Feedback_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : phase(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->phase = "";
      this->position_error = 0.0f;
      this->yaw_error = 0.0f;
      this->distance_remaining = 0.0f;
    }
  }

  // field types and members
  using _phase_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _phase_type phase;
  using _position_error_type =
    float;
  _position_error_type position_error;
  using _yaw_error_type =
    float;
  _yaw_error_type yaw_error;
  using _distance_remaining_type =
    float;
  _distance_remaining_type distance_remaining;

  // setters for named parameter idiom
  Type & set__phase(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->phase = _arg;
    return *this;
  }
  Type & set__position_error(
    const float & _arg)
  {
    this->position_error = _arg;
    return *this;
  }
  Type & set__yaw_error(
    const float & _arg)
  {
    this->yaw_error = _arg;
    return *this;
  }
  Type & set__distance_remaining(
    const float & _arg)
  {
    this->distance_remaining = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_Feedback
    std::shared_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_Feedback
    std::shared_ptr<marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_Feedback_ & other) const
  {
    if (this->phase != other.phase) {
      return false;
    }
    if (this->position_error != other.position_error) {
      return false;
    }
    if (this->yaw_error != other.yaw_error) {
      return false;
    }
    if (this->distance_remaining != other.distance_remaining) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_Feedback_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_Feedback_

// alias to use template instance with default allocator
using DockToStation_Feedback =
  marco_msgs::action::DockToStation_Feedback_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs


// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"
// Member 'goal'
#include "marco_msgs/action/detail/dock_to_station__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_SendGoal_Request_
{
  using Type = DockToStation_SendGoal_Request_<ContainerAllocator>;

  explicit DockToStation_SendGoal_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init),
    goal(_init)
  {
    (void)_init;
  }

  explicit DockToStation_SendGoal_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init),
    goal(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;
  using _goal_type =
    marco_msgs::action::DockToStation_Goal_<ContainerAllocator>;
  _goal_type goal;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }
  Type & set__goal(
    const marco_msgs::action::DockToStation_Goal_<ContainerAllocator> & _arg)
  {
    this->goal = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Request
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Request
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_SendGoal_Request_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    if (this->goal != other.goal) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_SendGoal_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_SendGoal_Request_

// alias to use template instance with default allocator
using DockToStation_SendGoal_Request =
  marco_msgs::action::DockToStation_SendGoal_Request_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs


// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_SendGoal_Response_
{
  using Type = DockToStation_SendGoal_Response_<ContainerAllocator>;

  explicit DockToStation_SendGoal_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
    }
  }

  explicit DockToStation_SendGoal_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
    }
  }

  // field types and members
  using _accepted_type =
    bool;
  _accepted_type accepted;
  using _stamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _stamp_type stamp;

  // setters for named parameter idiom
  Type & set__accepted(
    const bool & _arg)
  {
    this->accepted = _arg;
    return *this;
  }
  Type & set__stamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->stamp = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Response
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_SendGoal_Response
    std::shared_ptr<marco_msgs::action::DockToStation_SendGoal_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_SendGoal_Response_ & other) const
  {
    if (this->accepted != other.accepted) {
      return false;
    }
    if (this->stamp != other.stamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_SendGoal_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_SendGoal_Response_

// alias to use template instance with default allocator
using DockToStation_SendGoal_Response =
  marco_msgs::action::DockToStation_SendGoal_Response_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs

namespace marco_msgs
{

namespace action
{

struct DockToStation_SendGoal
{
  using Request = marco_msgs::action::DockToStation_SendGoal_Request;
  using Response = marco_msgs::action::DockToStation_SendGoal_Response;
};

}  // namespace action

}  // namespace marco_msgs


// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_GetResult_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_GetResult_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_GetResult_Request_
{
  using Type = DockToStation_GetResult_Request_<ContainerAllocator>;

  explicit DockToStation_GetResult_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init)
  {
    (void)_init;
  }

  explicit DockToStation_GetResult_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_GetResult_Request
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_GetResult_Request
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_GetResult_Request_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_GetResult_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_GetResult_Request_

// alias to use template instance with default allocator
using DockToStation_GetResult_Request =
  marco_msgs::action::DockToStation_GetResult_Request_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs


// Include directives for member types
// Member 'result'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_GetResult_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_GetResult_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_GetResult_Response_
{
  using Type = DockToStation_GetResult_Response_<ContainerAllocator>;

  explicit DockToStation_GetResult_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : result(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0;
    }
  }

  explicit DockToStation_GetResult_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : result(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0;
    }
  }

  // field types and members
  using _status_type =
    int8_t;
  _status_type status;
  using _result_type =
    marco_msgs::action::DockToStation_Result_<ContainerAllocator>;
  _result_type result;

  // setters for named parameter idiom
  Type & set__status(
    const int8_t & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__result(
    const marco_msgs::action::DockToStation_Result_<ContainerAllocator> & _arg)
  {
    this->result = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_GetResult_Response
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_GetResult_Response
    std::shared_ptr<marco_msgs::action::DockToStation_GetResult_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_GetResult_Response_ & other) const
  {
    if (this->status != other.status) {
      return false;
    }
    if (this->result != other.result) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_GetResult_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_GetResult_Response_

// alias to use template instance with default allocator
using DockToStation_GetResult_Response =
  marco_msgs::action::DockToStation_GetResult_Response_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs

namespace marco_msgs
{

namespace action
{

struct DockToStation_GetResult
{
  using Request = marco_msgs::action::DockToStation_GetResult_Request;
  using Response = marco_msgs::action::DockToStation_GetResult_Response;
};

}  // namespace action

}  // namespace marco_msgs


// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"
// Member 'feedback'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__marco_msgs__action__DockToStation_FeedbackMessage __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__action__DockToStation_FeedbackMessage __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct DockToStation_FeedbackMessage_
{
  using Type = DockToStation_FeedbackMessage_<ContainerAllocator>;

  explicit DockToStation_FeedbackMessage_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init),
    feedback(_init)
  {
    (void)_init;
  }

  explicit DockToStation_FeedbackMessage_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init),
    feedback(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;
  using _feedback_type =
    marco_msgs::action::DockToStation_Feedback_<ContainerAllocator>;
  _feedback_type feedback;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }
  Type & set__feedback(
    const marco_msgs::action::DockToStation_Feedback_<ContainerAllocator> & _arg)
  {
    this->feedback = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__action__DockToStation_FeedbackMessage
    std::shared_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__action__DockToStation_FeedbackMessage
    std::shared_ptr<marco_msgs::action::DockToStation_FeedbackMessage_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DockToStation_FeedbackMessage_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    if (this->feedback != other.feedback) {
      return false;
    }
    return true;
  }
  bool operator!=(const DockToStation_FeedbackMessage_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DockToStation_FeedbackMessage_

// alias to use template instance with default allocator
using DockToStation_FeedbackMessage =
  marco_msgs::action::DockToStation_FeedbackMessage_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace marco_msgs

#include "action_msgs/srv/cancel_goal.hpp"
#include "action_msgs/msg/goal_info.hpp"
#include "action_msgs/msg/goal_status_array.hpp"

namespace marco_msgs
{

namespace action
{

struct DockToStation
{
  /// The goal message defined in the action definition.
  using Goal = marco_msgs::action::DockToStation_Goal;
  /// The result message defined in the action definition.
  using Result = marco_msgs::action::DockToStation_Result;
  /// The feedback message defined in the action definition.
  using Feedback = marco_msgs::action::DockToStation_Feedback;

  struct Impl
  {
    /// The send_goal service using a wrapped version of the goal message as a request.
    using SendGoalService = marco_msgs::action::DockToStation_SendGoal;
    /// The get_result service using a wrapped version of the result message as a response.
    using GetResultService = marco_msgs::action::DockToStation_GetResult;
    /// The feedback message with generic fields which wraps the feedback message.
    using FeedbackMessage = marco_msgs::action::DockToStation_FeedbackMessage;

    /// The generic service to cancel a goal.
    using CancelGoalService = action_msgs::srv::CancelGoal;
    /// The generic message for the status of a goal.
    using GoalStatusMessage = action_msgs::msg::GoalStatusArray;
  };
};

typedef struct DockToStation DockToStation;

}  // namespace action

}  // namespace marco_msgs

#endif  // MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_HPP_
