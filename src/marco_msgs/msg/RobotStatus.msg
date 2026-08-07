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

# --- Kontrol modu ---
# Fiziksel anahtar otomatik konumdayken uzaktan manuel kontrol kilitlidir.
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
bool plc_connected
bool gate_permission_granted
