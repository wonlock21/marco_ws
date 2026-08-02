#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to marco_msgs__msg__LaneOffset
/// Zemindeki renkli seridin robota gore konumu.
/// Yayinci: goruntu isleme ekibi. Tuketici: marco_docking.
/// Sartname madde 4: istasyona 1.5 m kala serit takibi.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct LaneOffset {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,

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
    pub camera_frame: std::string::String,

}



impl Default for LaneOffset {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::LaneOffset::default())
  }
}

impl rosidl_runtime_rs::Message for LaneOffset {
  type RmwMsg = super::msg::rmw::LaneOffset;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detected: msg.detected,
        lateral_offset: msg.lateral_offset,
        heading_error: msg.heading_error,
        confidence: msg.confidence,
        camera_frame: msg.camera_frame.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      detected: msg.detected,
      lateral_offset: msg.lateral_offset,
      heading_error: msg.heading_error,
      confidence: msg.confidence,
        camera_frame: msg.camera_frame.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detected: msg.detected,
      lateral_offset: msg.lateral_offset,
      heading_error: msg.heading_error,
      confidence: msg.confidence,
      camera_frame: msg.camera_frame.to_string(),
    }
  }
}


// Corresponds to marco_msgs__msg__QrDetection
/// Okunan QR kodu ve kameraya gore konumu.
/// Yayinci: goruntu isleme ekibi (GM67 + OpenCV). Tuketici: marco_mission, marco_docking.
/// Sartname madde 5: QR okuma ve QR kodun kameraya gore pozisyonunun hesaplanmasi.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct QrDetection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,

    /// QR goruntude tespit edilebildi mi.
    pub detected: bool,

    /// QR icerigi. Istasyon kimligi burada tasinir, gorev hedefiyle karsilastirilir.
    pub data: std::string::String,

    /// QR kodun kamera cercevesine gore konumu.
    /// x ileri [m], y sola [m], theta QR duzleminin donusu [rad].
    pub pose_in_camera: geometry_msgs::msg::Pose2D,

    /// Tespit guveni.
    pub confidence: f32,

    /// Olcumun alindigi kamera: "front" veya "rear".
    pub camera_frame: std::string::String,

}



impl Default for QrDetection {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::QrDetection::default())
  }
}

impl rosidl_runtime_rs::Message for QrDetection {
  type RmwMsg = super::msg::rmw::QrDetection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detected: msg.detected,
        data: msg.data.as_str().into(),
        pose_in_camera: geometry_msgs::msg::Pose2D::into_rmw_message(std::borrow::Cow::Owned(msg.pose_in_camera)).into_owned(),
        confidence: msg.confidence,
        camera_frame: msg.camera_frame.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      detected: msg.detected,
        data: msg.data.as_str().into(),
        pose_in_camera: geometry_msgs::msg::Pose2D::into_rmw_message(std::borrow::Cow::Borrowed(&msg.pose_in_camera)).into_owned(),
      confidence: msg.confidence,
        camera_frame: msg.camera_frame.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detected: msg.detected,
      data: msg.data.to_string(),
      pose_in_camera: geometry_msgs::msg::Pose2D::from_rmw_message(msg.pose_in_camera),
      confidence: msg.confidence,
      camera_frame: msg.camera_frame.to_string(),
    }
  }
}


// Corresponds to marco_msgs__msg__RobotStatus
/// Robotun butunlesik durumu. Tuketici: Flutter GUI (PC ve mobil).
/// Sartname madde 10, arayuzde gosterilmesi zorunlu durumlari kapsar.
/// Eksik gosterilen her bilgi -4 puan.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RobotStatus {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    pub pose: geometry_msgs::msg::PoseWithCovarianceStamped,


    // This member is not documented.
    #[allow(missing_docs)]
    pub localization_valid: bool,

    /// AMCL kovaryansinin izi, guven gostergesi
    pub position_covariance: f32,

    /// --- Navigasyon ---
    /// nav2_route grafindaki aktif kenar
    pub current_route_edge: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub next_node: std::string::String,

    /// rotadan anlik sapma, limit 0.10
    pub cross_track_error: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub obstacle_detected: bool,

    /// --- Gorev ayrintilari ---
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pickup_node: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub dropoff_node: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub last_qr_data: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RobotStatus::default())
  }
}

impl rosidl_runtime_rs::Message for RobotStatus {
  type RmwMsg = super::msg::rmw::RobotStatus;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        mission_state: msg.mission_state,
        manual_mode_enabled: msg.manual_mode_enabled,
        estop_active: msg.estop_active,
        pose: geometry_msgs::msg::PoseWithCovarianceStamped::into_rmw_message(std::borrow::Cow::Owned(msg.pose)).into_owned(),
        localization_valid: msg.localization_valid,
        position_covariance: msg.position_covariance,
        current_route_edge: msg.current_route_edge.as_str().into(),
        next_node: msg.next_node.as_str().into(),
        cross_track_error: msg.cross_track_error,
        obstacle_detected: msg.obstacle_detected,
        task_id: msg.task_id.as_str().into(),
        pickup_node: msg.pickup_node.as_str().into(),
        dropoff_node: msg.dropoff_node.as_str().into(),
        last_qr_data: msg.last_qr_data.as_str().into(),
        plc_connected: msg.plc_connected,
        gate_permission_granted: msg.gate_permission_granted,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      mission_state: msg.mission_state,
      manual_mode_enabled: msg.manual_mode_enabled,
      estop_active: msg.estop_active,
        pose: geometry_msgs::msg::PoseWithCovarianceStamped::into_rmw_message(std::borrow::Cow::Borrowed(&msg.pose)).into_owned(),
      localization_valid: msg.localization_valid,
      position_covariance: msg.position_covariance,
        current_route_edge: msg.current_route_edge.as_str().into(),
        next_node: msg.next_node.as_str().into(),
      cross_track_error: msg.cross_track_error,
      obstacle_detected: msg.obstacle_detected,
        task_id: msg.task_id.as_str().into(),
        pickup_node: msg.pickup_node.as_str().into(),
        dropoff_node: msg.dropoff_node.as_str().into(),
        last_qr_data: msg.last_qr_data.as_str().into(),
      plc_connected: msg.plc_connected,
      gate_permission_granted: msg.gate_permission_granted,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      mission_state: msg.mission_state,
      manual_mode_enabled: msg.manual_mode_enabled,
      estop_active: msg.estop_active,
      pose: geometry_msgs::msg::PoseWithCovarianceStamped::from_rmw_message(msg.pose),
      localization_valid: msg.localization_valid,
      position_covariance: msg.position_covariance,
      current_route_edge: msg.current_route_edge.to_string(),
      next_node: msg.next_node.to_string(),
      cross_track_error: msg.cross_track_error,
      obstacle_detected: msg.obstacle_detected,
      task_id: msg.task_id.to_string(),
      pickup_node: msg.pickup_node.to_string(),
      dropoff_node: msg.dropoff_node.to_string(),
      last_qr_data: msg.last_qr_data.to_string(),
      plc_connected: msg.plc_connected,
      gate_permission_granted: msg.gate_permission_granted,
    }
  }
}


