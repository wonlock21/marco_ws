#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__AssignTask_Request() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__AssignTask_Request__init(msg: *mut AssignTask_Request) -> bool;
    fn marco_msgs__srv__AssignTask_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Request>, size: usize) -> bool;
    fn marco_msgs__srv__AssignTask_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Request>);
    fn marco_msgs__srv__AssignTask_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AssignTask_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Request>) -> bool;
}

// Corresponds to marco_msgs__srv__AssignTask_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AssignTask_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for AssignTask_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__AssignTask_Request__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__AssignTask_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AssignTask_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AssignTask_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AssignTask_Request where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/AssignTask_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__AssignTask_Request() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__AssignTask_Response() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__AssignTask_Response__init(msg: *mut AssignTask_Response) -> bool;
    fn marco_msgs__srv__AssignTask_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Response>, size: usize) -> bool;
    fn marco_msgs__srv__AssignTask_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Response>);
    fn marco_msgs__srv__AssignTask_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AssignTask_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<AssignTask_Response>) -> bool;
}

// Corresponds to marco_msgs__srv__AssignTask_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AssignTask_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pickup_node: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub dropoff_node: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for AssignTask_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__AssignTask_Response__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__AssignTask_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AssignTask_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__AssignTask_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AssignTask_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AssignTask_Response where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/AssignTask_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__AssignTask_Response() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__GatePermission_Request() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__GatePermission_Request__init(msg: *mut GatePermission_Request) -> bool;
    fn marco_msgs__srv__GatePermission_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Request>, size: usize) -> bool;
    fn marco_msgs__srv__GatePermission_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Request>);
    fn marco_msgs__srv__GatePermission_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GatePermission_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Request>) -> bool;
}

// Corresponds to marco_msgs__srv__GatePermission_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GatePermission_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub node_id: rosidl_runtime_rs::String,

}



impl Default for GatePermission_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__GatePermission_Request__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__GatePermission_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GatePermission_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GatePermission_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GatePermission_Request where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/GatePermission_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__GatePermission_Request() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__GatePermission_Response() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__GatePermission_Response__init(msg: *mut GatePermission_Response) -> bool;
    fn marco_msgs__srv__GatePermission_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Response>, size: usize) -> bool;
    fn marco_msgs__srv__GatePermission_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Response>);
    fn marco_msgs__srv__GatePermission_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GatePermission_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GatePermission_Response>) -> bool;
}

// Corresponds to marco_msgs__srv__GatePermission_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GatePermission_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub granted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for GatePermission_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__GatePermission_Response__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__GatePermission_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GatePermission_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__GatePermission_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GatePermission_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GatePermission_Response where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/GatePermission_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__GatePermission_Response() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__TaskComplete_Request() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__TaskComplete_Request__init(msg: *mut TaskComplete_Request) -> bool;
    fn marco_msgs__srv__TaskComplete_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Request>, size: usize) -> bool;
    fn marco_msgs__srv__TaskComplete_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Request>);
    fn marco_msgs__srv__TaskComplete_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskComplete_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Request>) -> bool;
}

// Corresponds to marco_msgs__srv__TaskComplete_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for TaskComplete_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__TaskComplete_Request__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__TaskComplete_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskComplete_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskComplete_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskComplete_Request where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/TaskComplete_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__TaskComplete_Request() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__TaskComplete_Response() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__TaskComplete_Response__init(msg: *mut TaskComplete_Response) -> bool;
    fn marco_msgs__srv__TaskComplete_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Response>, size: usize) -> bool;
    fn marco_msgs__srv__TaskComplete_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Response>);
    fn marco_msgs__srv__TaskComplete_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskComplete_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskComplete_Response>) -> bool;
}

// Corresponds to marco_msgs__srv__TaskComplete_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub acknowledged: bool,

}



impl Default for TaskComplete_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__TaskComplete_Response__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__TaskComplete_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskComplete_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__TaskComplete_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskComplete_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskComplete_Response where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/TaskComplete_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__TaskComplete_Response() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__StartMission_Request() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__StartMission_Request__init(msg: *mut StartMission_Request) -> bool;
    fn marco_msgs__srv__StartMission_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartMission_Request>, size: usize) -> bool;
    fn marco_msgs__srv__StartMission_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartMission_Request>);
    fn marco_msgs__srv__StartMission_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartMission_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<StartMission_Request>) -> bool;
}

// Corresponds to marco_msgs__srv__StartMission_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartMission_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for StartMission_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__StartMission_Request__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__StartMission_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartMission_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartMission_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartMission_Request where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/StartMission_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__StartMission_Request() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__StartMission_Response() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__srv__StartMission_Response__init(msg: *mut StartMission_Response) -> bool;
    fn marco_msgs__srv__StartMission_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartMission_Response>, size: usize) -> bool;
    fn marco_msgs__srv__StartMission_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartMission_Response>);
    fn marco_msgs__srv__StartMission_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartMission_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<StartMission_Response>) -> bool;
}

// Corresponds to marco_msgs__srv__StartMission_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartMission_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for StartMission_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__srv__StartMission_Response__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__srv__StartMission_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartMission_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__srv__StartMission_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartMission_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartMission_Response where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/srv/StartMission_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__srv__StartMission_Response() }
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


