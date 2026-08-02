#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__LaneOffset() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__msg__LaneOffset__init(msg: *mut LaneOffset) -> bool;
    fn marco_msgs__msg__LaneOffset__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<LaneOffset>, size: usize) -> bool;
    fn marco_msgs__msg__LaneOffset__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<LaneOffset>);
    fn marco_msgs__msg__LaneOffset__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<LaneOffset>, out_seq: *mut rosidl_runtime_rs::Sequence<LaneOffset>) -> bool;
}

// Corresponds to marco_msgs__msg__LaneOffset
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Zemindeki renkli seridin robota gore konumu.
/// Yayinci: goruntu isleme ekibi. Tuketici: marco_docking.
/// Sartname madde 4: istasyona 1.5 m kala serit takibi.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct LaneOffset {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,

    /// Serit goruntude tespit edilebildi mi. false ise diger alanlar gecersizdir.
    pub detected: bool,

    /// Seridin robot merkez ekseninden yanal sapmasi.
    /// Pozitif = serit robotun solunda, robot saga kaymis demektir.
    pub lateral_offset: f32,

    /// Robotun yonelimi ile serit dogrultusu arasindaki aci farki.
    /// Pozitif = robot serite gore saat yonunun tersine donuk.
    pub heading_error: f32,

    /// Tespit guveni. Docking kontrolcusu esik altini yok sayar.
    pub confidence: f32,

    /// Olcumun alindigi kamera: "front" veya "rear".
    /// Yuk tasinirken catal arkada kaldigi icin arka kamera kullanilir.
    pub camera_frame: rosidl_runtime_rs::String,

}



impl Default for LaneOffset {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__msg__LaneOffset__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__msg__LaneOffset__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for LaneOffset {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__LaneOffset__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__LaneOffset__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__LaneOffset__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for LaneOffset {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for LaneOffset where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/msg/LaneOffset";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__LaneOffset() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__QrDetection() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__msg__QrDetection__init(msg: *mut QrDetection) -> bool;
    fn marco_msgs__msg__QrDetection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<QrDetection>, size: usize) -> bool;
    fn marco_msgs__msg__QrDetection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<QrDetection>);
    fn marco_msgs__msg__QrDetection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<QrDetection>, out_seq: *mut rosidl_runtime_rs::Sequence<QrDetection>) -> bool;
}

// Corresponds to marco_msgs__msg__QrDetection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Okunan QR kodu ve kameraya gore konumu.
/// Yayinci: goruntu isleme ekibi (GM67 + OpenCV). Tuketici: marco_mission, marco_docking.
/// Sartname madde 5: QR okuma ve QR kodun kameraya gore pozisyonunun hesaplanmasi.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct QrDetection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,

    /// QR goruntude tespit edilebildi mi.
    pub detected: bool,

    /// QR icerigi. Istasyon kimligi burada tasinir, gorev hedefiyle karsilastirilir.
    pub data: rosidl_runtime_rs::String,

    /// QR kodun kamera cercevesine gore konumu.
    /// x ileri [m], y sola [m], theta QR duzleminin donusu [rad].
    pub pose_in_camera: geometry_msgs::msg::rmw::Pose2D,

    /// Tespit guveni.
    pub confidence: f32,

    /// Olcumun alindigi kamera: "front" veya "rear".
    pub camera_frame: rosidl_runtime_rs::String,

}



impl Default for QrDetection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__msg__QrDetection__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__msg__QrDetection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for QrDetection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__QrDetection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__QrDetection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__QrDetection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for QrDetection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for QrDetection where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/msg/QrDetection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__QrDetection() }
  }
}


#[link(name = "marco_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__RobotStatus() -> *const std::ffi::c_void;
}

#[link(name = "marco_msgs__rosidl_generator_c")]
extern "C" {
    fn marco_msgs__msg__RobotStatus__init(msg: *mut RobotStatus) -> bool;
    fn marco_msgs__msg__RobotStatus__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RobotStatus>, size: usize) -> bool;
    fn marco_msgs__msg__RobotStatus__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RobotStatus>);
    fn marco_msgs__msg__RobotStatus__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RobotStatus>, out_seq: *mut rosidl_runtime_rs::Sequence<RobotStatus>) -> bool;
}

// Corresponds to marco_msgs__msg__RobotStatus
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Robotun butunlesik durumu. Tuketici: Flutter GUI (PC ve mobil).
/// Sartname madde 10, arayuzde gosterilmesi zorunlu durumlari kapsar.
/// Eksik gosterilen her bilgi -4 puan.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RobotStatus {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub mission_state: u8,

    /// --- Kontrol modu ---
    /// Fiziksel anahtar otomatik konumdayken uzaktan manuel kontrol kilitlidir.
    pub manual_mode_enabled: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub estop_active: bool,

    /// --- Lokalizasyon ---
    pub pose: geometry_msgs::msg::rmw::PoseWithCovarianceStamped,


    // This member is not documented.
    #[allow(missing_docs)]
    pub localization_valid: bool,

    /// AMCL kovaryansinin izi, guven gostergesi
    pub position_covariance: f32,

    /// --- Navigasyon ---
    /// nav2_route grafindaki aktif kenar
    pub current_route_edge: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub next_node: rosidl_runtime_rs::String,

    /// rotadan anlik sapma, limit 0.10
    pub cross_track_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub obstacle_detected: bool,

    /// --- Gorev ayrintilari ---
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pickup_node: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub dropoff_node: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub last_qr_data: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub plc_connected: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub gate_permission_granted: bool,

}

impl RobotStatus {
    /// --- Gorev durumu (sartname madde 10 a-h) ---
    /// goreve hazir bekleme
    pub const STATE_IDLE: u8 = 0;

    /// gorev alindi, isleniyor
    pub const STATE_TASK_RECEIVED: u8 = 1;

    /// gorev alindi, yuksuz hareket
    pub const STATE_MOVING_UNLOADED: u8 = 2;

    /// gorev alindi, yuklu hareket
    pub const STATE_MOVING_LOADED: u8 = 3;

    /// fabrika otomasyon sistemi komut bekleniyor
    pub const STATE_WAITING_PLC: u8 = 4;

    /// gorev tamamlandi, baslangic noktasina hareket
    pub const STATE_RETURNING: u8 = 5;

    /// hata durumu
    pub const STATE_ERROR: u8 = 6;

    /// acil stop
    pub const STATE_ESTOP: u8 = 7;

}


impl Default for RobotStatus {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !marco_msgs__msg__RobotStatus__init(&mut msg as *mut _) {
        panic!("Call to marco_msgs__msg__RobotStatus__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RobotStatus {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__RobotStatus__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__RobotStatus__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { marco_msgs__msg__RobotStatus__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RobotStatus {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RobotStatus where Self: Sized {
  const TYPE_NAME: &'static str = "marco_msgs/msg/RobotStatus";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__marco_msgs__msg__RobotStatus() }
  }
}


