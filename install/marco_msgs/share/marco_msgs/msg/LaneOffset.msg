# Zemindeki renkli seridin robota gore konumu.
# Yayinci: goruntu isleme ekibi. Tuketici: marco_docking.
# Sartname madde 4: istasyona 1.5 m kala serit takibi.

std_msgs/Header header

# Serit goruntude tespit edilebildi mi. false ise diger alanlar gecersizdir.
bool detected

# Seridin robot merkez ekseninden yanal sapmasi [m].
# Pozitif = serit robotun solunda, robot saga kaymis demektir.
float32 lateral_offset

# Robotun yonelimi ile serit dogrultusu arasindaki aci farki [rad].
# Pozitif = robot serite gore saat yonunun tersine donuk.
float32 heading_error

# Tespit guveni [0.0 - 1.0]. Docking kontrolcusu esik altini yok sayar.
float32 confidence

# Olcumun alindigi kamera: "front" veya "rear".
# Yuk tasinirken catal arkada kaldigi icin arka kamera kullanilir.
string camera_frame
