# Robotun butunlesik durumu. Tuketici: Flutter GUI (PC ve mobil).
# Sartname madde 10, arayuzde gosterilmesi zorunlu durumlari kapsar.
# Eksik gosterilen her bilgi -4 puan.

std_msgs/Header header

# --- Gorev durumu (sartname madde 10 a-h) ---
uint8 STATE_IDLE=0                # goreve hazir bekleme
uint8 STATE_TASK_RECEIVED=1       # gorev alindi, isleniyor
uint8 STATE_MOVING_UNLOADED=2     # gorev alindi, yuksuz hareket
uint8 STATE_MOVING_LOADED=3       # gorev alindi, yuklu hareket
uint8 STATE_WAITING_PLC=4         # fabrika otomasyon sistemi komut bekleniyor
uint8 STATE_RETURNING=5           # gorev tamamlandi, baslangic noktasina hareket
uint8 STATE_ERROR=6               # hata durumu
uint8 STATE_ESTOP=7               # acil stop
uint8 mission_state
float32 mission_elapsed_s       # gorev basladigindan beri gecen sure [s]
string status_detail            # hata/bekleme gibi operator aciklamasi

# --- Kontrol modu ---
# Fiziksel mod anahtari henuz takili degil; alan gelecekteki donanim icin ayrildi.
bool manual_mode_enabled
bool estop_active

# --- Lokalizasyon ---
geometry_msgs/PoseWithCovarianceStamped pose
bool localization_valid
float32 position_covariance   # AMCL kovaryansinin izi, guven gostergesi

# --- Navigasyon ---
string current_route_edge     # nav2_route grafindaki aktif kenar
string next_node
float32 cross_track_error     # rotadan anlik sapma [m], limit 0.10
float32 route_speed_limit     # graf/sapma korumasindan etkin mutlak limit [m/s]
string route_guard_state      # idle | normal | warning | slowdown | stop
string route_stop_reason      # bos veya makine-okunur durus nedeni
uint64[] selected_route_edges # secilen semantik yolun sirali edge kimlikleri
bool obstacle_detected

# --- Arac telemetrisi ---
float32 linear_speed          # odom ileri/geri hiz [m/s]
float32 battery_voltage       # STM32 batarya gerilimi [V]
float32 battery_current       # sarj pozitif, tuketim negatif [A]
float32 battery_temperature   # batarya/elektronik sicakligi [C]

# --- Gorev ayrintilari ---
string task_id
string task_source             # plc | mock_plc | gui
string pickup_node
string dropoff_node
string[] route_nodes          # secim sirasindaki tum alma/birakma duraklari
uint32 current_stop_index     # route_nodes icinde siradaki/aktif durak
bool return_home
string last_qr_data
bool last_qr_detected
geometry_msgs/Pose2D last_qr_pose_in_camera
float32 last_qr_confidence
string last_qr_camera_frame
float32 last_qr_age_s           # son QR mesaji yasi [s], hic gelmediyse +Inf
bool plc_connected
bool gate_permission_granted

# --- Istasyon yaklasim/QR tetigi (F7A) ---
# IDLE | APPROACHING_STATION | QR_VERIFIED | TURNING_180 |
# LINE_FOLLOW_READY | LINE_FOLLOW_DOCKING | PICKUP_READY |
# DROPOFF_READY | EXITING_STATION
string station_phase
bool qr_trigger_armed
string expected_qr_id
string qr_target_station
string last_qr_reject_reason

# --- Sureli arka-serit docking (F7C) ---
string docking_target_station
float32 docking_configured_duration_s
float32 docking_elapsed_s
float32 docking_remaining_s
bool docking_lane_control_active
bool docking_camera_valid
bool docking_stopped
string docking_error_reason

# --- Etkin saha paketi ---
bool active_field_ready
string active_field_name
string active_field_version
string active_field_hash
