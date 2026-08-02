#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to marco_msgs__srv__AssignTask_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AssignTask_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for AssignTask_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AssignTask_Request::default())
  }
}

impl rosidl_runtime_rs::Message for AssignTask_Request {
  type RmwMsg = super::srv::rmw::AssignTask_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to marco_msgs__srv__AssignTask_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AssignTask_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pickup_node: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub dropoff_node: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for AssignTask_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AssignTask_Response::default())
  }
}

impl rosidl_runtime_rs::Message for AssignTask_Response {
  type RmwMsg = super::srv::rmw::AssignTask_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        task_id: msg.task_id.as_str().into(),
        pickup_node: msg.pickup_node.as_str().into(),
        dropoff_node: msg.dropoff_node.as_str().into(),
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        task_id: msg.task_id.as_str().into(),
        pickup_node: msg.pickup_node.as_str().into(),
        dropoff_node: msg.dropoff_node.as_str().into(),
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      task_id: msg.task_id.to_string(),
      pickup_node: msg.pickup_node.to_string(),
      dropoff_node: msg.dropoff_node.to_string(),
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to marco_msgs__srv__GatePermission_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GatePermission_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub node_id: std::string::String,

}



impl Default for GatePermission_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GatePermission_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GatePermission_Request {
  type RmwMsg = super::srv::rmw::GatePermission_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        node_id: msg.node_id.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        node_id: msg.node_id.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      node_id: msg.node_id.to_string(),
    }
  }
}


// Corresponds to marco_msgs__srv__GatePermission_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GatePermission_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub granted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for GatePermission_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GatePermission_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GatePermission_Response {
  type RmwMsg = super::srv::rmw::GatePermission_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        granted: msg.granted,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      granted: msg.granted,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      granted: msg.granted,
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to marco_msgs__srv__TaskComplete_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for TaskComplete_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::TaskComplete_Request::default())
  }
}

impl rosidl_runtime_rs::Message for TaskComplete_Request {
  type RmwMsg = super::srv::rmw::TaskComplete_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        task_id: msg.task_id.as_str().into(),
        success: msg.success,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        task_id: msg.task_id.as_str().into(),
      success: msg.success,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      task_id: msg.task_id.to_string(),
      success: msg.success,
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to marco_msgs__srv__TaskComplete_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub acknowledged: bool,

}



impl Default for TaskComplete_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::TaskComplete_Response::default())
  }
}

impl rosidl_runtime_rs::Message for TaskComplete_Response {
  type RmwMsg = super::srv::rmw::TaskComplete_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        acknowledged: msg.acknowledged,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      acknowledged: msg.acknowledged,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      acknowledged: msg.acknowledged,
    }
  }
}


// Corresponds to marco_msgs__srv__StartMission_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartMission_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for StartMission_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartMission_Request::default())
  }
}

impl rosidl_runtime_rs::Message for StartMission_Request {
  type RmwMsg = super::srv::rmw::StartMission_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to marco_msgs__srv__StartMission_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartMission_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for StartMission_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartMission_Response::default())
  }
}

impl rosidl_runtime_rs::Message for StartMission_Response {
  type RmwMsg = super::srv::rmw::StartMission_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        accepted: msg.accepted,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      accepted: msg.accepted,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      accepted: msg.accepted,
      message: msg.message.to_string(),
    }
  }
}






#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__AssignTask() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__srv__AssignTask
#[allow(missing_docs, non_camel_case_types)]
pub struct AssignTask;

impl rosidl_runtime_rs::Service for AssignTask {
    type Request = AssignTask_Request;
    type Response = AssignTask_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__AssignTask() }
    }
}




#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__GatePermission() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__srv__GatePermission
#[allow(missing_docs, non_camel_case_types)]
pub struct GatePermission;

impl rosidl_runtime_rs::Service for GatePermission {
    type Request = GatePermission_Request;
    type Response = GatePermission_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__GatePermission() }
    }
}




#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__TaskComplete() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__srv__TaskComplete
#[allow(missing_docs, non_camel_case_types)]
pub struct TaskComplete;

impl rosidl_runtime_rs::Service for TaskComplete {
    type Request = TaskComplete_Request;
    type Response = TaskComplete_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__TaskComplete() }
    }
}




#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__StartMission() -> *const std::ffi::c_void;
}

// Corresponds to marco_msgs__srv__StartMission
#[allow(missing_docs, non_camel_case_types)]
pub struct StartMission;

impl rosidl_runtime_rs::Service for StartMission {
    type Request = StartMission_Request;
    type Response = StartMission_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__marco_msgs__srv__StartMission() }
    }
}


