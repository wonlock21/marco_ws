# generated from rosidl_generator_py/resource/_idl.py.em
# with input from marco_msgs:msg/RobotStatus.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_RobotStatus(type):
    """Metaclass of message 'RobotStatus'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'STATE_IDLE': 0,
        'STATE_TASK_RECEIVED': 1,
        'STATE_MOVING_UNLOADED': 2,
        'STATE_MOVING_LOADED': 3,
        'STATE_WAITING_PLC': 4,
        'STATE_RETURNING': 5,
        'STATE_ERROR': 6,
        'STATE_ESTOP': 7,
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
                'marco_msgs.msg.RobotStatus')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__robot_status
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__robot_status
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__robot_status
            cls._TYPE_SUPPORT = module.type_support_msg__msg__robot_status
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__robot_status

            from geometry_msgs.msg import PoseWithCovarianceStamped
            if PoseWithCovarianceStamped.__class__._TYPE_SUPPORT is None:
                PoseWithCovarianceStamped.__class__.__import_type_support__()

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'STATE_IDLE': cls.__constants['STATE_IDLE'],
            'STATE_TASK_RECEIVED': cls.__constants['STATE_TASK_RECEIVED'],
            'STATE_MOVING_UNLOADED': cls.__constants['STATE_MOVING_UNLOADED'],
            'STATE_MOVING_LOADED': cls.__constants['STATE_MOVING_LOADED'],
            'STATE_WAITING_PLC': cls.__constants['STATE_WAITING_PLC'],
            'STATE_RETURNING': cls.__constants['STATE_RETURNING'],
            'STATE_ERROR': cls.__constants['STATE_ERROR'],
            'STATE_ESTOP': cls.__constants['STATE_ESTOP'],
        }

    @property
    def STATE_IDLE(self):
        """Message constant 'STATE_IDLE'."""
        return Metaclass_RobotStatus.__constants['STATE_IDLE']

    @property
    def STATE_TASK_RECEIVED(self):
        """Message constant 'STATE_TASK_RECEIVED'."""
        return Metaclass_RobotStatus.__constants['STATE_TASK_RECEIVED']

    @property
    def STATE_MOVING_UNLOADED(self):
        """Message constant 'STATE_MOVING_UNLOADED'."""
        return Metaclass_RobotStatus.__constants['STATE_MOVING_UNLOADED']

    @property
    def STATE_MOVING_LOADED(self):
        """Message constant 'STATE_MOVING_LOADED'."""
        return Metaclass_RobotStatus.__constants['STATE_MOVING_LOADED']

    @property
    def STATE_WAITING_PLC(self):
        """Message constant 'STATE_WAITING_PLC'."""
        return Metaclass_RobotStatus.__constants['STATE_WAITING_PLC']

    @property
    def STATE_RETURNING(self):
        """Message constant 'STATE_RETURNING'."""
        return Metaclass_RobotStatus.__constants['STATE_RETURNING']

    @property
    def STATE_ERROR(self):
        """Message constant 'STATE_ERROR'."""
        return Metaclass_RobotStatus.__constants['STATE_ERROR']

    @property
    def STATE_ESTOP(self):
        """Message constant 'STATE_ESTOP'."""
        return Metaclass_RobotStatus.__constants['STATE_ESTOP']


class RobotStatus(metaclass=Metaclass_RobotStatus):
    """
    Message class 'RobotStatus'.

    Constants:
      STATE_IDLE
      STATE_TASK_RECEIVED
      STATE_MOVING_UNLOADED
      STATE_MOVING_LOADED
      STATE_WAITING_PLC
      STATE_RETURNING
      STATE_ERROR
      STATE_ESTOP
    """

    __slots__ = [
        '_header',
        '_mission_state',
        '_manual_mode_enabled',
        '_estop_active',
        '_pose',
        '_localization_valid',
        '_position_covariance',
        '_current_route_edge',
        '_next_node',
        '_cross_track_error',
        '_obstacle_detected',
        '_task_id',
        '_pickup_node',
        '_dropoff_node',
        '_last_qr_data',
        '_plc_connected',
        '_gate_permission_granted',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'mission_state': 'uint8',
        'manual_mode_enabled': 'boolean',
        'estop_active': 'boolean',
        'pose': 'geometry_msgs/PoseWithCovarianceStamped',
        'localization_valid': 'boolean',
        'position_covariance': 'float',
        'current_route_edge': 'string',
        'next_node': 'string',
        'cross_track_error': 'float',
        'obstacle_detected': 'boolean',
        'task_id': 'string',
        'pickup_node': 'string',
        'dropoff_node': 'string',
        'last_qr_data': 'string',
        'plc_connected': 'boolean',
        'gate_permission_granted': 'boolean',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['geometry_msgs', 'msg'], 'PoseWithCovarianceStamped'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.mission_state = kwargs.get('mission_state', int())
        self.manual_mode_enabled = kwargs.get('manual_mode_enabled', bool())
        self.estop_active = kwargs.get('estop_active', bool())
        from geometry_msgs.msg import PoseWithCovarianceStamped
        self.pose = kwargs.get('pose', PoseWithCovarianceStamped())
        self.localization_valid = kwargs.get('localization_valid', bool())
        self.position_covariance = kwargs.get('position_covariance', float())
        self.current_route_edge = kwargs.get('current_route_edge', str())
        self.next_node = kwargs.get('next_node', str())
        self.cross_track_error = kwargs.get('cross_track_error', float())
        self.obstacle_detected = kwargs.get('obstacle_detected', bool())
        self.task_id = kwargs.get('task_id', str())
        self.pickup_node = kwargs.get('pickup_node', str())
        self.dropoff_node = kwargs.get('dropoff_node', str())
        self.last_qr_data = kwargs.get('last_qr_data', str())
        self.plc_connected = kwargs.get('plc_connected', bool())
        self.gate_permission_granted = kwargs.get('gate_permission_granted', bool())

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
        if self.header != other.header:
            return False
        if self.mission_state != other.mission_state:
            return False
        if self.manual_mode_enabled != other.manual_mode_enabled:
            return False
        if self.estop_active != other.estop_active:
            return False
        if self.pose != other.pose:
            return False
        if self.localization_valid != other.localization_valid:
            return False
        if self.position_covariance != other.position_covariance:
            return False
        if self.current_route_edge != other.current_route_edge:
            return False
        if self.next_node != other.next_node:
            return False
        if self.cross_track_error != other.cross_track_error:
            return False
        if self.obstacle_detected != other.obstacle_detected:
            return False
        if self.task_id != other.task_id:
            return False
        if self.pickup_node != other.pickup_node:
            return False
        if self.dropoff_node != other.dropoff_node:
            return False
        if self.last_qr_data != other.last_qr_data:
            return False
        if self.plc_connected != other.plc_connected:
            return False
        if self.gate_permission_granted != other.gate_permission_granted:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def mission_state(self):
        """Message field 'mission_state'."""
        return self._mission_state

    @mission_state.setter
    def mission_state(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'mission_state' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'mission_state' field must be an unsigned integer in [0, 255]"
        self._mission_state = value

    @builtins.property
    def manual_mode_enabled(self):
        """Message field 'manual_mode_enabled'."""
        return self._manual_mode_enabled

    @manual_mode_enabled.setter
    def manual_mode_enabled(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'manual_mode_enabled' field must be of type 'bool'"
        self._manual_mode_enabled = value

    @builtins.property
    def estop_active(self):
        """Message field 'estop_active'."""
        return self._estop_active

    @estop_active.setter
    def estop_active(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'estop_active' field must be of type 'bool'"
        self._estop_active = value

    @builtins.property
    def pose(self):
        """Message field 'pose'."""
        return self._pose

    @pose.setter
    def pose(self, value):
        if __debug__:
            from geometry_msgs.msg import PoseWithCovarianceStamped
            assert \
                isinstance(value, PoseWithCovarianceStamped), \
                "The 'pose' field must be a sub message of type 'PoseWithCovarianceStamped'"
        self._pose = value

    @builtins.property
    def localization_valid(self):
        """Message field 'localization_valid'."""
        return self._localization_valid

    @localization_valid.setter
    def localization_valid(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'localization_valid' field must be of type 'bool'"
        self._localization_valid = value

    @builtins.property
    def position_covariance(self):
        """Message field 'position_covariance'."""
        return self._position_covariance

    @position_covariance.setter
    def position_covariance(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_covariance' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'position_covariance' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._position_covariance = value

    @builtins.property
    def current_route_edge(self):
        """Message field 'current_route_edge'."""
        return self._current_route_edge

    @current_route_edge.setter
    def current_route_edge(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'current_route_edge' field must be of type 'str'"
        self._current_route_edge = value

    @builtins.property
    def next_node(self):
        """Message field 'next_node'."""
        return self._next_node

    @next_node.setter
    def next_node(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'next_node' field must be of type 'str'"
        self._next_node = value

    @builtins.property
    def cross_track_error(self):
        """Message field 'cross_track_error'."""
        return self._cross_track_error

    @cross_track_error.setter
    def cross_track_error(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'cross_track_error' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'cross_track_error' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._cross_track_error = value

    @builtins.property
    def obstacle_detected(self):
        """Message field 'obstacle_detected'."""
        return self._obstacle_detected

    @obstacle_detected.setter
    def obstacle_detected(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'obstacle_detected' field must be of type 'bool'"
        self._obstacle_detected = value

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
    def last_qr_data(self):
        """Message field 'last_qr_data'."""
        return self._last_qr_data

    @last_qr_data.setter
    def last_qr_data(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'last_qr_data' field must be of type 'str'"
        self._last_qr_data = value

    @builtins.property
    def plc_connected(self):
        """Message field 'plc_connected'."""
        return self._plc_connected

    @plc_connected.setter
    def plc_connected(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'plc_connected' field must be of type 'bool'"
        self._plc_connected = value

    @builtins.property
    def gate_permission_granted(self):
        """Message field 'gate_permission_granted'."""
        return self._gate_permission_granted

    @gate_permission_granted.setter
    def gate_permission_granted(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'gate_permission_granted' field must be of type 'bool'"
        self._gate_permission_granted = value
