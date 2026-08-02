// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from marco_msgs:msg/RobotStatus.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "marco_msgs/msg/detail/robot_status__struct.h"
#include "marco_msgs/msg/detail/robot_status__functions.h"

#include "rosidl_runtime_c/string.h"
#include "rosidl_runtime_c/string_functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool std_msgs__msg__header__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * std_msgs__msg__header__convert_to_py(void * raw_ros_message);
ROSIDL_GENERATOR_C_IMPORT
bool geometry_msgs__msg__pose_with_covariance_stamped__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * geometry_msgs__msg__pose_with_covariance_stamped__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool marco_msgs__msg__robot_status__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[41];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("marco_msgs.msg._robot_status.RobotStatus", full_classname_dest, 40) == 0);
  }
  marco_msgs__msg__RobotStatus * ros_message = _ros_message;
  {  // header
    PyObject * field = PyObject_GetAttrString(_pymsg, "header");
    if (!field) {
      return false;
    }
    if (!std_msgs__msg__header__convert_from_py(field, &ros_message->header)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // mission_state
    PyObject * field = PyObject_GetAttrString(_pymsg, "mission_state");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->mission_state = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // manual_mode_enabled
    PyObject * field = PyObject_GetAttrString(_pymsg, "manual_mode_enabled");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->manual_mode_enabled = (Py_True == field);
    Py_DECREF(field);
  }
  {  // estop_active
    PyObject * field = PyObject_GetAttrString(_pymsg, "estop_active");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->estop_active = (Py_True == field);
    Py_DECREF(field);
  }
  {  // pose
    PyObject * field = PyObject_GetAttrString(_pymsg, "pose");
    if (!field) {
      return false;
    }
    if (!geometry_msgs__msg__pose_with_covariance_stamped__convert_from_py(field, &ros_message->pose)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // localization_valid
    PyObject * field = PyObject_GetAttrString(_pymsg, "localization_valid");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->localization_valid = (Py_True == field);
    Py_DECREF(field);
  }
  {  // position_covariance
    PyObject * field = PyObject_GetAttrString(_pymsg, "position_covariance");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->position_covariance = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // current_route_edge
    PyObject * field = PyObject_GetAttrString(_pymsg, "current_route_edge");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->current_route_edge, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // next_node
    PyObject * field = PyObject_GetAttrString(_pymsg, "next_node");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->next_node, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // cross_track_error
    PyObject * field = PyObject_GetAttrString(_pymsg, "cross_track_error");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->cross_track_error = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // obstacle_detected
    PyObject * field = PyObject_GetAttrString(_pymsg, "obstacle_detected");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->obstacle_detected = (Py_True == field);
    Py_DECREF(field);
  }
  {  // task_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "task_id");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->task_id, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // pickup_node
    PyObject * field = PyObject_GetAttrString(_pymsg, "pickup_node");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->pickup_node, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // dropoff_node
    PyObject * field = PyObject_GetAttrString(_pymsg, "dropoff_node");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->dropoff_node, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // last_qr_data
    PyObject * field = PyObject_GetAttrString(_pymsg, "last_qr_data");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->last_qr_data, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // plc_connected
    PyObject * field = PyObject_GetAttrString(_pymsg, "plc_connected");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->plc_connected = (Py_True == field);
    Py_DECREF(field);
  }
  {  // gate_permission_granted
    PyObject * field = PyObject_GetAttrString(_pymsg, "gate_permission_granted");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->gate_permission_granted = (Py_True == field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * marco_msgs__msg__robot_status__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of RobotStatus */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("marco_msgs.msg._robot_status");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "RobotStatus");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  marco_msgs__msg__RobotStatus * ros_message = (marco_msgs__msg__RobotStatus *)raw_ros_message;
  {  // header
    PyObject * field = NULL;
    field = std_msgs__msg__header__convert_to_py(&ros_message->header);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "header", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // mission_state
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->mission_state);
    {
      int rc = PyObject_SetAttrString(_pymessage, "mission_state", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // manual_mode_enabled
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->manual_mode_enabled ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "manual_mode_enabled", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // estop_active
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->estop_active ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "estop_active", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // pose
    PyObject * field = NULL;
    field = geometry_msgs__msg__pose_with_covariance_stamped__convert_to_py(&ros_message->pose);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "pose", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // localization_valid
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->localization_valid ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "localization_valid", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // position_covariance
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->position_covariance);
    {
      int rc = PyObject_SetAttrString(_pymessage, "position_covariance", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // current_route_edge
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->current_route_edge.data,
      strlen(ros_message->current_route_edge.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "current_route_edge", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // next_node
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->next_node.data,
      strlen(ros_message->next_node.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "next_node", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // cross_track_error
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->cross_track_error);
    {
      int rc = PyObject_SetAttrString(_pymessage, "cross_track_error", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // obstacle_detected
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->obstacle_detected ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "obstacle_detected", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // task_id
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->task_id.data,
      strlen(ros_message->task_id.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "task_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // pickup_node
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->pickup_node.data,
      strlen(ros_message->pickup_node.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "pickup_node", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dropoff_node
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->dropoff_node.data,
      strlen(ros_message->dropoff_node.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "dropoff_node", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // last_qr_data
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->last_qr_data.data,
      strlen(ros_message->last_qr_data.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "last_qr_data", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // plc_connected
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->plc_connected ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "plc_connected", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gate_permission_granted
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->gate_permission_granted ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gate_permission_granted", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
