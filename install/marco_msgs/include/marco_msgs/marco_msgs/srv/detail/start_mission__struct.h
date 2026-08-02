// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from marco_msgs:srv/StartMission.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_H_
#define MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/StartMission in the package marco_msgs.
typedef struct marco_msgs__srv__StartMission_Request
{
  uint8_t structure_needs_at_least_one_member;
} marco_msgs__srv__StartMission_Request;

// Struct for a sequence of marco_msgs__srv__StartMission_Request.
typedef struct marco_msgs__srv__StartMission_Request__Sequence
{
  marco_msgs__srv__StartMission_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__srv__StartMission_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/StartMission in the package marco_msgs.
typedef struct marco_msgs__srv__StartMission_Response
{
  bool accepted;
  rosidl_runtime_c__String message;
} marco_msgs__srv__StartMission_Response;

// Struct for a sequence of marco_msgs__srv__StartMission_Response.
typedef struct marco_msgs__srv__StartMission_Response__Sequence
{
  marco_msgs__srv__StartMission_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__srv__StartMission_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__SRV__DETAIL__START_MISSION__STRUCT_H_
