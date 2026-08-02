// generated from rosidl_typesupport_cpp/resource/idl__type_support.cpp.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "marco_msgs/action/detail/dock_to_station__struct.hpp"
#include "rosidl_typesupport_cpp/identifier.hpp"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
#include "rosidl_typesupport_cpp/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_Goal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_Goal_type_support_ids_t;

static const _DockToStation_Goal_type_support_ids_t _DockToStation_Goal_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_Goal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_Goal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_Goal_type_support_symbol_names_t _DockToStation_Goal_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_Goal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_Goal)),
  }
};

typedef struct _DockToStation_Goal_type_support_data_t
{
  void * data[2];
} _DockToStation_Goal_type_support_data_t;

static _DockToStation_Goal_type_support_data_t _DockToStation_Goal_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_Goal_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_Goal_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_Goal_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_Goal_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_Goal_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_Goal_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_Goal>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_Goal_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_Goal)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_Goal>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_Result_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_Result_type_support_ids_t;

static const _DockToStation_Result_type_support_ids_t _DockToStation_Result_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_Result_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_Result_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_Result_type_support_symbol_names_t _DockToStation_Result_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_Result)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_Result)),
  }
};

typedef struct _DockToStation_Result_type_support_data_t
{
  void * data[2];
} _DockToStation_Result_type_support_data_t;

static _DockToStation_Result_type_support_data_t _DockToStation_Result_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_Result_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_Result_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_Result_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_Result_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_Result_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_Result_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_Result>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_Result_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_Result)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_Result>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_Feedback_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_Feedback_type_support_ids_t;

static const _DockToStation_Feedback_type_support_ids_t _DockToStation_Feedback_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_Feedback_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_Feedback_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_Feedback_type_support_symbol_names_t _DockToStation_Feedback_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_Feedback)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_Feedback)),
  }
};

typedef struct _DockToStation_Feedback_type_support_data_t
{
  void * data[2];
} _DockToStation_Feedback_type_support_data_t;

static _DockToStation_Feedback_type_support_data_t _DockToStation_Feedback_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_Feedback_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_Feedback_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_Feedback_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_Feedback_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_Feedback_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_Feedback_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_Feedback>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_Feedback_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_Feedback)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_Feedback>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_SendGoal_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_SendGoal_Request_type_support_ids_t;

static const _DockToStation_SendGoal_Request_type_support_ids_t _DockToStation_SendGoal_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_SendGoal_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_SendGoal_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_SendGoal_Request_type_support_symbol_names_t _DockToStation_SendGoal_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_SendGoal_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_SendGoal_Request)),
  }
};

typedef struct _DockToStation_SendGoal_Request_type_support_data_t
{
  void * data[2];
} _DockToStation_SendGoal_Request_type_support_data_t;

static _DockToStation_SendGoal_Request_type_support_data_t _DockToStation_SendGoal_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_SendGoal_Request_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_SendGoal_Request_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_SendGoal_Request_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_SendGoal_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_SendGoal_Request_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_SendGoal_Request_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_SendGoal_Request>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_SendGoal_Request_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_SendGoal_Request)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_SendGoal_Request>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_SendGoal_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_SendGoal_Response_type_support_ids_t;

static const _DockToStation_SendGoal_Response_type_support_ids_t _DockToStation_SendGoal_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_SendGoal_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_SendGoal_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_SendGoal_Response_type_support_symbol_names_t _DockToStation_SendGoal_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_SendGoal_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_SendGoal_Response)),
  }
};

typedef struct _DockToStation_SendGoal_Response_type_support_data_t
{
  void * data[2];
} _DockToStation_SendGoal_Response_type_support_data_t;

static _DockToStation_SendGoal_Response_type_support_data_t _DockToStation_SendGoal_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_SendGoal_Response_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_SendGoal_Response_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_SendGoal_Response_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_SendGoal_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_SendGoal_Response_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_SendGoal_Response_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_SendGoal_Response>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_SendGoal_Response_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_SendGoal_Response)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_SendGoal_Response>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/service_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_SendGoal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_SendGoal_type_support_ids_t;

static const _DockToStation_SendGoal_type_support_ids_t _DockToStation_SendGoal_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_SendGoal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_SendGoal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_SendGoal_type_support_symbol_names_t _DockToStation_SendGoal_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_SendGoal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_SendGoal)),
  }
};

typedef struct _DockToStation_SendGoal_type_support_data_t
{
  void * data[2];
} _DockToStation_SendGoal_type_support_data_t;

static _DockToStation_SendGoal_type_support_data_t _DockToStation_SendGoal_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_SendGoal_service_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_SendGoal_service_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_SendGoal_service_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_SendGoal_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t DockToStation_SendGoal_service_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_SendGoal_service_typesupport_map),
  ::rosidl_typesupport_cpp::get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<marco_msgs::action::DockToStation_SendGoal>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_SendGoal_service_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_SendGoal)() {
  return ::rosidl_typesupport_cpp::get_service_type_support_handle<marco_msgs::action::DockToStation_SendGoal>();
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_GetResult_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_GetResult_Request_type_support_ids_t;

static const _DockToStation_GetResult_Request_type_support_ids_t _DockToStation_GetResult_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_GetResult_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_GetResult_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_GetResult_Request_type_support_symbol_names_t _DockToStation_GetResult_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_GetResult_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_GetResult_Request)),
  }
};

typedef struct _DockToStation_GetResult_Request_type_support_data_t
{
  void * data[2];
} _DockToStation_GetResult_Request_type_support_data_t;

static _DockToStation_GetResult_Request_type_support_data_t _DockToStation_GetResult_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_GetResult_Request_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_GetResult_Request_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_GetResult_Request_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_GetResult_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_GetResult_Request_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_GetResult_Request_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_GetResult_Request>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_GetResult_Request_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_GetResult_Request)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_GetResult_Request>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_GetResult_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_GetResult_Response_type_support_ids_t;

static const _DockToStation_GetResult_Response_type_support_ids_t _DockToStation_GetResult_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_GetResult_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_GetResult_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_GetResult_Response_type_support_symbol_names_t _DockToStation_GetResult_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_GetResult_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_GetResult_Response)),
  }
};

typedef struct _DockToStation_GetResult_Response_type_support_data_t
{
  void * data[2];
} _DockToStation_GetResult_Response_type_support_data_t;

static _DockToStation_GetResult_Response_type_support_data_t _DockToStation_GetResult_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_GetResult_Response_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_GetResult_Response_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_GetResult_Response_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_GetResult_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_GetResult_Response_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_GetResult_Response_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_GetResult_Response>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_GetResult_Response_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_GetResult_Response)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_GetResult_Response>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_GetResult_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_GetResult_type_support_ids_t;

static const _DockToStation_GetResult_type_support_ids_t _DockToStation_GetResult_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_GetResult_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_GetResult_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_GetResult_type_support_symbol_names_t _DockToStation_GetResult_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_GetResult)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_GetResult)),
  }
};

typedef struct _DockToStation_GetResult_type_support_data_t
{
  void * data[2];
} _DockToStation_GetResult_type_support_data_t;

static _DockToStation_GetResult_type_support_data_t _DockToStation_GetResult_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_GetResult_service_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_GetResult_service_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_GetResult_service_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_GetResult_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t DockToStation_GetResult_service_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_GetResult_service_typesupport_map),
  ::rosidl_typesupport_cpp::get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<marco_msgs::action::DockToStation_GetResult>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_GetResult_service_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_GetResult)() {
  return ::rosidl_typesupport_cpp::get_service_type_support_handle<marco_msgs::action::DockToStation_GetResult>();
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _DockToStation_FeedbackMessage_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _DockToStation_FeedbackMessage_type_support_ids_t;

static const _DockToStation_FeedbackMessage_type_support_ids_t _DockToStation_FeedbackMessage_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _DockToStation_FeedbackMessage_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _DockToStation_FeedbackMessage_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _DockToStation_FeedbackMessage_type_support_symbol_names_t _DockToStation_FeedbackMessage_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, marco_msgs, action, DockToStation_FeedbackMessage)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, marco_msgs, action, DockToStation_FeedbackMessage)),
  }
};

typedef struct _DockToStation_FeedbackMessage_type_support_data_t
{
  void * data[2];
} _DockToStation_FeedbackMessage_type_support_data_t;

static _DockToStation_FeedbackMessage_type_support_data_t _DockToStation_FeedbackMessage_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _DockToStation_FeedbackMessage_message_typesupport_map = {
  2,
  "marco_msgs",
  &_DockToStation_FeedbackMessage_message_typesupport_ids.typesupport_identifier[0],
  &_DockToStation_FeedbackMessage_message_typesupport_symbol_names.symbol_name[0],
  &_DockToStation_FeedbackMessage_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t DockToStation_FeedbackMessage_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_DockToStation_FeedbackMessage_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<marco_msgs::action::DockToStation_FeedbackMessage>()
{
  return &::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_FeedbackMessage_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation_FeedbackMessage)() {
  return get_message_type_support_handle<marco_msgs::action::DockToStation_FeedbackMessage>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

#include "action_msgs/msg/goal_status_array.hpp"
#include "action_msgs/srv/cancel_goal.hpp"
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
#include "rosidl_runtime_c/action_type_support_struct.h"
#include "rosidl_typesupport_cpp/action_type_support.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support.hpp"

namespace marco_msgs
{

namespace action
{

namespace rosidl_typesupport_cpp
{

static rosidl_action_type_support_t DockToStation_action_type_support_handle = {
  NULL, NULL, NULL, NULL, NULL};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace marco_msgs

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_action_type_support_t *
get_action_type_support_handle<marco_msgs::action::DockToStation>()
{
  using ::marco_msgs::action::rosidl_typesupport_cpp::DockToStation_action_type_support_handle;
  // Thread-safe by always writing the same values to the static struct
  DockToStation_action_type_support_handle.goal_service_type_support = get_service_type_support_handle<::marco_msgs::action::DockToStation::Impl::SendGoalService>();
  DockToStation_action_type_support_handle.result_service_type_support = get_service_type_support_handle<::marco_msgs::action::DockToStation::Impl::GetResultService>();
  DockToStation_action_type_support_handle.cancel_service_type_support = get_service_type_support_handle<::marco_msgs::action::DockToStation::Impl::CancelGoalService>();
  DockToStation_action_type_support_handle.feedback_message_type_support = get_message_type_support_handle<::marco_msgs::action::DockToStation::Impl::FeedbackMessage>();
  DockToStation_action_type_support_handle.status_message_type_support = get_message_type_support_handle<::marco_msgs::action::DockToStation::Impl::GoalStatusMessage>();
  return &DockToStation_action_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_action_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__ACTION_SYMBOL_NAME(rosidl_typesupport_cpp, marco_msgs, action, DockToStation)() {
  return ::rosidl_typesupport_cpp::get_action_type_support_handle<marco_msgs::action::DockToStation>();
}

#ifdef __cplusplus
}
#endif
