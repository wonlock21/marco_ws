// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:srv/AssignTask.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__STRUCT_HPP_
#define MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__AssignTask_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__AssignTask_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AssignTask_Request_
{
  using Type = AssignTask_Request_<ContainerAllocator>;

  explicit AssignTask_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit AssignTask_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::srv::AssignTask_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::AssignTask_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::AssignTask_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::AssignTask_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__AssignTask_Request
    std::shared_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__AssignTask_Request
    std::shared_ptr<marco_msgs::srv::AssignTask_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AssignTask_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const AssignTask_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AssignTask_Request_

// alias to use template instance with default allocator
using AssignTask_Request =
  marco_msgs::srv::AssignTask_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__AssignTask_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__AssignTask_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AssignTask_Response_
{
  using Type = AssignTask_Response_<ContainerAllocator>;

  explicit AssignTask_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->task_id = "";
      this->pickup_node = "";
      this->dropoff_node = "";
      this->message = "";
    }
  }

  explicit AssignTask_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : task_id(_alloc),
    pickup_node(_alloc),
    dropoff_node(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->task_id = "";
      this->pickup_node = "";
      this->dropoff_node = "";
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _task_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_id_type task_id;
  using _pickup_node_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _pickup_node_type pickup_node;
  using _dropoff_node_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _dropoff_node_type dropoff_node;
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
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    marco_msgs::srv::AssignTask_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::AssignTask_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::AssignTask_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::AssignTask_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__AssignTask_Response
    std::shared_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__AssignTask_Response
    std::shared_ptr<marco_msgs::srv::AssignTask_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AssignTask_Response_ & other) const
  {
    if (this->success != other.success) {
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
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const AssignTask_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AssignTask_Response_

// alias to use template instance with default allocator
using AssignTask_Response =
  marco_msgs::srv::AssignTask_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs

namespace marco_msgs
{

namespace srv
{

struct AssignTask
{
  using Request = marco_msgs::srv::AssignTask_Request;
  using Response = marco_msgs::srv::AssignTask_Response;
};

}  // namespace srv

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__ASSIGN_TASK__STRUCT_HPP_
