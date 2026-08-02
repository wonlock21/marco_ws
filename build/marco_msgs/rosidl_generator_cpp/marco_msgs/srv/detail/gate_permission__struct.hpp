// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:srv/GatePermission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__STRUCT_HPP_
#define MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__GatePermission_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__GatePermission_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GatePermission_Request_
{
  using Type = GatePermission_Request_<ContainerAllocator>;

  explicit GatePermission_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->node_id = "";
    }
  }

  explicit GatePermission_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : node_id(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->node_id = "";
    }
  }

  // field types and members
  using _node_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _node_id_type node_id;

  // setters for named parameter idiom
  Type & set__node_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->node_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::srv::GatePermission_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::GatePermission_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::GatePermission_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::GatePermission_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__GatePermission_Request
    std::shared_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__GatePermission_Request
    std::shared_ptr<marco_msgs::srv::GatePermission_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GatePermission_Request_ & other) const
  {
    if (this->node_id != other.node_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const GatePermission_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GatePermission_Request_

// alias to use template instance with default allocator
using GatePermission_Request =
  marco_msgs::srv::GatePermission_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__GatePermission_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__GatePermission_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GatePermission_Response_
{
  using Type = GatePermission_Response_<ContainerAllocator>;

  explicit GatePermission_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->granted = false;
      this->message = "";
    }
  }

  explicit GatePermission_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->granted = false;
      this->message = "";
    }
  }

  // field types and members
  using _granted_type =
    bool;
  _granted_type granted;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__granted(
    const bool & _arg)
  {
    this->granted = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::srv::GatePermission_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::GatePermission_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::GatePermission_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::GatePermission_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__GatePermission_Response
    std::shared_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__GatePermission_Response
    std::shared_ptr<marco_msgs::srv::GatePermission_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GatePermission_Response_ & other) const
  {
    if (this->granted != other.granted) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const GatePermission_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GatePermission_Response_

// alias to use template instance with default allocator
using GatePermission_Response =
  marco_msgs::srv::GatePermission_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs

namespace marco_msgs
{

namespace srv
{

struct GatePermission
{
  using Request = marco_msgs::srv::GatePermission_Request;
  using Response = marco_msgs::srv::GatePermission_Response;
};

}  // namespace srv

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__GATE_PERMISSION__STRUCT_HPP_
