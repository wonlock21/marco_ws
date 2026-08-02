// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice
#include "marco_msgs/action/detail/dock_to_station__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `station_id`
#include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__action__DockToStation_Goal__init(marco_msgs__action__DockToStation_Goal * msg)
{
  if (!msg) {
    return false;
  }
  // station_id
  if (!rosidl_runtime_c__String__init(&msg->station_id)) {
    marco_msgs__action__DockToStation_Goal__fini(msg);
    return false;
  }
  // position_tolerance
  // yaw_tolerance
  // approach_type
  // timeout
  return true;
}

void
marco_msgs__action__DockToStation_Goal__fini(marco_msgs__action__DockToStation_Goal * msg)
{
  if (!msg) {
    return;
  }
  // station_id
  rosidl_runtime_c__String__fini(&msg->station_id);
  // position_tolerance
  // yaw_tolerance
  // approach_type
  // timeout
}

bool
marco_msgs__action__DockToStation_Goal__are_equal(const marco_msgs__action__DockToStation_Goal * lhs, const marco_msgs__action__DockToStation_Goal * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // station_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->station_id), &(rhs->station_id)))
  {
    return false;
  }
  // position_tolerance
  if (lhs->position_tolerance != rhs->position_tolerance) {
    return false;
  }
  // yaw_tolerance
  if (lhs->yaw_tolerance != rhs->yaw_tolerance) {
    return false;
  }
  // approach_type
  if (lhs->approach_type != rhs->approach_type) {
    return false;
  }
  // timeout
  if (lhs->timeout != rhs->timeout) {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Goal__copy(
  const marco_msgs__action__DockToStation_Goal * input,
  marco_msgs__action__DockToStation_Goal * output)
{
  if (!input || !output) {
    return false;
  }
  // station_id
  if (!rosidl_runtime_c__String__copy(
      &(input->station_id), &(output->station_id)))
  {
    return false;
  }
  // position_tolerance
  output->position_tolerance = input->position_tolerance;
  // yaw_tolerance
  output->yaw_tolerance = input->yaw_tolerance;
  // approach_type
  output->approach_type = input->approach_type;
  // timeout
  output->timeout = input->timeout;
  return true;
}

marco_msgs__action__DockToStation_Goal *
marco_msgs__action__DockToStation_Goal__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Goal * msg = (marco_msgs__action__DockToStation_Goal *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Goal), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_Goal));
  bool success = marco_msgs__action__DockToStation_Goal__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_Goal__destroy(marco_msgs__action__DockToStation_Goal * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_Goal__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_Goal__Sequence__init(marco_msgs__action__DockToStation_Goal__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Goal * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_Goal *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_Goal), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_Goal__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_Goal__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_Goal__Sequence__fini(marco_msgs__action__DockToStation_Goal__Sequence * array)
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
      marco_msgs__action__DockToStation_Goal__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_Goal__Sequence *
marco_msgs__action__DockToStation_Goal__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Goal__Sequence * array = (marco_msgs__action__DockToStation_Goal__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Goal__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_Goal__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_Goal__Sequence__destroy(marco_msgs__action__DockToStation_Goal__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_Goal__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_Goal__Sequence__are_equal(const marco_msgs__action__DockToStation_Goal__Sequence * lhs, const marco_msgs__action__DockToStation_Goal__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_Goal__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Goal__Sequence__copy(
  const marco_msgs__action__DockToStation_Goal__Sequence * input,
  marco_msgs__action__DockToStation_Goal__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_Goal);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_Goal * data =
      (marco_msgs__action__DockToStation_Goal *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_Goal__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_Goal__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_Goal__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__action__DockToStation_Result__init(marco_msgs__action__DockToStation_Result * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // final_position_error
  // final_yaw_error
  // result_code
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    marco_msgs__action__DockToStation_Result__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_Result__fini(marco_msgs__action__DockToStation_Result * msg)
{
  if (!msg) {
    return;
  }
  // success
  // final_position_error
  // final_yaw_error
  // result_code
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
marco_msgs__action__DockToStation_Result__are_equal(const marco_msgs__action__DockToStation_Result * lhs, const marco_msgs__action__DockToStation_Result * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // final_position_error
  if (lhs->final_position_error != rhs->final_position_error) {
    return false;
  }
  // final_yaw_error
  if (lhs->final_yaw_error != rhs->final_yaw_error) {
    return false;
  }
  // result_code
  if (lhs->result_code != rhs->result_code) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Result__copy(
  const marco_msgs__action__DockToStation_Result * input,
  marco_msgs__action__DockToStation_Result * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // final_position_error
  output->final_position_error = input->final_position_error;
  // final_yaw_error
  output->final_yaw_error = input->final_yaw_error;
  // result_code
  output->result_code = input->result_code;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_Result *
marco_msgs__action__DockToStation_Result__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Result * msg = (marco_msgs__action__DockToStation_Result *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Result), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_Result));
  bool success = marco_msgs__action__DockToStation_Result__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_Result__destroy(marco_msgs__action__DockToStation_Result * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_Result__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_Result__Sequence__init(marco_msgs__action__DockToStation_Result__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Result * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_Result *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_Result), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_Result__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_Result__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_Result__Sequence__fini(marco_msgs__action__DockToStation_Result__Sequence * array)
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
      marco_msgs__action__DockToStation_Result__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_Result__Sequence *
marco_msgs__action__DockToStation_Result__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Result__Sequence * array = (marco_msgs__action__DockToStation_Result__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Result__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_Result__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_Result__Sequence__destroy(marco_msgs__action__DockToStation_Result__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_Result__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_Result__Sequence__are_equal(const marco_msgs__action__DockToStation_Result__Sequence * lhs, const marco_msgs__action__DockToStation_Result__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_Result__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Result__Sequence__copy(
  const marco_msgs__action__DockToStation_Result__Sequence * input,
  marco_msgs__action__DockToStation_Result__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_Result);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_Result * data =
      (marco_msgs__action__DockToStation_Result *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_Result__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_Result__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_Result__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `phase`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__action__DockToStation_Feedback__init(marco_msgs__action__DockToStation_Feedback * msg)
{
  if (!msg) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__init(&msg->phase)) {
    marco_msgs__action__DockToStation_Feedback__fini(msg);
    return false;
  }
  // position_error
  // yaw_error
  // distance_remaining
  return true;
}

void
marco_msgs__action__DockToStation_Feedback__fini(marco_msgs__action__DockToStation_Feedback * msg)
{
  if (!msg) {
    return;
  }
  // phase
  rosidl_runtime_c__String__fini(&msg->phase);
  // position_error
  // yaw_error
  // distance_remaining
}

bool
marco_msgs__action__DockToStation_Feedback__are_equal(const marco_msgs__action__DockToStation_Feedback * lhs, const marco_msgs__action__DockToStation_Feedback * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->phase), &(rhs->phase)))
  {
    return false;
  }
  // position_error
  if (lhs->position_error != rhs->position_error) {
    return false;
  }
  // yaw_error
  if (lhs->yaw_error != rhs->yaw_error) {
    return false;
  }
  // distance_remaining
  if (lhs->distance_remaining != rhs->distance_remaining) {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Feedback__copy(
  const marco_msgs__action__DockToStation_Feedback * input,
  marco_msgs__action__DockToStation_Feedback * output)
{
  if (!input || !output) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__copy(
      &(input->phase), &(output->phase)))
  {
    return false;
  }
  // position_error
  output->position_error = input->position_error;
  // yaw_error
  output->yaw_error = input->yaw_error;
  // distance_remaining
  output->distance_remaining = input->distance_remaining;
  return true;
}

marco_msgs__action__DockToStation_Feedback *
marco_msgs__action__DockToStation_Feedback__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Feedback * msg = (marco_msgs__action__DockToStation_Feedback *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Feedback), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_Feedback));
  bool success = marco_msgs__action__DockToStation_Feedback__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_Feedback__destroy(marco_msgs__action__DockToStation_Feedback * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_Feedback__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_Feedback__Sequence__init(marco_msgs__action__DockToStation_Feedback__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Feedback * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_Feedback *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_Feedback), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_Feedback__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_Feedback__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_Feedback__Sequence__fini(marco_msgs__action__DockToStation_Feedback__Sequence * array)
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
      marco_msgs__action__DockToStation_Feedback__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_Feedback__Sequence *
marco_msgs__action__DockToStation_Feedback__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_Feedback__Sequence * array = (marco_msgs__action__DockToStation_Feedback__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_Feedback__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_Feedback__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_Feedback__Sequence__destroy(marco_msgs__action__DockToStation_Feedback__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_Feedback__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_Feedback__Sequence__are_equal(const marco_msgs__action__DockToStation_Feedback__Sequence * lhs, const marco_msgs__action__DockToStation_Feedback__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_Feedback__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_Feedback__Sequence__copy(
  const marco_msgs__action__DockToStation_Feedback__Sequence * input,
  marco_msgs__action__DockToStation_Feedback__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_Feedback);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_Feedback * data =
      (marco_msgs__action__DockToStation_Feedback *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_Feedback__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_Feedback__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_Feedback__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
#include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `goal`
// already included above
// #include "marco_msgs/action/detail/dock_to_station__functions.h"

bool
marco_msgs__action__DockToStation_SendGoal_Request__init(marco_msgs__action__DockToStation_SendGoal_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    marco_msgs__action__DockToStation_SendGoal_Request__fini(msg);
    return false;
  }
  // goal
  if (!marco_msgs__action__DockToStation_Goal__init(&msg->goal)) {
    marco_msgs__action__DockToStation_SendGoal_Request__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_SendGoal_Request__fini(marco_msgs__action__DockToStation_SendGoal_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // goal
  marco_msgs__action__DockToStation_Goal__fini(&msg->goal);
}

bool
marco_msgs__action__DockToStation_SendGoal_Request__are_equal(const marco_msgs__action__DockToStation_SendGoal_Request * lhs, const marco_msgs__action__DockToStation_SendGoal_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // goal
  if (!marco_msgs__action__DockToStation_Goal__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_SendGoal_Request__copy(
  const marco_msgs__action__DockToStation_SendGoal_Request * input,
  marco_msgs__action__DockToStation_SendGoal_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // goal
  if (!marco_msgs__action__DockToStation_Goal__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_SendGoal_Request *
marco_msgs__action__DockToStation_SendGoal_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Request * msg = (marco_msgs__action__DockToStation_SendGoal_Request *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_SendGoal_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_SendGoal_Request));
  bool success = marco_msgs__action__DockToStation_SendGoal_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_SendGoal_Request__destroy(marco_msgs__action__DockToStation_SendGoal_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_SendGoal_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__init(marco_msgs__action__DockToStation_SendGoal_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Request * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_SendGoal_Request *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_SendGoal_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_SendGoal_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_SendGoal_Request__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__fini(marco_msgs__action__DockToStation_SendGoal_Request__Sequence * array)
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
      marco_msgs__action__DockToStation_SendGoal_Request__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_SendGoal_Request__Sequence *
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Request__Sequence * array = (marco_msgs__action__DockToStation_SendGoal_Request__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_SendGoal_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_SendGoal_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__destroy(marco_msgs__action__DockToStation_SendGoal_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_SendGoal_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__are_equal(const marco_msgs__action__DockToStation_SendGoal_Request__Sequence * lhs, const marco_msgs__action__DockToStation_SendGoal_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_SendGoal_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_SendGoal_Request__Sequence__copy(
  const marco_msgs__action__DockToStation_SendGoal_Request__Sequence * input,
  marco_msgs__action__DockToStation_SendGoal_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_SendGoal_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_SendGoal_Request * data =
      (marco_msgs__action__DockToStation_SendGoal_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_SendGoal_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_SendGoal_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_SendGoal_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
marco_msgs__action__DockToStation_SendGoal_Response__init(marco_msgs__action__DockToStation_SendGoal_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    marco_msgs__action__DockToStation_SendGoal_Response__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_SendGoal_Response__fini(marco_msgs__action__DockToStation_SendGoal_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
marco_msgs__action__DockToStation_SendGoal_Response__are_equal(const marco_msgs__action__DockToStation_SendGoal_Response * lhs, const marco_msgs__action__DockToStation_SendGoal_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_SendGoal_Response__copy(
  const marco_msgs__action__DockToStation_SendGoal_Response * input,
  marco_msgs__action__DockToStation_SendGoal_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_SendGoal_Response *
marco_msgs__action__DockToStation_SendGoal_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Response * msg = (marco_msgs__action__DockToStation_SendGoal_Response *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_SendGoal_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_SendGoal_Response));
  bool success = marco_msgs__action__DockToStation_SendGoal_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_SendGoal_Response__destroy(marco_msgs__action__DockToStation_SendGoal_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_SendGoal_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__init(marco_msgs__action__DockToStation_SendGoal_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Response * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_SendGoal_Response *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_SendGoal_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_SendGoal_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_SendGoal_Response__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__fini(marco_msgs__action__DockToStation_SendGoal_Response__Sequence * array)
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
      marco_msgs__action__DockToStation_SendGoal_Response__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_SendGoal_Response__Sequence *
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_SendGoal_Response__Sequence * array = (marco_msgs__action__DockToStation_SendGoal_Response__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_SendGoal_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_SendGoal_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__destroy(marco_msgs__action__DockToStation_SendGoal_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_SendGoal_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__are_equal(const marco_msgs__action__DockToStation_SendGoal_Response__Sequence * lhs, const marco_msgs__action__DockToStation_SendGoal_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_SendGoal_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_SendGoal_Response__Sequence__copy(
  const marco_msgs__action__DockToStation_SendGoal_Response__Sequence * input,
  marco_msgs__action__DockToStation_SendGoal_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_SendGoal_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_SendGoal_Response * data =
      (marco_msgs__action__DockToStation_SendGoal_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_SendGoal_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_SendGoal_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_SendGoal_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"

bool
marco_msgs__action__DockToStation_GetResult_Request__init(marco_msgs__action__DockToStation_GetResult_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    marco_msgs__action__DockToStation_GetResult_Request__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_GetResult_Request__fini(marco_msgs__action__DockToStation_GetResult_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
}

bool
marco_msgs__action__DockToStation_GetResult_Request__are_equal(const marco_msgs__action__DockToStation_GetResult_Request * lhs, const marco_msgs__action__DockToStation_GetResult_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_GetResult_Request__copy(
  const marco_msgs__action__DockToStation_GetResult_Request * input,
  marco_msgs__action__DockToStation_GetResult_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_GetResult_Request *
marco_msgs__action__DockToStation_GetResult_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Request * msg = (marco_msgs__action__DockToStation_GetResult_Request *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_GetResult_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_GetResult_Request));
  bool success = marco_msgs__action__DockToStation_GetResult_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_GetResult_Request__destroy(marco_msgs__action__DockToStation_GetResult_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_GetResult_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_GetResult_Request__Sequence__init(marco_msgs__action__DockToStation_GetResult_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Request * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_GetResult_Request *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_GetResult_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_GetResult_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_GetResult_Request__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_GetResult_Request__Sequence__fini(marco_msgs__action__DockToStation_GetResult_Request__Sequence * array)
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
      marco_msgs__action__DockToStation_GetResult_Request__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_GetResult_Request__Sequence *
marco_msgs__action__DockToStation_GetResult_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Request__Sequence * array = (marco_msgs__action__DockToStation_GetResult_Request__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_GetResult_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_GetResult_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_GetResult_Request__Sequence__destroy(marco_msgs__action__DockToStation_GetResult_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_GetResult_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_GetResult_Request__Sequence__are_equal(const marco_msgs__action__DockToStation_GetResult_Request__Sequence * lhs, const marco_msgs__action__DockToStation_GetResult_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_GetResult_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_GetResult_Request__Sequence__copy(
  const marco_msgs__action__DockToStation_GetResult_Request__Sequence * input,
  marco_msgs__action__DockToStation_GetResult_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_GetResult_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_GetResult_Request * data =
      (marco_msgs__action__DockToStation_GetResult_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_GetResult_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_GetResult_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_GetResult_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `result`
// already included above
// #include "marco_msgs/action/detail/dock_to_station__functions.h"

bool
marco_msgs__action__DockToStation_GetResult_Response__init(marco_msgs__action__DockToStation_GetResult_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  // result
  if (!marco_msgs__action__DockToStation_Result__init(&msg->result)) {
    marco_msgs__action__DockToStation_GetResult_Response__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_GetResult_Response__fini(marco_msgs__action__DockToStation_GetResult_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  // result
  marco_msgs__action__DockToStation_Result__fini(&msg->result);
}

bool
marco_msgs__action__DockToStation_GetResult_Response__are_equal(const marco_msgs__action__DockToStation_GetResult_Response * lhs, const marco_msgs__action__DockToStation_GetResult_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // result
  if (!marco_msgs__action__DockToStation_Result__are_equal(
      &(lhs->result), &(rhs->result)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_GetResult_Response__copy(
  const marco_msgs__action__DockToStation_GetResult_Response * input,
  marco_msgs__action__DockToStation_GetResult_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  // result
  if (!marco_msgs__action__DockToStation_Result__copy(
      &(input->result), &(output->result)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_GetResult_Response *
marco_msgs__action__DockToStation_GetResult_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Response * msg = (marco_msgs__action__DockToStation_GetResult_Response *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_GetResult_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_GetResult_Response));
  bool success = marco_msgs__action__DockToStation_GetResult_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_GetResult_Response__destroy(marco_msgs__action__DockToStation_GetResult_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_GetResult_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_GetResult_Response__Sequence__init(marco_msgs__action__DockToStation_GetResult_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Response * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_GetResult_Response *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_GetResult_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_GetResult_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_GetResult_Response__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_GetResult_Response__Sequence__fini(marco_msgs__action__DockToStation_GetResult_Response__Sequence * array)
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
      marco_msgs__action__DockToStation_GetResult_Response__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_GetResult_Response__Sequence *
marco_msgs__action__DockToStation_GetResult_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_GetResult_Response__Sequence * array = (marco_msgs__action__DockToStation_GetResult_Response__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_GetResult_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_GetResult_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_GetResult_Response__Sequence__destroy(marco_msgs__action__DockToStation_GetResult_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_GetResult_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_GetResult_Response__Sequence__are_equal(const marco_msgs__action__DockToStation_GetResult_Response__Sequence * lhs, const marco_msgs__action__DockToStation_GetResult_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_GetResult_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_GetResult_Response__Sequence__copy(
  const marco_msgs__action__DockToStation_GetResult_Response__Sequence * input,
  marco_msgs__action__DockToStation_GetResult_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_GetResult_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_GetResult_Response * data =
      (marco_msgs__action__DockToStation_GetResult_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_GetResult_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_GetResult_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_GetResult_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `feedback`
// already included above
// #include "marco_msgs/action/detail/dock_to_station__functions.h"

bool
marco_msgs__action__DockToStation_FeedbackMessage__init(marco_msgs__action__DockToStation_FeedbackMessage * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    marco_msgs__action__DockToStation_FeedbackMessage__fini(msg);
    return false;
  }
  // feedback
  if (!marco_msgs__action__DockToStation_Feedback__init(&msg->feedback)) {
    marco_msgs__action__DockToStation_FeedbackMessage__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__action__DockToStation_FeedbackMessage__fini(marco_msgs__action__DockToStation_FeedbackMessage * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // feedback
  marco_msgs__action__DockToStation_Feedback__fini(&msg->feedback);
}

bool
marco_msgs__action__DockToStation_FeedbackMessage__are_equal(const marco_msgs__action__DockToStation_FeedbackMessage * lhs, const marco_msgs__action__DockToStation_FeedbackMessage * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // feedback
  if (!marco_msgs__action__DockToStation_Feedback__are_equal(
      &(lhs->feedback), &(rhs->feedback)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__action__DockToStation_FeedbackMessage__copy(
  const marco_msgs__action__DockToStation_FeedbackMessage * input,
  marco_msgs__action__DockToStation_FeedbackMessage * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // feedback
  if (!marco_msgs__action__DockToStation_Feedback__copy(
      &(input->feedback), &(output->feedback)))
  {
    return false;
  }
  return true;
}

marco_msgs__action__DockToStation_FeedbackMessage *
marco_msgs__action__DockToStation_FeedbackMessage__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_FeedbackMessage * msg = (marco_msgs__action__DockToStation_FeedbackMessage *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_FeedbackMessage), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__action__DockToStation_FeedbackMessage));
  bool success = marco_msgs__action__DockToStation_FeedbackMessage__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__action__DockToStation_FeedbackMessage__destroy(marco_msgs__action__DockToStation_FeedbackMessage * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__action__DockToStation_FeedbackMessage__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__init(marco_msgs__action__DockToStation_FeedbackMessage__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_FeedbackMessage * data = NULL;

  if (size) {
    data = (marco_msgs__action__DockToStation_FeedbackMessage *)allocator.zero_allocate(size, sizeof(marco_msgs__action__DockToStation_FeedbackMessage), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__action__DockToStation_FeedbackMessage__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__action__DockToStation_FeedbackMessage__fini(&data[i - 1]);
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
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__fini(marco_msgs__action__DockToStation_FeedbackMessage__Sequence * array)
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
      marco_msgs__action__DockToStation_FeedbackMessage__fini(&array->data[i]);
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

marco_msgs__action__DockToStation_FeedbackMessage__Sequence *
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__action__DockToStation_FeedbackMessage__Sequence * array = (marco_msgs__action__DockToStation_FeedbackMessage__Sequence *)allocator.allocate(sizeof(marco_msgs__action__DockToStation_FeedbackMessage__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__action__DockToStation_FeedbackMessage__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__destroy(marco_msgs__action__DockToStation_FeedbackMessage__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__action__DockToStation_FeedbackMessage__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__are_equal(const marco_msgs__action__DockToStation_FeedbackMessage__Sequence * lhs, const marco_msgs__action__DockToStation_FeedbackMessage__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__action__DockToStation_FeedbackMessage__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__action__DockToStation_FeedbackMessage__Sequence__copy(
  const marco_msgs__action__DockToStation_FeedbackMessage__Sequence * input,
  marco_msgs__action__DockToStation_FeedbackMessage__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__action__DockToStation_FeedbackMessage);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__action__DockToStation_FeedbackMessage * data =
      (marco_msgs__action__DockToStation_FeedbackMessage *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__action__DockToStation_FeedbackMessage__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__action__DockToStation_FeedbackMessage__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__action__DockToStation_FeedbackMessage__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
