// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from marco_msgs:srv/TaskComplete.idl
// generated code does not contain a copyright notice
#include "marco_msgs/srv/detail/task_complete__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `task_id`
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__srv__TaskComplete_Request__init(marco_msgs__srv__TaskComplete_Request * msg)
{
  if (!msg) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__init(&msg->task_id)) {
    marco_msgs__srv__TaskComplete_Request__fini(msg);
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    marco_msgs__srv__TaskComplete_Request__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__srv__TaskComplete_Request__fini(marco_msgs__srv__TaskComplete_Request * msg)
{
  if (!msg) {
    return;
  }
  // task_id
  rosidl_runtime_c__String__fini(&msg->task_id);
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
marco_msgs__srv__TaskComplete_Request__are_equal(const marco_msgs__srv__TaskComplete_Request * lhs, const marco_msgs__srv__TaskComplete_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->task_id), &(rhs->task_id)))
  {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
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
marco_msgs__srv__TaskComplete_Request__copy(
  const marco_msgs__srv__TaskComplete_Request * input,
  marco_msgs__srv__TaskComplete_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__copy(
      &(input->task_id), &(output->task_id)))
  {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

marco_msgs__srv__TaskComplete_Request *
marco_msgs__srv__TaskComplete_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Request * msg = (marco_msgs__srv__TaskComplete_Request *)allocator.allocate(sizeof(marco_msgs__srv__TaskComplete_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__srv__TaskComplete_Request));
  bool success = marco_msgs__srv__TaskComplete_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__srv__TaskComplete_Request__destroy(marco_msgs__srv__TaskComplete_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__srv__TaskComplete_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__srv__TaskComplete_Request__Sequence__init(marco_msgs__srv__TaskComplete_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Request * data = NULL;

  if (size) {
    data = (marco_msgs__srv__TaskComplete_Request *)allocator.zero_allocate(size, sizeof(marco_msgs__srv__TaskComplete_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__srv__TaskComplete_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__srv__TaskComplete_Request__fini(&data[i - 1]);
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
marco_msgs__srv__TaskComplete_Request__Sequence__fini(marco_msgs__srv__TaskComplete_Request__Sequence * array)
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
      marco_msgs__srv__TaskComplete_Request__fini(&array->data[i]);
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

marco_msgs__srv__TaskComplete_Request__Sequence *
marco_msgs__srv__TaskComplete_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Request__Sequence * array = (marco_msgs__srv__TaskComplete_Request__Sequence *)allocator.allocate(sizeof(marco_msgs__srv__TaskComplete_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__srv__TaskComplete_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__srv__TaskComplete_Request__Sequence__destroy(marco_msgs__srv__TaskComplete_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__srv__TaskComplete_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__srv__TaskComplete_Request__Sequence__are_equal(const marco_msgs__srv__TaskComplete_Request__Sequence * lhs, const marco_msgs__srv__TaskComplete_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__srv__TaskComplete_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__srv__TaskComplete_Request__Sequence__copy(
  const marco_msgs__srv__TaskComplete_Request__Sequence * input,
  marco_msgs__srv__TaskComplete_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__srv__TaskComplete_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__srv__TaskComplete_Request * data =
      (marco_msgs__srv__TaskComplete_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__srv__TaskComplete_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__srv__TaskComplete_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__srv__TaskComplete_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
marco_msgs__srv__TaskComplete_Response__init(marco_msgs__srv__TaskComplete_Response * msg)
{
  if (!msg) {
    return false;
  }
  // acknowledged
  return true;
}

void
marco_msgs__srv__TaskComplete_Response__fini(marco_msgs__srv__TaskComplete_Response * msg)
{
  if (!msg) {
    return;
  }
  // acknowledged
}

bool
marco_msgs__srv__TaskComplete_Response__are_equal(const marco_msgs__srv__TaskComplete_Response * lhs, const marco_msgs__srv__TaskComplete_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // acknowledged
  if (lhs->acknowledged != rhs->acknowledged) {
    return false;
  }
  return true;
}

bool
marco_msgs__srv__TaskComplete_Response__copy(
  const marco_msgs__srv__TaskComplete_Response * input,
  marco_msgs__srv__TaskComplete_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // acknowledged
  output->acknowledged = input->acknowledged;
  return true;
}

marco_msgs__srv__TaskComplete_Response *
marco_msgs__srv__TaskComplete_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Response * msg = (marco_msgs__srv__TaskComplete_Response *)allocator.allocate(sizeof(marco_msgs__srv__TaskComplete_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__srv__TaskComplete_Response));
  bool success = marco_msgs__srv__TaskComplete_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__srv__TaskComplete_Response__destroy(marco_msgs__srv__TaskComplete_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__srv__TaskComplete_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__srv__TaskComplete_Response__Sequence__init(marco_msgs__srv__TaskComplete_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Response * data = NULL;

  if (size) {
    data = (marco_msgs__srv__TaskComplete_Response *)allocator.zero_allocate(size, sizeof(marco_msgs__srv__TaskComplete_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__srv__TaskComplete_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__srv__TaskComplete_Response__fini(&data[i - 1]);
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
marco_msgs__srv__TaskComplete_Response__Sequence__fini(marco_msgs__srv__TaskComplete_Response__Sequence * array)
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
      marco_msgs__srv__TaskComplete_Response__fini(&array->data[i]);
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

marco_msgs__srv__TaskComplete_Response__Sequence *
marco_msgs__srv__TaskComplete_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__TaskComplete_Response__Sequence * array = (marco_msgs__srv__TaskComplete_Response__Sequence *)allocator.allocate(sizeof(marco_msgs__srv__TaskComplete_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__srv__TaskComplete_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__srv__TaskComplete_Response__Sequence__destroy(marco_msgs__srv__TaskComplete_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__srv__TaskComplete_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__srv__TaskComplete_Response__Sequence__are_equal(const marco_msgs__srv__TaskComplete_Response__Sequence * lhs, const marco_msgs__srv__TaskComplete_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__srv__TaskComplete_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__srv__TaskComplete_Response__Sequence__copy(
  const marco_msgs__srv__TaskComplete_Response__Sequence * input,
  marco_msgs__srv__TaskComplete_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__srv__TaskComplete_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__srv__TaskComplete_Response * data =
      (marco_msgs__srv__TaskComplete_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__srv__TaskComplete_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__srv__TaskComplete_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__srv__TaskComplete_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
