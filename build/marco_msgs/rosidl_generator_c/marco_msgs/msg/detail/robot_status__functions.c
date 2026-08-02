// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from marco_msgs:msg/RobotStatus.idl
// generated code does not contain a copyright notice
#include "marco_msgs/msg/detail/robot_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `pose`
#include "geometry_msgs/msg/detail/pose_with_covariance_stamped__functions.h"
// Member `current_route_edge`
// Member `next_node`
// Member `task_id`
// Member `pickup_node`
// Member `dropoff_node`
// Member `last_qr_data`
#include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__msg__RobotStatus__init(marco_msgs__msg__RobotStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // mission_state
  // manual_mode_enabled
  // estop_active
  // pose
  if (!geometry_msgs__msg__PoseWithCovarianceStamped__init(&msg->pose)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // localization_valid
  // position_covariance
  // current_route_edge
  if (!rosidl_runtime_c__String__init(&msg->current_route_edge)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // next_node
  if (!rosidl_runtime_c__String__init(&msg->next_node)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // cross_track_error
  // obstacle_detected
  // task_id
  if (!rosidl_runtime_c__String__init(&msg->task_id)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // pickup_node
  if (!rosidl_runtime_c__String__init(&msg->pickup_node)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // dropoff_node
  if (!rosidl_runtime_c__String__init(&msg->dropoff_node)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // last_qr_data
  if (!rosidl_runtime_c__String__init(&msg->last_qr_data)) {
    marco_msgs__msg__RobotStatus__fini(msg);
    return false;
  }
  // plc_connected
  // gate_permission_granted
  return true;
}

void
marco_msgs__msg__RobotStatus__fini(marco_msgs__msg__RobotStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // mission_state
  // manual_mode_enabled
  // estop_active
  // pose
  geometry_msgs__msg__PoseWithCovarianceStamped__fini(&msg->pose);
  // localization_valid
  // position_covariance
  // current_route_edge
  rosidl_runtime_c__String__fini(&msg->current_route_edge);
  // next_node
  rosidl_runtime_c__String__fini(&msg->next_node);
  // cross_track_error
  // obstacle_detected
  // task_id
  rosidl_runtime_c__String__fini(&msg->task_id);
  // pickup_node
  rosidl_runtime_c__String__fini(&msg->pickup_node);
  // dropoff_node
  rosidl_runtime_c__String__fini(&msg->dropoff_node);
  // last_qr_data
  rosidl_runtime_c__String__fini(&msg->last_qr_data);
  // plc_connected
  // gate_permission_granted
}

bool
marco_msgs__msg__RobotStatus__are_equal(const marco_msgs__msg__RobotStatus * lhs, const marco_msgs__msg__RobotStatus * rhs)
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
  // mission_state
  if (lhs->mission_state != rhs->mission_state) {
    return false;
  }
  // manual_mode_enabled
  if (lhs->manual_mode_enabled != rhs->manual_mode_enabled) {
    return false;
  }
  // estop_active
  if (lhs->estop_active != rhs->estop_active) {
    return false;
  }
  // pose
  if (!geometry_msgs__msg__PoseWithCovarianceStamped__are_equal(
      &(lhs->pose), &(rhs->pose)))
  {
    return false;
  }
  // localization_valid
  if (lhs->localization_valid != rhs->localization_valid) {
    return false;
  }
  // position_covariance
  if (lhs->position_covariance != rhs->position_covariance) {
    return false;
  }
  // current_route_edge
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->current_route_edge), &(rhs->current_route_edge)))
  {
    return false;
  }
  // next_node
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->next_node), &(rhs->next_node)))
  {
    return false;
  }
  // cross_track_error
  if (lhs->cross_track_error != rhs->cross_track_error) {
    return false;
  }
  // obstacle_detected
  if (lhs->obstacle_detected != rhs->obstacle_detected) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->task_id), &(rhs->task_id)))
  {
    return false;
  }
  // pickup_node
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->pickup_node), &(rhs->pickup_node)))
  {
    return false;
  }
  // dropoff_node
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->dropoff_node), &(rhs->dropoff_node)))
  {
    return false;
  }
  // last_qr_data
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->last_qr_data), &(rhs->last_qr_data)))
  {
    return false;
  }
  // plc_connected
  if (lhs->plc_connected != rhs->plc_connected) {
    return false;
  }
  // gate_permission_granted
  if (lhs->gate_permission_granted != rhs->gate_permission_granted) {
    return false;
  }
  return true;
}

bool
marco_msgs__msg__RobotStatus__copy(
  const marco_msgs__msg__RobotStatus * input,
  marco_msgs__msg__RobotStatus * output)
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
  // mission_state
  output->mission_state = input->mission_state;
  // manual_mode_enabled
  output->manual_mode_enabled = input->manual_mode_enabled;
  // estop_active
  output->estop_active = input->estop_active;
  // pose
  if (!geometry_msgs__msg__PoseWithCovarianceStamped__copy(
      &(input->pose), &(output->pose)))
  {
    return false;
  }
  // localization_valid
  output->localization_valid = input->localization_valid;
  // position_covariance
  output->position_covariance = input->position_covariance;
  // current_route_edge
  if (!rosidl_runtime_c__String__copy(
      &(input->current_route_edge), &(output->current_route_edge)))
  {
    return false;
  }
  // next_node
  if (!rosidl_runtime_c__String__copy(
      &(input->next_node), &(output->next_node)))
  {
    return false;
  }
  // cross_track_error
  output->cross_track_error = input->cross_track_error;
  // obstacle_detected
  output->obstacle_detected = input->obstacle_detected;
  // task_id
  if (!rosidl_runtime_c__String__copy(
      &(input->task_id), &(output->task_id)))
  {
    return false;
  }
  // pickup_node
  if (!rosidl_runtime_c__String__copy(
      &(input->pickup_node), &(output->pickup_node)))
  {
    return false;
  }
  // dropoff_node
  if (!rosidl_runtime_c__String__copy(
      &(input->dropoff_node), &(output->dropoff_node)))
  {
    return false;
  }
  // last_qr_data
  if (!rosidl_runtime_c__String__copy(
      &(input->last_qr_data), &(output->last_qr_data)))
  {
    return false;
  }
  // plc_connected
  output->plc_connected = input->plc_connected;
  // gate_permission_granted
  output->gate_permission_granted = input->gate_permission_granted;
  return true;
}

marco_msgs__msg__RobotStatus *
marco_msgs__msg__RobotStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__RobotStatus * msg = (marco_msgs__msg__RobotStatus *)allocator.allocate(sizeof(marco_msgs__msg__RobotStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__msg__RobotStatus));
  bool success = marco_msgs__msg__RobotStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__msg__RobotStatus__destroy(marco_msgs__msg__RobotStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__msg__RobotStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__msg__RobotStatus__Sequence__init(marco_msgs__msg__RobotStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__RobotStatus * data = NULL;

  if (size) {
    data = (marco_msgs__msg__RobotStatus *)allocator.zero_allocate(size, sizeof(marco_msgs__msg__RobotStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__msg__RobotStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__msg__RobotStatus__fini(&data[i - 1]);
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
marco_msgs__msg__RobotStatus__Sequence__fini(marco_msgs__msg__RobotStatus__Sequence * array)
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
      marco_msgs__msg__RobotStatus__fini(&array->data[i]);
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

marco_msgs__msg__RobotStatus__Sequence *
marco_msgs__msg__RobotStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__msg__RobotStatus__Sequence * array = (marco_msgs__msg__RobotStatus__Sequence *)allocator.allocate(sizeof(marco_msgs__msg__RobotStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__msg__RobotStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__msg__RobotStatus__Sequence__destroy(marco_msgs__msg__RobotStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__msg__RobotStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__msg__RobotStatus__Sequence__are_equal(const marco_msgs__msg__RobotStatus__Sequence * lhs, const marco_msgs__msg__RobotStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__msg__RobotStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__msg__RobotStatus__Sequence__copy(
  const marco_msgs__msg__RobotStatus__Sequence * input,
  marco_msgs__msg__RobotStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__msg__RobotStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__msg__RobotStatus * data =
      (marco_msgs__msg__RobotStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__msg__RobotStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__msg__RobotStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__msg__RobotStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
