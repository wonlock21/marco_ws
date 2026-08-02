// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from marco_msgs:msg/QrDetection.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__QR_DETECTION__STRUCT_H_
#define MARCO_MSGS__MSG__DETAIL__QR_DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'data'
// Member 'camera_frame'
#include "rosidl_runtime_c/string.h"
// Member 'pose_in_camera'
#include "geometry_msgs/msg/detail/pose2_d__struct.h"

/// Struct defined in msg/QrDetection in the package marco_msgs.
/**
  * Okunan QR kodu ve kameraya gore konumu.
  * Yayinci: goruntu isleme ekibi (GM67 + OpenCV). Tuketici: marco_mission, marco_docking.
  * Sartname madde 5: QR okuma ve QR kodun kameraya gore pozisyonunun hesaplanmasi.
 */
typedef struct marco_msgs__msg__QrDetection
{
  std_msgs__msg__Header header;
  /// QR goruntude tespit edilebildi mi.
  bool detected;
  /// QR icerigi. Istasyon kimligi burada tasinir, gorev hedefiyle karsilastirilir.
  rosidl_runtime_c__String data;
  /// QR kodun kamera cercevesine gore konumu.
  /// x ileri [m], y sola [m], theta QR duzleminin donusu [rad].
  geometry_msgs__msg__Pose2D pose_in_camera;
  /// Tespit guveni.
  float confidence;
  /// Olcumun alindigi kamera: "front" veya "rear".
  rosidl_runtime_c__String camera_frame;
} marco_msgs__msg__QrDetection;

// Struct for a sequence of marco_msgs__msg__QrDetection.
typedef struct marco_msgs__msg__QrDetection__Sequence
{
  marco_msgs__msg__QrDetection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__msg__QrDetection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__MSG__DETAIL__QR_DETECTION__STRUCT_H_
