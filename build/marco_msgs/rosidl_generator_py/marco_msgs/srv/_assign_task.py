# generated from rosidl_generator_py/resource/_idl.py.em
# with input from marco_msgs:srv/AssignTask.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_AssignTask_Request(type):
    """Metaclass of message 'AssignTask_Request'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('marco_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'marco_msgs.srv.AssignTask_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__assign_task__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__assign_task__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__assign_task__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__assign_task__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__assign_task__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class AssignTask_Request(metaclass=Metaclass_AssignTask_Request):
    """Message class 'AssignTask_Request'."""

    __slots__ = [
    ]

    _fields_and_field_types = {
    }

    SLOT_TYPES = (
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)


# Import statements for member types

import builtins  # noqa: E402, I100

# already imported above
# import rosidl_parser.definition


class Metaclass_AssignTask_Response(type):
    """Metaclass of message 'AssignTask_Response'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('marco_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'marco_msgs.srv.AssignTask_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__assign_task__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__assign_task__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__assign_task__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__assign_task__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__assign_task__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class AssignTask_Response(metaclass=Metaclass_AssignTask_Response):
    """Message class 'AssignTask_Response'."""

    __slots__ = [
        '_success',
        '_task_id',
        '_pickup_node',
        '_dropoff_node',
        '_message',
    ]

    _fields_and_field_types = {
        'success': 'boolean',
        'task_id': 'string',
        'pickup_node': 'string',
        'dropoff_node': 'string',
        'message': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.success = kwargs.get('success', bool())
        self.task_id = kwargs.get('task_id', str())
        self.pickup_node = kwargs.get('pickup_node', str())
        self.dropoff_node = kwargs.get('dropoff_node', str())
        self.message = kwargs.get('message', str())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.success != other.success:
            return False
        if self.task_id != other.task_id:
            return False
        if self.pickup_node != other.pickup_node:
            return False
        if self.dropoff_node != other.dropoff_node:
            return False
        if self.message != other.message:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def success(self):
        """Message field 'success'."""
        return self._success

    @success.setter
    def success(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'success' field must be of type 'bool'"
        self._success = value

    @builtins.property
    def task_id(self):
        """Message field 'task_id'."""
        return self._task_id

    @task_id.setter
    def task_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'task_id' field must be of type 'str'"
        self._task_id = value

    @builtins.property
    def pickup_node(self):
        """Message field 'pickup_node'."""
        return self._pickup_node

    @pickup_node.setter
    def pickup_node(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'pickup_node' field must be of type 'str'"
        self._pickup_node = value

    @builtins.property
    def dropoff_node(self):
        """Message field 'dropoff_node'."""
        return self._dropoff_node

    @dropoff_node.setter
    def dropoff_node(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'dropoff_node' field must be of type 'str'"
        self._dropoff_node = value

    @builtins.property
    def message(self):
        """Message field 'message'."""
        return self._message

    @message.setter
    def message(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'message' field must be of type 'str'"
        self._message = value


class Metaclass_AssignTask(type):
    """Metaclass of service 'AssignTask'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('marco_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'marco_msgs.srv.AssignTask')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__assign_task

            from marco_msgs.srv import _assign_task
            if _assign_task.Metaclass_AssignTask_Request._TYPE_SUPPORT is None:
                _assign_task.Metaclass_AssignTask_Request.__import_type_support__()
            if _assign_task.Metaclass_AssignTask_Response._TYPE_SUPPORT is None:
                _assign_task.Metaclass_AssignTask_Response.__import_type_support__()


class AssignTask(metaclass=Metaclass_AssignTask):
    from marco_msgs.srv._assign_task import AssignTask_Request as Request
    from marco_msgs.srv._assign_task import AssignTask_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
