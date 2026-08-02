// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from marco_msgs:msg/RobotStatus.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_H_
#define MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'STATE_IDLE'.
/**
  * --- Gorev durumu (sartname madde 10 a-h) ---
  * goreve hazir bekleme
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_IDLE = 0
};

/// Constant 'STATE_TASK_RECEIVED'.
/**
  * gorev alindi, isleniyor
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_TASK_RECEIVED = 1
};

/// Constant 'STATE_MOVING_UNLOADED'.
/**
  * gorev alindi, yuksuz hareket
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_MOVING_UNLOADED = 2
};

/// Constant 'STATE_MOVING_LOADED'.
/**
  * gorev alindi, yuklu hareket
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_MOVING_LOADED = 3
};

/// Constant 'STATE_WAITING_PLC'.
/**
  * fabrika otomasyon sistemi komut bekleniyor
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_WAITING_PLC = 4
};

/// Constant 'STATE_RETURNING'.
/**
  * gorev tamamlandi, baslangic noktasina hareket
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_RETURNING = 5
};

/// Constant 'STATE_ERROR'.
/**
  * hata durumu
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_ERROR = 6
};

/// Constant 'STATE_ESTOP'.
/**
  * acil stop
 */
enum
{
  marco_msgs__msg__RobotStatus__STATE_ESTOP = 7
};

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'pose'
#include "geometry_msgs/msg/detail/pose_with_covariance_stamped__struct.h"
// Member 'current_route_edge'
// Member 'next_node'
// Member 'task_id'
// Member 'pickup_node'
// Member 'dropoff_node'
// Member 'last_qr_data'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/RobotStatus in the package marco_msgs.
/**
  * Robotun butunlesik durumu. Tuketici: Flutter GUI (PC ve mobil).
  * Sartname madde 10, arayuzde gosterilmesi zorunlu durumlari kapsar.
  * Eksik gosterilen her bilgi -4 puan.
 */
typedef struct marco_msgs__msg__RobotStatus
{
  std_msgs__msg__Header header;
  uint8_t mission_state;
  /// --- Kontrol modu ---
  /// Fiziksel anahtar otomatik konumdayken uzaktan manuel kontrol kilitlidir.
  bool manual_mode_enabled;
  bool estop_active;
  /// --- Lokalizasyon ---
  geometry_msgs__msg__PoseWithCovarianceStamped pose;
  bool localization_valid;
  /// AMCL kovaryansinin izi, guven gostergesi
  float position_covariance;
  /// --- Navigasyon ---
  /// nav2_route grafindaki aktif kenar
  rosidl_runtime_c__String current_route_edge;
  rosidl_runtime_c__String next_node;
  /// rotadan anlik sapma, limit 0.10
  float cross_track_error;
  bool obstacle_detected;
  /// --- Gorev ayrintilari ---
  rosidl_runtime_c__String task_id;
  rosidl_runtime_c__String pickup_node;
  rosidl_runtime_c__String dropoff_node;
  rosidl_runtime_c__String last_qr_data;
  bool plc_connected;
  bool gate_permission_granted;
} marco_msgs__msg__RobotStatus;

// Struct for a sequence of marco_msgs__msg__RobotStatus.
typedef struct marco_msgs__msg__RobotStatus__Sequence
{
  marco_msgs__msg__RobotStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__msg__RobotStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__MSG__DETAIL__ROBOT_STATUS__STRUCT_H_
