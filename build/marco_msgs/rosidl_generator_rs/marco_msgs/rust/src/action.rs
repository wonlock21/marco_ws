
#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to marco_msgs__action__DockToStation_Goal

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_Goal {
    /// --- Hedef ---
    /// Yanasilacak istasyonun kimligi. QR icerigiyle dogrulanir.
    pub station_id: std::string::String,

    /// Sartname madde 8 varsayilanlari: +/- 7.5 cm konum, +/- 5 derece yon.
    /// [m]
    pub position_tolerance: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw_tolerance: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub approach_type: u8,

    /// Zaman asimi. Asilirsa action iptal edilir ve gorev yonetimine hata bildirilir.
    pub timeout: f32,

}

impl DockToStation_Goal {
    /// Yuk alma mi birakma mi. Catalin hangi tarafta kalacagini ve hangi kameranin
    /// kullanilacagini belirler.
    pub const APPROACH_PICKUP: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const APPROACH_DROPOFF: u8 = 1;

}


impl Default for DockToStation_Goal {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_Goal::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_Goal {
  type RmwMsg = super::action::rmw::DockToStation_Goal;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        station_id: msg.station_id.as_str().into(),
        position_tolerance: msg.position_tolerance,
        yaw_tolerance: msg.yaw_tolerance,
        approach_type: msg.approach_type,
        timeout: msg.timeout,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        station_id: msg.station_id.as_str().into(),
      position_tolerance: msg.position_tolerance,
      yaw_tolerance: msg.yaw_tolerance,
      approach_type: msg.approach_type,
      timeout: msg.timeout,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      station_id: msg.station_id.to_string(),
      position_tolerance: msg.position_tolerance,
      yaw_tolerance: msg.yaw_tolerance,
      approach_type: msg.approach_type,
      timeout: msg.timeout,
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_Result

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_Result {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,

    /// Duruldugu andaki olculen hata. Kalibrasyon ve saha analizi icin kaydedilir.
    /// [m]
    pub final_position_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub final_yaw_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub result_code: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}

impl DockToStation_Result {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const RESULT_OK: u8 = 0;

    /// okunan QR hedefle uyusmadi
    pub const RESULT_QR_MISMATCH: u8 = 1;

    /// serit kaybedildi
    pub const RESULT_LANE_LOST: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const RESULT_TIMEOUT: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const RESULT_OBSTACLE: u8 = 4;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const RESULT_ABORTED: u8 = 5;

}


impl Default for DockToStation_Result {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_Result::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_Result {
  type RmwMsg = super::action::rmw::DockToStation_Result;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        final_position_error: msg.final_position_error,
        final_yaw_error: msg.final_yaw_error,
        result_code: msg.result_code,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
      final_position_error: msg.final_position_error,
      final_yaw_error: msg.final_yaw_error,
      result_code: msg.result_code,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      final_position_error: msg.final_position_error,
      final_yaw_error: msg.final_yaw_error,
      result_code: msg.result_code,
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_Feedback

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_Feedback {

    // This member is not documented.
    #[allow(missing_docs)]
    pub phase: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance_remaining: f32,

}



impl Default for DockToStation_Feedback {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_Feedback::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_Feedback {
  type RmwMsg = super::action::rmw::DockToStation_Feedback;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        phase: msg.phase.as_str().into(),
        position_error: msg.position_error,
        yaw_error: msg.yaw_error,
        distance_remaining: msg.distance_remaining,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        phase: msg.phase.as_str().into(),
      position_error: msg.position_error,
      yaw_error: msg.yaw_error,
      distance_remaining: msg.distance_remaining,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      phase: msg.phase.to_string(),
      position_error: msg.position_error,
      yaw_error: msg.yaw_error,
      distance_remaining: msg.distance_remaining,
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_FeedbackMessage

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_FeedbackMessage {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub feedback: super::action::DockToStation_Feedback,

}



impl Default for DockToStation_FeedbackMessage {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_FeedbackMessage::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_FeedbackMessage {
  type RmwMsg = super::action::rmw::DockToStation_FeedbackMessage;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Owned(msg.goal_id)).into_owned(),
        feedback: super::action::DockToStation_Feedback::into_rmw_message(std::borrow::Cow::Owned(msg.feedback)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Borrowed(&msg.goal_id)).into_owned(),
        feedback: super::action::DockToStation_Feedback::into_rmw_message(std::borrow::Cow::Borrowed(&msg.feedback)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      goal_id: unique_identifier_msgs::msg::UUID::from_rmw_message(msg.goal_id),
      feedback: super::action::DockToStation_Feedback::from_rmw_message(msg.feedback),
    }
  }
}






// Corresponds to marco_msgs__action__DockToStation_SendGoal_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_SendGoal_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: super::action::DockToStation_Goal,

}



impl Default for DockToStation_SendGoal_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_SendGoal_Request::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_SendGoal_Request {
  type RmwMsg = super::action::rmw::DockToStation_SendGoal_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Owned(msg.goal_id)).into_owned(),
        goal: super::action::DockToStation_Goal::into_rmw_message(std::borrow::Cow::Owned(msg.goal)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Borrowed(&msg.goal_id)).into_owned(),
        goal: super::action::DockToStation_Goal::into_rmw_message(std::borrow::Cow::Borrowed(&msg.goal)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      goal_id: unique_identifier_msgs::msg::UUID::from_rmw_message(msg.goal_id),
      goal: super::action::DockToStation_Goal::from_rmw_message(msg.goal),
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_SendGoal_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_SendGoal_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::Time,

}



impl Default for DockToStation_SendGoal_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_SendGoal_Response::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_SendGoal_Response {
  type RmwMsg = super::action::rmw::DockToStation_SendGoal_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        accepted: msg.accepted,
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Owned(msg.stamp)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      accepted: msg.accepted,
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Borrowed(&msg.stamp)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      accepted: msg.accepted,
      stamp: builtin_interfaces::msg::Time::from_rmw_message(msg.stamp),
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_GetResult_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_GetResult_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::UUID,

}



impl Default for DockToStation_GetResult_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_GetResult_Request::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_GetResult_Request {
  type RmwMsg = super::action::rmw::DockToStation_GetResult_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Owned(msg.goal_id)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal_id: unique_identifier_msgs::msg::UUID::into_rmw_message(std::borrow::Cow::Borrowed(&msg.goal_id)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      goal_id: unique_identifier_msgs::msg::UUID::from_rmw_message(msg.goal_id),
    }
  }
}


// Corresponds to marco_msgs__action__DockToStation_GetResult_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DockToStation_GetResult_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: i8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub result: super::action::DockToStation_Result,

}



impl Default for DockToStation_GetResult_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::action::rmw::DockToStation_GetResult_Response::default())
  }
}

impl rosidl_runtime_rs::Message for DockToStation_GetResult_Response {
  type RmwMsg = super::action::rmw::DockToStation_GetResult_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        status: msg.status,
        result: super::action::DockToStation_Result::into_rmw_message(std::borrow::Cow::Owned(msg.result)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      status: msg.status,
        result: super::action::DockToStation_Result::into_rmw_message(std::borrow::Cow::Borrowed(&msg.result)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      status: msg.status,
      result: super::action::DockToStation_Result::from_rmw_message(msg.result),
    }
  }
}






#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__action__DockToStation_SendGoal() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__action__DockToStation_SendGoal
#[allow(missing_docs, non_camel_case_types)]
pub struct DockToStation_SendGoal;

impl rosidl_runtime_rs::Service for DockToStation_SendGoal {
    type Request = DockToStation_SendGoal_Request;
    type Response = DockToStation_SendGoal_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__action__DockToStation_SendGoal() }
    }
}




#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__action__DockToStation_GetResult() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__action__DockToStation_GetResult
#[allow(missing_docs, non_camel_case_types)]
pub struct DockToStation_GetResult;

impl rosidl_runtime_rs::Service for DockToStation_GetResult {
    type Request = DockToStation_GetResult_Request;
    type Response = DockToStation_GetResult_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__action__DockToStation_GetResult() }
    }
}






#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_action_type_support_handle__marco_msgs__action__DockToStation() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__action__DockToStation
#[allow(missing_docs, non_camel_case_types)]
pub struct DockToStation;

impl rosidl_runtime_rs::Action for DockToStation {
  // --- Associated types for client library users ---
  /// The goal message defined in the action definition.
  type Goal = DockToStation_Goal;

  /// The result message defined in the action definition.
  type Result = DockToStation_Result;

  /// The feedback message defined in the action definition.
  type Feedback = DockToStation_Feedback;

  // --- Associated types for client library implementation ---
  /// The feedback message with generic fields which wraps the feedback message.
  type FeedbackMessage = super::action::DockToStation_FeedbackMessage;

  /// The send_goal service using a wrapped version of the goal message as a request.
  type SendGoalService = super::action::DockToStation_SendGoal;

  /// The generic service to cancel a goal.
  type CancelGoalService = action_msgs::srv::rmw::CancelGoal;

  /// The get_result service using a wrapped version of the result message as a response.
  type GetResultService = super::action::DockToStation_GetResult;

  // --- Methods for client library implementation ---
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_action_type_support_handle__marco_msgs__action__DockToStation() }
  }

  fn create_goal_request(
    goal_id: &[u8; 16],
    goal: super::action::rmw::DockToStation_Goal,
  ) -> super::action::rmw::DockToStation_SendGoal_Request {
   super::action::rmw::DockToStation_SendGoal_Request {
      goal_id: unique_identifier_msgs::msg::rmw::UUID { uuid: *goal_id },
      goal,
    }
  }

  fn split_goal_request(
    request: super::action::rmw::DockToStation_SendGoal_Request,
  ) -> (
    [u8; 16],
   super::action::rmw::DockToStation_Goal,
  ) {
    (request.goal_id.uuid, request.goal)
  }

  fn create_goal_response(
    accepted: bool,
    stamp: (i32, u32),
  ) -> super::action::rmw::DockToStation_SendGoal_Response {
   super::action::rmw::DockToStation_SendGoal_Response {
      accepted,
      stamp: builtin_interfaces::msg::rmw::Time {
        sec: stamp.0,
        nanosec: stamp.1,
      },
    }
  }

  fn get_goal_response_accepted(
    response: &super::action::rmw::DockToStation_SendGoal_Response,
  ) -> bool {
    response.accepted
  }

  fn get_goal_response_stamp(
    response: &super::action::rmw::DockToStation_SendGoal_Response,
  ) -> (i32, u32) {
    (response.stamp.sec, response.stamp.nanosec)
  }

  fn create_feedback_message(
    goal_id: &[u8; 16],
    feedback: super::action::rmw::DockToStation_Feedback,
  ) -> super::action::rmw::DockToStation_FeedbackMessage {
    let mut message = super::action::rmw::DockToStation_FeedbackMessage::default();
    message.goal_id.uuid = *goal_id;
    message.feedback = feedback;
    message
  }

  fn split_feedback_message(
    feedback: super::action::rmw::DockToStation_FeedbackMessage,
  ) -> (
    [u8; 16],
   super::action::rmw::DockToStation_Feedback,
  ) {
    (feedback.goal_id.uuid, feedback.feedback)
  }

  fn create_result_request(
    goal_id: &[u8; 16],
  ) -> super::action::rmw::DockToStation_GetResult_Request {
   super::action::rmw::DockToStation_GetResult_Request {
      goal_id: unique_identifier_msgs::msg::rmw::UUID { uuid: *goal_id },
    }
  }

  fn get_result_request_uuid(
    request: &super::action::rmw::DockToStation_GetResult_Request,
  ) -> &[u8; 16] {
    &request.goal_id.uuid
  }

  fn create_result_response(
    status: i8,
    result: super::action::rmw::DockToStation_Result,
  ) -> super::action::rmw::DockToStation_GetResult_Response {
   super::action::rmw::DockToStation_GetResult_Response {
      status,
      result,
    }
  }

  fn split_result_response(
    response: super::action::rmw::DockToStation_GetResult_Response
  ) -> (
    i8,
   super::action::rmw::DockToStation_Result,
  ) {
    (response.status, response.result)
  }
}


