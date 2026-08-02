// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:srv/TaskComplete.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__STRUCT_HPP_
#define MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__TaskComplete_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__TaskComplete_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct TaskComplete_Request_
{
  using Type = TaskComplete_Request_<ContainerAllocator>;

  explicit TaskComplete_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
      this->success = false;
      this->message = "";
    }
  }

  explicit TaskComplete_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : task_id(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
      this->success = false;
      this->message = "";
    }
  }

  // field types and members
  using _task_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_id_type task_id;
  using _success_type =
    bool;
  _success_type success;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__task_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_id = _arg;
    return *this;
  }
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
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
    marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__TaskComplete_Request
    std::shared_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__TaskComplete_Request
    std::shared_ptr<marco_msgs::srv::TaskComplete_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TaskComplete_Request_ & other) const
  {
    if (this->task_id != other.task_id) {
      return false;
    }
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const TaskComplete_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TaskComplete_Request_

// alias to use template instance with default allocator
using TaskComplete_Request =
  marco_msgs::srv::TaskComplete_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__TaskComplete_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__TaskComplete_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct TaskComplete_Response_
{
  using Type = TaskComplete_Response_<ContainerAllocator>;

  explicit TaskComplete_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->acknowledged = false;
    }
  }

  explicit TaskComplete_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->acknowledged = false;
    }
  }

  // field types and members
  using _acknowledged_type =
    bool;
  _acknowledged_type acknowledged;

  // setters for named parameter idiom
  Type & set__acknowledged(
    const bool & _arg)
  {
    this->acknowledged = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__TaskComplete_Response
    std::shared_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__TaskComplete_Response
    std::shared_ptr<marco_msgs::srv::TaskComplete_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TaskComplete_Response_ & other) const
  {
    if (this->acknowledged != other.acknowledged) {
      return false;
    }
    return true;
  }
  bool operator!=(const TaskComplete_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TaskComplete_Response_

// alias to use template instance with default allocator
using TaskComplete_Response =
  marco_msgs::srv::TaskComplete_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs

namespace marco_msgs
{

namespace srv
{

struct TaskComplete
{
  using Request = marco_msgs::srv::TaskComplete_Request;
  using Response = marco_msgs::srv::TaskComplete_Response;
};

}  // namespace srv

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__TASK_COMPLETE__STRUCT_HPP_
