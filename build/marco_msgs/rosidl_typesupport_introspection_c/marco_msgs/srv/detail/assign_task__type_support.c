// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from marco_msgs:srv/AssignTask.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "marco_msgs/srv/detail/assign_task__rosidl_typesupport_introspection_c.h"
#include "marco_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "marco_msgs/srv/detail/assign_task__functions.h"
#include "marco_msgs/srv/detail/assign_task__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  marco_msgs__srv__AssignTask_Request__init(message_memory);
}

void marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_fini_function(void * message_memory)
{
  marco_msgs__srv__AssignTask_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_member_array[1] = {
  {
    "structure_needs_at_least_one_member",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Request, structure_needs_at_least_one_member),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_members = {
  "marco_msgs__srv",  // message namespace
  "AssignTask_Request",  // message name
  1,  // number of fields
  sizeof(marco_msgs__srv__AssignTask_Request),
  marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_member_array,  // message members
  marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_type_support_handle = {
  0,
  &marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_marco_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Request)() {
  if (!marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_type_support_handle.typesupport_identifier) {
    marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &marco_msgs__srv__AssignTask_Request__rosidl_typesupport_introspection_c__AssignTask_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "marco_msgs/srv/detail/assign_task__rosidl_typesupport_introspection_c.h"
// already included above
// #include "marco_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "marco_msgs/srv/detail/assign_task__functions.h"
// already included above
// #include "marco_msgs/srv/detail/assign_task__struct.h"


// Include directives for member types
// Member `task_id`
// Member `pickup_node`
// Member `dropoff_node`
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  marco_msgs__srv__AssignTask_Response__init(message_memory);
}

void marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_fini_function(void * message_memory)
{
  marco_msgs__srv__AssignTask_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_member_array[5] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "task_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Response, task_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pickup_node",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Response, pickup_node),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "dropoff_node",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Response, dropoff_node),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(marco_msgs__srv__AssignTask_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_members = {
  "marco_msgs__srv",  // message namespace
  "AssignTask_Response",  // message name
  5,  // number of fields
  sizeof(marco_msgs__srv__AssignTask_Response),
  marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_member_array,  // message members
  marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_type_support_handle = {
  0,
  &marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_marco_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Response)() {
  if (!marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_type_support_handle.typesupport_identifier) {
    marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &marco_msgs__srv__AssignTask_Response__rosidl_typesupport_introspection_c__AssignTask_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "marco_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "marco_msgs/srv/detail/assign_task__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_members = {
  "marco_msgs__srv",  // service namespace
  "AssignTask",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_Request_message_type_support_handle,
  NULL  // response message
  // marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_Response_message_type_support_handle
};

static rosidl_service_type_support_t marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_type_support_handle = {
  0,
  &marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_marco_msgs
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask)() {
  if (!marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_type_support_handle.typesupport_identifier) {
    marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, marco_msgs, srv, AssignTask_Response)()->data;
  }

  return &marco_msgs__srv__detail__assign_task__rosidl_typesupport_introspection_c__AssignTask_service_type_support_handle;
}
