// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from marco_msgs:msg/QrDetection.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__MSG__DETAIL__QR_DETECTION__FUNCTIONS_H_
#define MARCO_MSGS__MSG__DETAIL__QR_DETECTION__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "marco_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "marco_msgs/msg/detail/qr_detection__struct.h"

/// Initialize msg/QrDetection message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * marco_msgs__msg__QrDetection
 * )) before or use
 * marco_msgs__msg__QrDetection__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__QrDetection__init(marco_msgs__msg__QrDetection * msg);

/// Finalize msg/QrDetection message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__QrDetection__fini(marco_msgs__msg__QrDetection * msg);

/// Create msg/QrDetection message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * marco_msgs__msg__QrDetection__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
marco_msgs__msg__QrDetection *
marco_msgs__msg__QrDetection__create();

/// Destroy msg/QrDetection message.
/**
 * It calls
 * marco_msgs__msg__QrDetection__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__QrDetection__destroy(marco_msgs__msg__QrDetection * msg);

/// Check for msg/QrDetection message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__QrDetection__are_equal(const marco_msgs__msg__QrDetection * lhs, const marco_msgs__msg__QrDetection * rhs);

/// Copy a msg/QrDetection message.
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
marco_msgs__msg__QrDetection__copy(
  const marco_msgs__msg__QrDetection * input,
  marco_msgs__msg__QrDetection * output);

/// Initialize array of msg/QrDetection messages.
/**
 * It allocates the memory for the number of elements and calls
 * marco_msgs__msg__QrDetection__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__QrDetection__Sequence__init(marco_msgs__msg__QrDetection__Sequence * array, size_t size);

/// Finalize array of msg/QrDetection messages.
/**
 * It calls
 * marco_msgs__msg__QrDetection__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__QrDetection__Sequence__fini(marco_msgs__msg__QrDetection__Sequence * array);

/// Create array of msg/QrDetection messages.
/**
 * It allocates the memory for the array and calls
 * marco_msgs__msg__QrDetection__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
marco_msgs__msg__QrDetection__Sequence *
marco_msgs__msg__QrDetection__Sequence__create(size_t size);

/// Destroy array of msg/QrDetection messages.
/**
 * It calls
 * marco_msgs__msg__QrDetection__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
void
marco_msgs__msg__QrDetection__Sequence__destroy(marco_msgs__msg__QrDetection__Sequence * array);

/// Check for msg/QrDetection message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_marco_msgs
bool
marco_msgs__msg__QrDetection__Sequence__are_equal(const marco_msgs__msg__QrDetection__Sequence * lhs, const marco_msgs__msg__QrDetection__Sequence * rhs);

/// Copy an array of msg/QrDetection messages.
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
marco_msgs__msg__QrDetection__Sequence__copy(
  const marco_msgs__msg__QrDetection__Sequence * input,
  marco_msgs__msg__QrDetection__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MARCO_MSGS__MSG__DETAIL__QR_DETECTION__FUNCTIONS_H_
