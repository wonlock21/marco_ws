std_msgs/Header header

# Harita onizleme goruntusundeki piksel merkezi.
float32 pixel_x
float32 pixel_y

# Ekran koordinatlarinda yon: sifir saga, pozitif saat yonunde (radyan).
float32 screen_yaw

uint32 map_width
uint32 map_height
bool inside_map

# "slam_toolbox" veya "amcl"
string source
