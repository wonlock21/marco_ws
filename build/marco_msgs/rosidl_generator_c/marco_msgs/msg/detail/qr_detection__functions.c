// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from marco_msgs:msg/QrDetection.idl
// generated code does not contain a copyright notice
#include "marco_msgs/msg/detail/qr_detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `data`
// Member `camera_frame`
#include "rosidl_runtime_c/string_functions.h"
// Member `pose_in_camera`
#include "geometry_msgs/msg/detail/pose2_d__functions.h"

bool
marco_msgs__msg__QrDetection__init(marco_msgs__msg__QrDetection * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    marco_msgs__msg__QrDetection__fini(msg);
    return false;
  }
  // detected
  // data
  if (!rosidl_runtime_c__String__init(&msg->data)) {
    marco_msgs__msg__QrDetection__fini(msg);
    return false;
  }
  // pose_in_camera
  if (!geometry_msgs__msg__Pose2D__init(&msg->pose_in_camera)) {
    marco_msgs__msg__QrDetection__fini(msg);
    return false;
  }
  // confidence
  // camera_frame
  if (!rosidl_runtime_c__String__init(&msg->camera_frame)) {
    marco_msgs__msg__QrDetection__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__msg__QrDetection__fini(marco_msgs__msg__QrDetection * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // detected
  // data
  rosidl_runtime_c__String__fini(&msg->data);
  // pose_in_camera
  geometry_msgs__msg__Pose2D__fini(&msg->pose_in_camera);
  // confidence
  // camera_frame
  rosidl_runtime_c__String__fini(&msg->camera_frame);
}

bool
marco_msgs__msg__QrDetection__are_equal(const marco_msgs__msg__QrDetection * lhs, const marco_msgs__msg__QrDetection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // detected
  if (lhs->detected != rhs->detected) {
    return false;
  }
  // data
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->data), &(rhs->data)))
  {
    return false;
  }
  // pose_in_camera
  if (!geometry_msgs__msg__Pose2D__are_equal(
      &(lhs->pose_in_camera), &(rhs->pose_in_camera)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // camera_frame
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->camera_frame), &(rhs->camera_frame)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__msg__QrDetection__copy(
  const marco_msgs__msg__QrDetection * input,
  marco_msgs__msg__QrDetection * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // detected
  output->detected = input->detected;
  // data
  if (!rosidl_runtime_c__String__copy(
      &(input->data), &(output->data)))
  {
    return false;
  }
  // pose_in_camera
  if (!geometry_msgs__msg__Pose2D__copy(
      &(input->pose_in_camera), &(output->pose_in_camera)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // camera_frame
  if (!rosidl_runtime_c__String__copy(
      &(input->camera_frame), &(output->camera_frame)))
  {
    return false;
  }
  return true;
}

marco_msgs__msg__QrDetection *
marco_msgs__msg__QrDetection__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__QrDetection * msg = (marco_msgs__msg__QrDetection *)allocator.allocate(sizeof(marco_msgs__msg__QrDetection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__msg__QrDetection));
  bool success = marco_msgs__msg__QrDetection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__msg__QrDetection__destroy(marco_msgs__msg__QrDetection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__msg__QrDetection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__msg__QrDetection__Sequence__init(marco_msgs__msg__QrDetection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__QrDetection * data = NULL;

  if (size) {
    data = (marco_msgs__msg__QrDetection *)allocator.zero_allocate(size, sizeof(marco_msgs__msg__QrDetection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__msg__QrDetection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__msg__QrDetection__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
marco_msgs__msg__QrDetection__Sequence__fini(marco_msgs__msg__QrDetection__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      marco_msgs__msg__QrDetection__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

marco_msgs__msg__QrDetection__Sequence *
marco_msgs__msg__QrDetection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__QrDetection__Sequence * array = (marco_msgs__msg__QrDetection__Sequence *)allocator.allocate(sizeof(marco_msgs__msg__QrDetection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__msg__QrDetection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__msg__QrDetection__Sequence__destroy(marco_msgs__msg__QrDetection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__msg__QrDetection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__msg__QrDetection__Sequence__are_equal(const marco_msgs__msg__QrDetection__Sequence * lhs, const marco_msgs__msg__QrDetection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__msg__QrDetection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__msg__QrDetection__Sequence__copy(
  const marco_msgs__msg__QrDetection__Sequence * input,
  marco_msgs__msg__QrDetection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__msg__QrDetection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__msg__QrDetection * data =
      (marco_msgs__msg__QrDetection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__msg__QrDetection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__msg__QrDetection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__msg__QrDetection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
