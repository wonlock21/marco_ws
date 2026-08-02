// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_H_
#define MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'APPROACH_PICKUP'.
/**
  * Yuk alma mi birakma mi. Catalin hangi tarafta kalacagini ve hangi kameranin
  * kullanilacagini belirler.
 */
enum
{
  marco_msgs__action__DockToStation_Goal__APPROACH_PICKUP = 0
};

/// Constant 'APPROACH_DROPOFF'.
enum
{
  marco_msgs__action__DockToStation_Goal__APPROACH_DROPOFF = 1
};

// Include directives for member types
// Member 'station_id'
#include "rosidl_runtime_c/string.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_Goal
{
  /// --- Hedef ---
  /// Yanasilacak istasyonun kimligi. QR icerigiyle dogrulanir.
  rosidl_runtime_c__String station_id;
  /// Sartname madde 8 varsayilanlari: +/- 7.5 cm konum, +/- 5 derece yon.
  /// [m]
  float position_tolerance;
  float yaw_tolerance;
  uint8_t approach_type;
  /// Zaman asimi. Asilirsa action iptal edilir ve gorev yonetimine hata bildirilir.
  float timeout;
} marco_msgs__action__DockToStation_Goal;

// Struct for a sequence of marco_msgs__action__DockToStation_Goal.
typedef struct marco_msgs__action__DockToStation_Goal__Sequence
{
  marco_msgs__action__DockToStation_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_Goal__Sequence;


// Constants defined in the message

/// Constant 'RESULT_OK'.
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_OK = 0
};

/// Constant 'RESULT_QR_MISMATCH'.
/**
  * okunan QR hedefle uyusmadi
 */
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_QR_MISMATCH = 1
};

/// Constant 'RESULT_LANE_LOST'.
/**
  * serit kaybedildi
 */
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_LANE_LOST = 2
};

/// Constant 'RESULT_TIMEOUT'.
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_TIMEOUT = 3
};

/// Constant 'RESULT_OBSTACLE'.
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_OBSTACLE = 4
};

/// Constant 'RESULT_ABORTED'.
enum
{
  marco_msgs__action__DockToStation_Result__RESULT_ABORTED = 5
};

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_Result
{
  bool success;
  /// Duruldugu andaki olculen hata. Kalibrasyon ve saha analizi icin kaydedilir.
  /// [m]
  float final_position_error;
  float final_yaw_error;
  uint8_t result_code;
  rosidl_runtime_c__String message;
} marco_msgs__action__DockToStation_Result;

// Struct for a sequence of marco_msgs__action__DockToStation_Result.
typedef struct marco_msgs__action__DockToStation_Result__Sequence
{
  marco_msgs__action__DockToStation_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_Result__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'phase'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_Feedback
{
  rosidl_runtime_c__String phase;
  float position_error;
  float yaw_error;
  float distance_remaining;
} marco_msgs__action__DockToStation_Feedback;

// Struct for a sequence of marco_msgs__action__DockToStation_Feedback.
typedef struct marco_msgs__action__DockToStation_Feedback__Sequence
{
  marco_msgs__action__DockToStation_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_Feedback__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "marco_msgs/action/detail/dock_to_station__struct.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  marco_msgs__action__DockToStation_Goal goal;
} marco_msgs__action__DockToStation_SendGoal_Request;

// Struct for a sequence of marco_msgs__action__DockToStation_SendGoal_Request.
typedef struct marco_msgs__action__DockToStation_SendGoal_Request__Sequence
{
  marco_msgs__action__DockToStation_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_SendGoal_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} marco_msgs__action__DockToStation_SendGoal_Response;

// Struct for a sequence of marco_msgs__action__DockToStation_SendGoal_Response.
typedef struct marco_msgs__action__DockToStation_SendGoal_Response__Sequence
{
  marco_msgs__action__DockToStation_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_SendGoal_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} marco_msgs__action__DockToStation_GetResult_Request;

// Struct for a sequence of marco_msgs__action__DockToStation_GetResult_Request.
typedef struct marco_msgs__action__DockToStation_GetResult_Request__Sequence
{
  marco_msgs__action__DockToStation_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_GetResult_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_GetResult_Response
{
  int8_t status;
  marco_msgs__action__DockToStation_Result result;
} marco_msgs__action__DockToStation_GetResult_Response;

// Struct for a sequence of marco_msgs__action__DockToStation_GetResult_Response.
typedef struct marco_msgs__action__DockToStation_GetResult_Response__Sequence
{
  marco_msgs__action__DockToStation_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_GetResult_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "marco_msgs/action/detail/dock_to_station__struct.h"

/// Struct defined in action/DockToStation in the package marco_msgs.
typedef struct marco_msgs__action__DockToStation_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  marco_msgs__action__DockToStation_Feedback feedback;
} marco_msgs__action__DockToStation_FeedbackMessage;

// Struct for a sequence of marco_msgs__action__DockToStation_FeedbackMessage.
typedef struct marco_msgs__action__DockToStation_FeedbackMessage__Sequence
{
  marco_msgs__action__DockToStation_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__action__DockToStation_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__STRUCT_H_
