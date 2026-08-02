// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from marco_msgs:msg/LaneOffset.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_H_
#define MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_H_

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
// Member 'camera_frame'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/LaneOffset in the package marco_msgs.
/**
  * Zemindeki renkli seridin robota gore konumu.
  * Yayinci: goruntu isleme ekibi. Tuketici: marco_docking.
  * Sartname madde 4: istasyona 1.5 m kala serit takibi.
 */
typedef struct marco_msgs__msg__LaneOffset
{
  std_msgs__msg__Header header;
  /// Serit goruntude tespit edilebildi mi. false ise diger alanlar gecersizdir.
  bool detected;
  /// Seridin robot merkez ekseninden yanal sapmasi.
  /// Pozitif = serit robotun solunda, robot saga kaymis demektir.
  float lateral_offset;
  /// Robotun yonelimi ile serit dogrultusu arasindaki aci farki.
  /// Pozitif = robot serite gore saat yonunun tersine donuk.
  float heading_error;
  /// Tespit guveni. Docking kontrolcusu esik altini yok sayar.
  float confidence;
  /// Olcumun alindigi kamera: "front" veya "rear".
  /// Yuk tasinirken catal arkada kaldigi icin arka kamera kullanilir.
  rosidl_runtime_c__String camera_frame;
} marco_msgs__msg__LaneOffset;

// Struct for a sequence of marco_msgs__msg__LaneOffset.
typedef struct marco_msgs__msg__LaneOffset__Sequence
{
  marco_msgs__msg__LaneOffset * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} marco_msgs__msg__LaneOffset__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__STRUCT_H_
