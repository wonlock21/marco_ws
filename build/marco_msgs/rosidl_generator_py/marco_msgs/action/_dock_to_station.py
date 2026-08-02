# generated from rosidl_generator_py/resource/_idl.py.em
# with input from marco_msgs:action/DockToStation.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_DockToStation_Goal(type):
    """Metaclass of message 'DockToStation_Goal'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'APPROACH_PICKUP': 0,
        'APPROACH_DROPOFF': 1,
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
                'marco_msgs.action.DockToStation_Goal')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__goal
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__goal
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__goal
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__goal
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__goal

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'APPROACH_PICKUP': cls.__constants['APPROACH_PICKUP'],
            'APPROACH_DROPOFF': cls.__constants['APPROACH_DROPOFF'],
        }

    @property
    def APPROACH_PICKUP(self):
        """Message constant 'APPROACH_PICKUP'."""
        return Metaclass_DockToStation_Goal.__constants['APPROACH_PICKUP']

    @property
    def APPROACH_DROPOFF(self):
        """Message constant 'APPROACH_DROPOFF'."""
        return Metaclass_DockToStation_Goal.__constants['APPROACH_DROPOFF']


class DockToStation_Goal(metaclass=Metaclass_DockToStation_Goal):
    """
    Message class 'DockToStation_Goal'.

    Constants:
      APPROACH_PICKUP
      APPROACH_DROPOFF
    """

    __slots__ = [
        '_station_id',
        '_position_tolerance',
        '_yaw_tolerance',
        '_approach_type',
        '_timeout',
    ]

    _fields_and_field_types = {
        'station_id': 'string',
        'position_tolerance': 'float',
        'yaw_tolerance': 'float',
        'approach_type': 'uint8',
        'timeout': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.station_id = kwargs.get('station_id', str())
        self.position_tolerance = kwargs.get('position_tolerance', float())
        self.yaw_tolerance = kwargs.get('yaw_tolerance', float())
        self.approach_type = kwargs.get('approach_type', int())
        self.timeout = kwargs.get('timeout', float())

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
        if self.station_id != other.station_id:
            return False
        if self.position_tolerance != other.position_tolerance:
            return False
        if self.yaw_tolerance != other.yaw_tolerance:
            return False
        if self.approach_type != other.approach_type:
            return False
        if self.timeout != other.timeout:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def station_id(self):
        """Message field 'station_id'."""
        return self._station_id

    @station_id.setter
    def station_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'station_id' field must be of type 'str'"
        self._station_id = value

    @builtins.property
    def position_tolerance(self):
        """Message field 'position_tolerance'."""
        return self._position_tolerance

    @position_tolerance.setter
    def position_tolerance(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_tolerance' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'position_tolerance' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._position_tolerance = value

    @builtins.property
    def yaw_tolerance(self):
        """Message field 'yaw_tolerance'."""
        return self._yaw_tolerance

    @yaw_tolerance.setter
    def yaw_tolerance(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'yaw_tolerance' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'yaw_tolerance' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._yaw_tolerance = value

    @builtins.property
    def approach_type(self):
        """Message field 'approach_type'."""
        return self._approach_type

    @approach_type.setter
    def approach_type(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'approach_type' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'approach_type' field must be an unsigned integer in [0, 255]"
        self._approach_type = value

    @builtins.property
    def timeout(self):
        """Message field 'timeout'."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'timeout' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'timeout' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._timeout = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import math

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_Result(type):
    """Metaclass of message 'DockToStation_Result'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'RESULT_OK': 0,
        'RESULT_QR_MISMATCH': 1,
        'RESULT_LANE_LOST': 2,
        'RESULT_TIMEOUT': 3,
        'RESULT_OBSTACLE': 4,
        'RESULT_ABORTED': 5,
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
                'marco_msgs.action.DockToStation_Result')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__result
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__result
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__result
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__result
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__result

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'RESULT_OK': cls.__constants['RESULT_OK'],
            'RESULT_QR_MISMATCH': cls.__constants['RESULT_QR_MISMATCH'],
            'RESULT_LANE_LOST': cls.__constants['RESULT_LANE_LOST'],
            'RESULT_TIMEOUT': cls.__constants['RESULT_TIMEOUT'],
            'RESULT_OBSTACLE': cls.__constants['RESULT_OBSTACLE'],
            'RESULT_ABORTED': cls.__constants['RESULT_ABORTED'],
        }

    @property
    def RESULT_OK(self):
        """Message constant 'RESULT_OK'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_OK']

    @property
    def RESULT_QR_MISMATCH(self):
        """Message constant 'RESULT_QR_MISMATCH'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_QR_MISMATCH']

    @property
    def RESULT_LANE_LOST(self):
        """Message constant 'RESULT_LANE_LOST'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_LANE_LOST']

    @property
    def RESULT_TIMEOUT(self):
        """Message constant 'RESULT_TIMEOUT'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_TIMEOUT']

    @property
    def RESULT_OBSTACLE(self):
        """Message constant 'RESULT_OBSTACLE'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_OBSTACLE']

    @property
    def RESULT_ABORTED(self):
        """Message constant 'RESULT_ABORTED'."""
        return Metaclass_DockToStation_Result.__constants['RESULT_ABORTED']


class DockToStation_Result(metaclass=Metaclass_DockToStation_Result):
    """
    Message class 'DockToStation_Result'.

    Constants:
      RESULT_OK
      RESULT_QR_MISMATCH
      RESULT_LANE_LOST
      RESULT_TIMEOUT
      RESULT_OBSTACLE
      RESULT_ABORTED
    """

    __slots__ = [
        '_success',
        '_final_position_error',
        '_final_yaw_error',
        '_result_code',
        '_message',
    ]

    _fields_and_field_types = {
        'success': 'boolean',
        'final_position_error': 'float',
        'final_yaw_error': 'float',
        'result_code': 'uint8',
        'message': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.success = kwargs.get('success', bool())
        self.final_position_error = kwargs.get('final_position_error', float())
        self.final_yaw_error = kwargs.get('final_yaw_error', float())
        self.result_code = kwargs.get('result_code', int())
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
        if self.final_position_error != other.final_position_error:
            return False
        if self.final_yaw_error != other.final_yaw_error:
            return False
        if self.result_code != other.result_code:
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
    def final_position_error(self):
        """Message field 'final_position_error'."""
        return self._final_position_error

    @final_position_error.setter
    def final_position_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'final_position_error' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'final_position_error' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._final_position_error = value

    @builtins.property
    def final_yaw_error(self):
        """Message field 'final_yaw_error'."""
        return self._final_yaw_error

    @final_yaw_error.setter
    def final_yaw_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'final_yaw_error' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'final_yaw_error' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._final_yaw_error = value

    @builtins.property
    def result_code(self):
        """Message field 'result_code'."""
        return self._result_code

    @result_code.setter
    def result_code(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'result_code' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'result_code' field must be an unsigned integer in [0, 255]"
        self._result_code = value

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


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import math

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_Feedback(type):
    """Metaclass of message 'DockToStation_Feedback'."""

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
                'marco_msgs.action.DockToStation_Feedback')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__feedback
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__feedback
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__feedback
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__feedback
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__feedback

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_Feedback(metaclass=Metaclass_DockToStation_Feedback):
    """Message class 'DockToStation_Feedback'."""

    __slots__ = [
        '_phase',
        '_position_error',
        '_yaw_error',
        '_distance_remaining',
    ]

    _fields_and_field_types = {
        'phase': 'string',
        'position_error': 'float',
        'yaw_error': 'float',
        'distance_remaining': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.phase = kwargs.get('phase', str())
        self.position_error = kwargs.get('position_error', float())
        self.yaw_error = kwargs.get('yaw_error', float())
        self.distance_remaining = kwargs.get('distance_remaining', float())

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
        if self.phase != other.phase:
            return False
        if self.position_error != other.position_error:
            return False
        if self.yaw_error != other.yaw_error:
            return False
        if self.distance_remaining != other.distance_remaining:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def phase(self):
        """Message field 'phase'."""
        return self._phase

    @phase.setter
    def phase(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'phase' field must be of type 'str'"
        self._phase = value

    @builtins.property
    def position_error(self):
        """Message field 'position_error'."""
        return self._position_error

    @position_error.setter
    def position_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_error' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'position_error' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._position_error = value

    @builtins.property
    def yaw_error(self):
        """Message field 'yaw_error'."""
        return self._yaw_error

    @yaw_error.setter
    def yaw_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'yaw_error' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'yaw_error' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._yaw_error = value

    @builtins.property
    def distance_remaining(self):
        """Message field 'distance_remaining'."""
        return self._distance_remaining

    @distance_remaining.setter
    def distance_remaining(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'distance_remaining' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'distance_remaining' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._distance_remaining = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_SendGoal_Request(type):
    """Metaclass of message 'DockToStation_SendGoal_Request'."""

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
                'marco_msgs.action.DockToStation_SendGoal_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__send_goal__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__send_goal__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__send_goal__request
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__send_goal__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__send_goal__request

            from marco_msgs.action import DockToStation
            if DockToStation.Goal.__class__._TYPE_SUPPORT is None:
                DockToStation.Goal.__class__.__import_type_support__()

            from unique_identifier_msgs.msg import UUID
            if UUID.__class__._TYPE_SUPPORT is None:
                UUID.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_SendGoal_Request(metaclass=Metaclass_DockToStation_SendGoal_Request):
    """Message class 'DockToStation_SendGoal_Request'."""

    __slots__ = [
        '_goal_id',
        '_goal',
    ]

    _fields_and_field_types = {
        'goal_id': 'unique_identifier_msgs/UUID',
        'goal': 'marco_msgs/DockToStation_Goal',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['unique_identifier_msgs', 'msg'], 'UUID'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['marco_msgs', 'action'], 'DockToStation_Goal'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from unique_identifier_msgs.msg import UUID
        self.goal_id = kwargs.get('goal_id', UUID())
        from marco_msgs.action._dock_to_station import DockToStation_Goal
        self.goal = kwargs.get('goal', DockToStation_Goal())

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
        if self.goal_id != other.goal_id:
            return False
        if self.goal != other.goal:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def goal_id(self):
        """Message field 'goal_id'."""
        return self._goal_id

    @goal_id.setter
    def goal_id(self, value):
        if __debug__:
            from unique_identifier_msgs.msg import UUID
            assert \
                isinstance(value, UUID), \
                "The 'goal_id' field must be a sub message of type 'UUID'"
        self._goal_id = value

    @builtins.property
    def goal(self):
        """Message field 'goal'."""
        return self._goal

    @goal.setter
    def goal(self, value):
        if __debug__:
            from marco_msgs.action._dock_to_station import DockToStation_Goal
            assert \
                isinstance(value, DockToStation_Goal), \
                "The 'goal' field must be a sub message of type 'DockToStation_Goal'"
        self._goal = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_SendGoal_Response(type):
    """Metaclass of message 'DockToStation_SendGoal_Response'."""

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
                'marco_msgs.action.DockToStation_SendGoal_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__send_goal__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__send_goal__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__send_goal__response
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__send_goal__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__send_goal__response

            from builtin_interfaces.msg import Time
            if Time.__class__._TYPE_SUPPORT is None:
                Time.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_SendGoal_Response(metaclass=Metaclass_DockToStation_SendGoal_Response):
    """Message class 'DockToStation_SendGoal_Response'."""

    __slots__ = [
        '_accepted',
        '_stamp',
    ]

    _fields_and_field_types = {
        'accepted': 'boolean',
        'stamp': 'builtin_interfaces/Time',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.accepted = kwargs.get('accepted', bool())
        from builtin_interfaces.msg import Time
        self.stamp = kwargs.get('stamp', Time())

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
        if self.accepted != other.accepted:
            return False
        if self.stamp != other.stamp:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def accepted(self):
        """Message field 'accepted'."""
        return self._accepted

    @accepted.setter
    def accepted(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'accepted' field must be of type 'bool'"
        self._accepted = value

    @builtins.property
    def stamp(self):
        """Message field 'stamp'."""
        return self._stamp

    @stamp.setter
    def stamp(self, value):
        if __debug__:
            from builtin_interfaces.msg import Time
            assert \
                isinstance(value, Time), \
                "The 'stamp' field must be a sub message of type 'Time'"
        self._stamp = value


class Metaclass_DockToStation_SendGoal(type):
    """Metaclass of service 'DockToStation_SendGoal'."""

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
                'marco_msgs.action.DockToStation_SendGoal')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__action__dock_to_station__send_goal

            from marco_msgs.action import _dock_to_station
            if _dock_to_station.Metaclass_DockToStation_SendGoal_Request._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_SendGoal_Request.__import_type_support__()
            if _dock_to_station.Metaclass_DockToStation_SendGoal_Response._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_SendGoal_Response.__import_type_support__()


class DockToStation_SendGoal(metaclass=Metaclass_DockToStation_SendGoal):
    from marco_msgs.action._dock_to_station import DockToStation_SendGoal_Request as Request
    from marco_msgs.action._dock_to_station import DockToStation_SendGoal_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_GetResult_Request(type):
    """Metaclass of message 'DockToStation_GetResult_Request'."""

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
                'marco_msgs.action.DockToStation_GetResult_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__get_result__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__get_result__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__get_result__request
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__get_result__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__get_result__request

            from unique_identifier_msgs.msg import UUID
            if UUID.__class__._TYPE_SUPPORT is None:
                UUID.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_GetResult_Request(metaclass=Metaclass_DockToStation_GetResult_Request):
    """Message class 'DockToStation_GetResult_Request'."""

    __slots__ = [
        '_goal_id',
    ]

    _fields_and_field_types = {
        'goal_id': 'unique_identifier_msgs/UUID',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['unique_identifier_msgs', 'msg'], 'UUID'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from unique_identifier_msgs.msg import UUID
        self.goal_id = kwargs.get('goal_id', UUID())

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
        if self.goal_id != other.goal_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def goal_id(self):
        """Message field 'goal_id'."""
        return self._goal_id

    @goal_id.setter
    def goal_id(self, value):
        if __debug__:
            from unique_identifier_msgs.msg import UUID
            assert \
                isinstance(value, UUID), \
                "The 'goal_id' field must be a sub message of type 'UUID'"
        self._goal_id = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_GetResult_Response(type):
    """Metaclass of message 'DockToStation_GetResult_Response'."""

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
                'marco_msgs.action.DockToStation_GetResult_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__get_result__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__get_result__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__get_result__response
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__get_result__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__get_result__response

            from marco_msgs.action import DockToStation
            if DockToStation.Result.__class__._TYPE_SUPPORT is None:
                DockToStation.Result.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_GetResult_Response(metaclass=Metaclass_DockToStation_GetResult_Response):
    """Message class 'DockToStation_GetResult_Response'."""

    __slots__ = [
        '_status',
        '_result',
    ]

    _fields_and_field_types = {
        'status': 'int8',
        'result': 'marco_msgs/DockToStation_Result',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['marco_msgs', 'action'], 'DockToStation_Result'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.status = kwargs.get('status', int())
        from marco_msgs.action._dock_to_station import DockToStation_Result
        self.result = kwargs.get('result', DockToStation_Result())

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
        if self.status != other.status:
            return False
        if self.result != other.result:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def status(self):
        """Message field 'status'."""
        return self._status

    @status.setter
    def status(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'status' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'status' field must be an integer in [-128, 127]"
        self._status = value

    @builtins.property
    def result(self):
        """Message field 'result'."""
        return self._result

    @result.setter
    def result(self, value):
        if __debug__:
            from marco_msgs.action._dock_to_station import DockToStation_Result
            assert \
                isinstance(value, DockToStation_Result), \
                "The 'result' field must be a sub message of type 'DockToStation_Result'"
        self._result = value


class Metaclass_DockToStation_GetResult(type):
    """Metaclass of service 'DockToStation_GetResult'."""

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
                'marco_msgs.action.DockToStation_GetResult')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__action__dock_to_station__get_result

            from marco_msgs.action import _dock_to_station
            if _dock_to_station.Metaclass_DockToStation_GetResult_Request._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_GetResult_Request.__import_type_support__()
            if _dock_to_station.Metaclass_DockToStation_GetResult_Response._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_GetResult_Response.__import_type_support__()


class DockToStation_GetResult(metaclass=Metaclass_DockToStation_GetResult):
    from marco_msgs.action._dock_to_station import DockToStation_GetResult_Request as Request
    from marco_msgs.action._dock_to_station import DockToStation_GetResult_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_DockToStation_FeedbackMessage(type):
    """Metaclass of message 'DockToStation_FeedbackMessage'."""

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
                'marco_msgs.action.DockToStation_FeedbackMessage')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__action__dock_to_station__feedback_message
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__action__dock_to_station__feedback_message
            cls._CONVERT_TO_PY = module.convert_to_py_msg__action__dock_to_station__feedback_message
            cls._TYPE_SUPPORT = module.type_support_msg__action__dock_to_station__feedback_message
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__action__dock_to_station__feedback_message

            from marco_msgs.action import DockToStation
            if DockToStation.Feedback.__class__._TYPE_SUPPORT is None:
                DockToStation.Feedback.__class__.__import_type_support__()

            from unique_identifier_msgs.msg import UUID
            if UUID.__class__._TYPE_SUPPORT is None:
                UUID.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class DockToStation_FeedbackMessage(metaclass=Metaclass_DockToStation_FeedbackMessage):
    """Message class 'DockToStation_FeedbackMessage'."""

    __slots__ = [
        '_goal_id',
        '_feedback',
    ]

    _fields_and_field_types = {
        'goal_id': 'unique_identifier_msgs/UUID',
        'feedback': 'marco_msgs/DockToStation_Feedback',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['unique_identifier_msgs', 'msg'], 'UUID'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['marco_msgs', 'action'], 'DockToStation_Feedback'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from unique_identifier_msgs.msg import UUID
        self.goal_id = kwargs.get('goal_id', UUID())
        from marco_msgs.action._dock_to_station import DockToStation_Feedback
        self.feedback = kwargs.get('feedback', DockToStation_Feedback())

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
        if self.goal_id != other.goal_id:
            return False
        if self.feedback != other.feedback:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def goal_id(self):
        """Message field 'goal_id'."""
        return self._goal_id

    @goal_id.setter
    def goal_id(self, value):
        if __debug__:
            from unique_identifier_msgs.msg import UUID
            assert \
                isinstance(value, UUID), \
                "The 'goal_id' field must be a sub message of type 'UUID'"
        self._goal_id = value

    @builtins.property
    def feedback(self):
        """Message field 'feedback'."""
        return self._feedback

    @feedback.setter
    def feedback(self, value):
        if __debug__:
            from marco_msgs.action._dock_to_station import DockToStation_Feedback
            assert \
                isinstance(value, DockToStation_Feedback), \
                "The 'feedback' field must be a sub message of type 'DockToStation_Feedback'"
        self._feedback = value


class Metaclass_DockToStation(type):
    """Metaclass of action 'DockToStation'."""

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
                'marco_msgs.action.DockToStation')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_action__action__dock_to_station

            from action_msgs.msg import _goal_status_array
            if _goal_status_array.Metaclass_GoalStatusArray._TYPE_SUPPORT is None:
                _goal_status_array.Metaclass_GoalStatusArray.__import_type_support__()
            from action_msgs.srv import _cancel_goal
            if _cancel_goal.Metaclass_CancelGoal._TYPE_SUPPORT is None:
                _cancel_goal.Metaclass_CancelGoal.__import_type_support__()

            from marco_msgs.action import _dock_to_station
            if _dock_to_station.Metaclass_DockToStation_SendGoal._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_SendGoal.__import_type_support__()
            if _dock_to_station.Metaclass_DockToStation_GetResult._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_GetResult.__import_type_support__()
            if _dock_to_station.Metaclass_DockToStation_FeedbackMessage._TYPE_SUPPORT is None:
                _dock_to_station.Metaclass_DockToStation_FeedbackMessage.__import_type_support__()


class DockToStation(metaclass=Metaclass_DockToStation):

    # The goal message defined in the action definition.
    from marco_msgs.action._dock_to_station import DockToStation_Goal as Goal
    # The result message defined in the action definition.
    from marco_msgs.action._dock_to_station import DockToStation_Result as Result
    # The feedback message defined in the action definition.
    from marco_msgs.action._dock_to_station import DockToStation_Feedback as Feedback

    class Impl:

        # The send_goal service using a wrapped version of the goal message as a request.
        from marco_msgs.action._dock_to_station import DockToStation_SendGoal as SendGoalService
        # The get_result service using a wrapped version of the result message as a response.
        from marco_msgs.action._dock_to_station import DockToStation_GetResult as GetResultService
        # The feedback message with generic fields which wraps the feedback message.
        from marco_msgs.action._dock_to_station import DockToStation_FeedbackMessage as FeedbackMessage

        # The generic service to cancel a goal.
        from action_msgs.srv._cancel_goal import CancelGoal as CancelGoalService
        # The generic message for get the status of a goal.
        from action_msgs.msg._goal_status_array import GoalStatusArray as GoalStatusMessage

    def __init__(self):
        raise NotImplementedError('Action classes can not be instantiated')
