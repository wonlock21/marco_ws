// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from marco_msgs:msg/LaneOffset.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__FUNCTIONS_H_
#define MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "marco_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "marco_msgs/msg/detail/lane_offset__struct.h"

/// Initialize msg/LaneOffset message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * marco_msgs__msg__LaneOffset
 * )) before or use
 * marco_msgs__msg__LaneOffset__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__init(marco_msgs__msg__LaneOffset * msg);

/// Finalize msg/LaneOffset message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__LaneOffset__fini(marco_msgs__msg__LaneOffset * msg);

/// Create msg/LaneOffset message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * marco_msgs__msg__LaneOffset__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
marco_msgs__msg__LaneOffset *
marco_msgs__msg__LaneOffset__create();

/// Destroy msg/LaneOffset message.
/**
 * It calls
 * marco_msgs__msg__LaneOffset__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__LaneOffset__destroy(marco_msgs__msg__LaneOffset * msg);

/// Check for msg/LaneOffset message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__are_equal(const marco_msgs__msg__LaneOffset * lhs, const marco_msgs__msg__LaneOffset * rhs);

/// Copy a msg/LaneOffset message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__copy(
  const marco_msgs__msg__LaneOffset * input,
  marco_msgs__msg__LaneOffset * output);

/// Initialize array of msg/LaneOffset messages.
/**
 * It allocates the memory for the number of elements and calls
 * marco_msgs__msg__LaneOffset__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__Sequence__init(marco_msgs__msg__LaneOffset__Sequence * array, size_t size);

/// Finalize array of msg/LaneOffset messages.
/**
 * It calls
 * marco_msgs__msg__LaneOffset__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__LaneOffset__Sequence__fini(marco_msgs__msg__LaneOffset__Sequence * array);

/// Create array of msg/LaneOffset messages.
/**
 * It allocates the memory for the array and calls
 * marco_msgs__msg__LaneOffset__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
marco_msgs__msg__LaneOffset__Sequence *
marco_msgs__msg__LaneOffset__Sequence__create(size_t size);

/// Destroy array of msg/LaneOffset messages.
/**
 * It calls
 * marco_msgs__msg__LaneOffset__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__LaneOffset__Sequence__destroy(marco_msgs__msg__LaneOffset__Sequence * array);

/// Check for msg/LaneOffset message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__Sequence__are_equal(const marco_msgs__msg__LaneOffset__Sequence * lhs, const marco_msgs__msg__LaneOffset__Sequence * rhs);

/// Copy an array of msg/LaneOffset messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__LaneOffset__Sequence__copy(
  const marco_msgs__msg__LaneOffset__Sequence * input,
  marco_msgs__msg__LaneOffset__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__MSG__DETAIL__LANE_OFFSET__FUNCTIONS_H_
