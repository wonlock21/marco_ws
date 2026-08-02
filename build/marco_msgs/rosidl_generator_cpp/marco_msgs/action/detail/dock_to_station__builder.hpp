// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from marco_msgs:action/DockToStation.idl
// generated code does not contain a copyright notice

#ifndef MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__BUILDER_HPP_
#define MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "marco_msgs/action/detail/dock_to_station__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_Goal_timeout
{
public:
  explicit Init_DockToStation_Goal_timeout(::marco_msgs::action::DockToStation_Goal & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_Goal timeout(::marco_msgs::action::DockToStation_Goal::_timeout_type arg)
  {
    msg_.timeout = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Goal msg_;
};

class Init_DockToStation_Goal_approach_type
{
public:
  explicit Init_DockToStation_Goal_approach_type(::marco_msgs::action::DockToStation_Goal & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Goal_timeout approach_type(::marco_msgs::action::DockToStation_Goal::_approach_type_type arg)
  {
    msg_.approach_type = std::move(arg);
    return Init_DockToStation_Goal_timeout(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Goal msg_;
};

class Init_DockToStation_Goal_yaw_tolerance
{
public:
  explicit Init_DockToStation_Goal_yaw_tolerance(::marco_msgs::action::DockToStation_Goal & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Goal_approach_type yaw_tolerance(::marco_msgs::action::DockToStation_Goal::_yaw_tolerance_type arg)
  {
    msg_.yaw_tolerance = std::move(arg);
    return Init_DockToStation_Goal_approach_type(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Goal msg_;
};

class Init_DockToStation_Goal_position_tolerance
{
public:
  explicit Init_DockToStation_Goal_position_tolerance(::marco_msgs::action::DockToStation_Goal & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Goal_yaw_tolerance position_tolerance(::marco_msgs::action::DockToStation_Goal::_position_tolerance_type arg)
  {
    msg_.position_tolerance = std::move(arg);
    return Init_DockToStation_Goal_yaw_tolerance(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Goal msg_;
};

class Init_DockToStation_Goal_station_id
{
public:
  Init_DockToStation_Goal_station_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_Goal_position_tolerance station_id(::marco_msgs::action::DockToStation_Goal::_station_id_type arg)
  {
    msg_.station_id = std::move(arg);
    return Init_DockToStation_Goal_position_tolerance(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Goal msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_Goal>()
{
  return marco_msgs::action::builder::Init_DockToStation_Goal_station_id();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_Result_message
{
public:
  explicit Init_DockToStation_Result_message(::marco_msgs::action::DockToStation_Result & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_Result message(::marco_msgs::action::DockToStation_Result::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Result msg_;
};

class Init_DockToStation_Result_result_code
{
public:
  explicit Init_DockToStation_Result_result_code(::marco_msgs::action::DockToStation_Result & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Result_message result_code(::marco_msgs::action::DockToStation_Result::_result_code_type arg)
  {
    msg_.result_code = std::move(arg);
    return Init_DockToStation_Result_message(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Result msg_;
};

class Init_DockToStation_Result_final_yaw_error
{
public:
  explicit Init_DockToStation_Result_final_yaw_error(::marco_msgs::action::DockToStation_Result & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Result_result_code final_yaw_error(::marco_msgs::action::DockToStation_Result::_final_yaw_error_type arg)
  {
    msg_.final_yaw_error = std::move(arg);
    return Init_DockToStation_Result_result_code(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Result msg_;
};

class Init_DockToStation_Result_final_position_error
{
public:
  explicit Init_DockToStation_Result_final_position_error(::marco_msgs::action::DockToStation_Result & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Result_final_yaw_error final_position_error(::marco_msgs::action::DockToStation_Result::_final_position_error_type arg)
  {
    msg_.final_position_error = std::move(arg);
    return Init_DockToStation_Result_final_yaw_error(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Result msg_;
};

class Init_DockToStation_Result_success
{
public:
  Init_DockToStation_Result_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_Result_final_position_error success(::marco_msgs::action::DockToStation_Result::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_DockToStation_Result_final_position_error(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_Result>()
{
  return marco_msgs::action::builder::Init_DockToStation_Result_success();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_Feedback_distance_remaining
{
public:
  explicit Init_DockToStation_Feedback_distance_remaining(::marco_msgs::action::DockToStation_Feedback & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_Feedback distance_remaining(::marco_msgs::action::DockToStation_Feedback::_distance_remaining_type arg)
  {
    msg_.distance_remaining = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Feedback msg_;
};

class Init_DockToStation_Feedback_yaw_error
{
public:
  explicit Init_DockToStation_Feedback_yaw_error(::marco_msgs::action::DockToStation_Feedback & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Feedback_distance_remaining yaw_error(::marco_msgs::action::DockToStation_Feedback::_yaw_error_type arg)
  {
    msg_.yaw_error = std::move(arg);
    return Init_DockToStation_Feedback_distance_remaining(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Feedback msg_;
};

class Init_DockToStation_Feedback_position_error
{
public:
  explicit Init_DockToStation_Feedback_position_error(::marco_msgs::action::DockToStation_Feedback & msg)
  : msg_(msg)
  {}
  Init_DockToStation_Feedback_yaw_error position_error(::marco_msgs::action::DockToStation_Feedback::_position_error_type arg)
  {
    msg_.position_error = std::move(arg);
    return Init_DockToStation_Feedback_yaw_error(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Feedback msg_;
};

class Init_DockToStation_Feedback_phase
{
public:
  Init_DockToStation_Feedback_phase()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_Feedback_position_error phase(::marco_msgs::action::DockToStation_Feedback::_phase_type arg)
  {
    msg_.phase = std::move(arg);
    return Init_DockToStation_Feedback_position_error(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_Feedback>()
{
  return marco_msgs::action::builder::Init_DockToStation_Feedback_phase();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_SendGoal_Request_goal
{
public:
  explicit Init_DockToStation_SendGoal_Request_goal(::marco_msgs::action::DockToStation_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_SendGoal_Request goal(::marco_msgs::action::DockToStation_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_SendGoal_Request msg_;
};

class Init_DockToStation_SendGoal_Request_goal_id
{
public:
  Init_DockToStation_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_SendGoal_Request_goal goal_id(::marco_msgs::action::DockToStation_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DockToStation_SendGoal_Request_goal(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_SendGoal_Request>()
{
  return marco_msgs::action::builder::Init_DockToStation_SendGoal_Request_goal_id();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_SendGoal_Response_stamp
{
public:
  explicit Init_DockToStation_SendGoal_Response_stamp(::marco_msgs::action::DockToStation_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_SendGoal_Response stamp(::marco_msgs::action::DockToStation_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_SendGoal_Response msg_;
};

class Init_DockToStation_SendGoal_Response_accepted
{
public:
  Init_DockToStation_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_SendGoal_Response_stamp accepted(::marco_msgs::action::DockToStation_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_DockToStation_SendGoal_Response_stamp(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_SendGoal_Response>()
{
  return marco_msgs::action::builder::Init_DockToStation_SendGoal_Response_accepted();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_GetResult_Request_goal_id
{
public:
  Init_DockToStation_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::marco_msgs::action::DockToStation_GetResult_Request goal_id(::marco_msgs::action::DockToStation_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_GetResult_Request>()
{
  return marco_msgs::action::builder::Init_DockToStation_GetResult_Request_goal_id();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_GetResult_Response_result
{
public:
  explicit Init_DockToStation_GetResult_Response_result(::marco_msgs::action::DockToStation_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_GetResult_Response result(::marco_msgs::action::DockToStation_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_GetResult_Response msg_;
};

class Init_DockToStation_GetResult_Response_status
{
public:
  Init_DockToStation_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_GetResult_Response_result status(::marco_msgs::action::DockToStation_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_DockToStation_GetResult_Response_result(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_GetResult_Response>()
{
  return marco_msgs::action::builder::Init_DockToStation_GetResult_Response_status();
}

}  // namespace marco_msgs


namespace marco_msgs
{

namespace action
{

namespace builder
{

class Init_DockToStation_FeedbackMessage_feedback
{
public:
  explicit Init_DockToStation_FeedbackMessage_feedback(::marco_msgs::action::DockToStation_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::marco_msgs::action::DockToStation_FeedbackMessage feedback(::marco_msgs::action::DockToStation_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_FeedbackMessage msg_;
};

class Init_DockToStation_FeedbackMessage_goal_id
{
public:
  Init_DockToStation_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DockToStation_FeedbackMessage_feedback goal_id(::marco_msgs::action::DockToStation_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DockToStation_FeedbackMessage_feedback(msg_);
  }

private:
  ::marco_msgs::action::DockToStation_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::marco_msgs::action::DockToStation_FeedbackMessage>()
{
  return marco_msgs::action::builder::Init_DockToStation_FeedbackMessage_goal_id();
}

}  // namespace marco_msgs

#endif  // MARCO_MSGS__ACTION__DETAIL__DOCK_TO_STATION__BUILDER_HPP_
