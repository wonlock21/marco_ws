// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:msg/LaneOffset.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_HPP_
#define MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_HPP_

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

#ifndef _WIN32
# define DEPRECATED__marco_msgs__msg__LaneOffset __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__msg__LaneOffset __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct LaneOffset_
{
  using Type = LaneOffset_<ContainerAllocator>;

  explicit LaneOffset_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->detected = false;
      this->lateral_offset = 0.0f;
      this->heading_error = 0.0f;
      this->confidence = 0.0f;
      this->camera_frame = "";
    }
  }

  explicit LaneOffset_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    camera_frame(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->detected = false;
      this->lateral_offset = 0.0f;
      this->heading_error = 0.0f;
      this->confidence = 0.0f;
      this->camera_frame = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _detected_type =
    bool;
  _detected_type detected;
  using _lateral_offset_type =
    float;
  _lateral_offset_type lateral_offset;
  using _heading_error_type =
    float;
  _heading_error_type heading_error;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _camera_frame_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _camera_frame_type camera_frame;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__detected(
    const bool & _arg)
  {
    this->detected = _arg;
    return *this;
  }
  Type & set__lateral_offset(
    const float & _arg)
  {
    this->lateral_offset = _arg;
    return *this;
  }
  Type & set__heading_error(
    const float & _arg)
  {
    this->heading_error = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__camera_frame(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->camera_frame = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::msg::LaneOffset_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::msg::LaneOffset_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::msg::LaneOffset_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::msg::LaneOffset_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__msg__LaneOffset
    std::shared_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__msg__LaneOffset
    std::shared_ptr<marco_msgs::msg::LaneOffset_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const LaneOffset_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->detected != other.detected) {
      return false;
    }
    if (this->lateral_offset != other.lateral_offset) {
      return false;
    }
    if (this->heading_error != other.heading_error) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->camera_frame != other.camera_frame) {
      return false;
    }
    return true;
  }
  bool operator!=(const LaneOffset_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct LaneOffset_

// alias to use template instance with default allocator
using LaneOffset =
  marco_msgs::msg::LaneOffset_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace marco_msgs

#endif  // MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_HPP_
