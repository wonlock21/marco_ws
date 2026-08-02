// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from marco_msgs:srv/StartMission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_HPP_
#define MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__StartMission_Request __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__StartMission_Request __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartMission_Request_
{
  using Type = StartMission_Request_<ContainerAllocator>;

  explicit StartMission_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit StartMission_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    marco_msgs::srv::StartMission_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::StartMission_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::StartMission_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::StartMission_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__StartMission_Request
    std::shared_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__StartMission_Request
    std::shared_ptr<marco_msgs::srv::StartMission_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartMission_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartMission_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartMission_Request_

// alias to use template instance with default allocator
using StartMission_Request =
  marco_msgs::srv::StartMission_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs


#ifndef _WIN32
# define DEPRECATED__marco_msgs__srv__StartMission_Response __attribute__((deprecated))
#else
# define DEPRECATED__marco_msgs__srv__StartMission_Response __declspec(deprecated)
#endif

namespace marco_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartMission_Response_
{
  using Type = StartMission_Response_<ContainerAllocator>;

  explicit StartMission_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
      this->message = "";
    }
  }

  explicit StartMission_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
      this->message = "";
    }
  }

  // field types and members
  using _accepted_type =
    bool;
  _accepted_type accepted;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__accepted(
    const bool & _arg)
  {
    this->accepted = _arg;
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
    marco_msgs::srv::StartMission_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const marco_msgs::srv::StartMission_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::StartMission_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      marco_msgs::srv::StartMission_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__marco_msgs__srv__StartMission_Response
    std::shared_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__marco_msgs__srv__StartMission_Response
    std::shared_ptr<marco_msgs::srv::StartMission_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartMission_Response_ & other) const
  {
    if (this->accepted != other.accepted) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartMission_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartMission_Response_

// alias to use template instance with default allocator
using StartMission_Response =
  marco_msgs::srv::StartMission_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace marco_msgs

namespace marco_msgs
{

namespace srv
{

struct StartMission
{
  using Request = marco_msgs::srv::StartMission_Request;
  using Response = marco_msgs::srv::StartMission_Response;
};

}  // namespace srv

}  // namespace marco_msgs

#endif  // MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_HPP_
