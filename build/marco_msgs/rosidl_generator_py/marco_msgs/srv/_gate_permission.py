# generated from rosidl_generator_py/resource/_idl.py.em
# with input from marco_msgs:srv/GatePermission.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_GatePermission_Request(type):
    """Metaclass of message 'GatePermission_Request'."""

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
                'marco_msgs.srv.GatePermission_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__gate_permission__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__gate_permission__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__gate_permission__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__gate_permission__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__gate_permission__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GatePermission_Request(metaclass=Metaclass_GatePermission_Request):
    """Message class 'GatePermission_Request'."""

    __slots__ = [
        '_node_id',
    ]

    _fields_and_field_types = {
        'node_id': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.node_id = kwargs.get('node_id', str())

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
        if self.node_id != other.node_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def node_id(self):
        """Message field 'node_id'."""
        return self._node_id

    @node_id.setter
    def node_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'node_id' field must be of type 'str'"
        self._node_id = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_GatePermission_Response(type):
    """Metaclass of message 'GatePermission_Response'."""

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
                'marco_msgs.srv.GatePermission_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__gate_permission__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__gate_permission__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__gate_permission__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__gate_permission__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__gate_permission__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GatePermission_Response(metaclass=Metaclass_GatePermission_Response):
    """Message class 'GatePermission_Response'."""

    __slots__ = [
        '_granted',
        '_message',
    ]

    _fields_and_field_types = {
        'granted': 'boolean',
        'message': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.granted = kwargs.get('granted', bool())
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
        if self.granted != other.granted:
            return False
        if self.message != other.message:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def granted(self):
        """Message field 'granted'."""
        return self._granted

    @granted.setter
    def granted(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'granted' field must be of type 'bool'"
        self._granted = value

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


class Metaclass_GatePermission(type):
    """Metaclass of service 'GatePermission'."""

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
                'marco_msgs.srv.GatePermission')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__gate_permission

            from marco_msgs.srv import _gate_permission
            if _gate_permission.Metaclass_GatePermission_Request._TYPE_SUPPORT is None:
                _gate_permission.Metaclass_GatePermission_Request.__import_type_support__()
            if _gate_permission.Metaclass_GatePermission_Response._TYPE_SUPPORT is None:
                _gate_permission.Metaclass_GatePermission_Response.__import_type_support__()


class GatePermission(metaclass=Metaclass_GatePermission):
    from marco_msgs.srv._gate_permission import GatePermission_Request as Request
    from marco_msgs.srv._gate_permission import GatePermission_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
