// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from marco_msgs:srv/GatePermission.idl
// generated code does not contain a copyright notice
#include "marco_msgs/srv/detail/gate_permission__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `node_id`
#include "rosidl_runtime_c/string_functions.h"

bool
marco_msgs__srv__GatePermission_Request__init(marco_msgs__srv__GatePermission_Request * msg)
{
  if (!msg) {
    return false;
  }
  // node_id
  if (!rosidl_runtime_c__String__init(&msg->node_id)) {
    marco_msgs__srv__GatePermission_Request__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__srv__GatePermission_Request__fini(marco_msgs__srv__GatePermission_Request * msg)
{
  if (!msg) {
    return;
  }
  // node_id
  rosidl_runtime_c__String__fini(&msg->node_id);
}

bool
marco_msgs__srv__GatePermission_Request__are_equal(const marco_msgs__srv__GatePermission_Request * lhs, const marco_msgs__srv__GatePermission_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // node_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->node_id), &(rhs->node_id)))
  {
    return false;
  }
  return true;
}

bool
marco_msgs__srv__GatePermission_Request__copy(
  const marco_msgs__srv__GatePermission_Request * input,
  marco_msgs__srv__GatePermission_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // node_id
  if (!rosidl_runtime_c__String__copy(
      &(input->node_id), &(output->node_id)))
  {
    return false;
  }
  return true;
}

marco_msgs__srv__GatePermission_Request *
marco_msgs__srv__GatePermission_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Request * msg = (marco_msgs__srv__GatePermission_Request *)allocator.allocate(sizeof(marco_msgs__srv__GatePermission_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__srv__GatePermission_Request));
  bool success = marco_msgs__srv__GatePermission_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__srv__GatePermission_Request__destroy(marco_msgs__srv__GatePermission_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__srv__GatePermission_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__srv__GatePermission_Request__Sequence__init(marco_msgs__srv__GatePermission_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Request * data = NULL;

  if (size) {
    data = (marco_msgs__srv__GatePermission_Request *)allocator.zero_allocate(size, sizeof(marco_msgs__srv__GatePermission_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__srv__GatePermission_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__srv__GatePermission_Request__fini(&data[i - 1]);
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
marco_msgs__srv__GatePermission_Request__Sequence__fini(marco_msgs__srv__GatePermission_Request__Sequence * array)
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
      marco_msgs__srv__GatePermission_Request__fini(&array->data[i]);
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

marco_msgs__srv__GatePermission_Request__Sequence *
marco_msgs__srv__GatePermission_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Request__Sequence * array = (marco_msgs__srv__GatePermission_Request__Sequence *)allocator.allocate(sizeof(marco_msgs__srv__GatePermission_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__srv__GatePermission_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__srv__GatePermission_Request__Sequence__destroy(marco_msgs__srv__GatePermission_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__srv__GatePermission_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__srv__GatePermission_Request__Sequence__are_equal(const marco_msgs__srv__GatePermission_Request__Sequence * lhs, const marco_msgs__srv__GatePermission_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__srv__GatePermission_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__srv__GatePermission_Request__Sequence__copy(
  const marco_msgs__srv__GatePermission_Request__Sequence * input,
  marco_msgs__srv__GatePermission_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__srv__GatePermission_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__srv__GatePermission_Request * data =
      (marco_msgs__srv__GatePermission_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__srv__GatePermission_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__srv__GatePermission_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__srv__GatePermission_Request__copy(
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
marco_msgs__srv__GatePermission_Response__init(marco_msgs__srv__GatePermission_Response * msg)
{
  if (!msg) {
    return false;
  }
  // granted
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    marco_msgs__srv__GatePermission_Response__fini(msg);
    return false;
  }
  return true;
}

void
marco_msgs__srv__GatePermission_Response__fini(marco_msgs__srv__GatePermission_Response * msg)
{
  if (!msg) {
    return;
  }
  // granted
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
marco_msgs__srv__GatePermission_Response__are_equal(const marco_msgs__srv__GatePermission_Response * lhs, const marco_msgs__srv__GatePermission_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // granted
  if (lhs->granted != rhs->granted) {
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
marco_msgs__srv__GatePermission_Response__copy(
  const marco_msgs__srv__GatePermission_Response * input,
  marco_msgs__srv__GatePermission_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // granted
  output->granted = input->granted;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

marco_msgs__srv__GatePermission_Response *
marco_msgs__srv__GatePermission_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Response * msg = (marco_msgs__srv__GatePermission_Response *)allocator.allocate(sizeof(marco_msgs__srv__GatePermission_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(marco_msgs__srv__GatePermission_Response));
  bool success = marco_msgs__srv__GatePermission_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
marco_msgs__srv__GatePermission_Response__destroy(marco_msgs__srv__GatePermission_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    marco_msgs__srv__GatePermission_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
marco_msgs__srv__GatePermission_Response__Sequence__init(marco_msgs__srv__GatePermission_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Response * data = NULL;

  if (size) {
    data = (marco_msgs__srv__GatePermission_Response *)allocator.zero_allocate(size, sizeof(marco_msgs__srv__GatePermission_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = marco_msgs__srv__GatePermission_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        marco_msgs__srv__GatePermission_Response__fini(&data[i - 1]);
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
marco_msgs__srv__GatePermission_Response__Sequence__fini(marco_msgs__srv__GatePermission_Response__Sequence * array)
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
      marco_msgs__srv__GatePermission_Response__fini(&array->data[i]);
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

marco_msgs__srv__GatePermission_Response__Sequence *
marco_msgs__srv__GatePermission_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  marco_msgs__srv__GatePermission_Response__Sequence * array = (marco_msgs__srv__GatePermission_Response__Sequence *)allocator.allocate(sizeof(marco_msgs__srv__GatePermission_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = marco_msgs__srv__GatePermission_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
marco_msgs__srv__GatePermission_Response__Sequence__destroy(marco_msgs__srv__GatePermission_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    marco_msgs__srv__GatePermission_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
marco_msgs__srv__GatePermission_Response__Sequence__are_equal(const marco_msgs__srv__GatePermission_Response__Sequence * lhs, const marco_msgs__srv__GatePermission_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!marco_msgs__srv__GatePermission_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
marco_msgs__srv__GatePermission_Response__Sequence__copy(
  const marco_msgs__srv__GatePermission_Response__Sequence * input,
  marco_msgs__srv__GatePermission_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(marco_msgs__srv__GatePermission_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    marco_msgs__srv__GatePermission_Response * data =
      (marco_msgs__srv__GatePermission_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!marco_msgs__srv__GatePermission_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          marco_msgs__srv__GatePermission_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!marco_msgs__srv__GatePermission_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
