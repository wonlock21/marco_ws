# Faz 3 Flutter Saha ve Rota Entegrasyon Promptu

Bu dosya tek başına Flutter ajanına verilmek üzere hazırlanmıştır. Ajanın
`marco_ws` klasörünü görmesi gerekmez. Aşağıdaki ROS mesaj, servis, topic,
durum yönetimi ve kabul kriterleri kanonik sözleşmedir.

## Ajana görev

Mevcut Flutter projesindeki çalışan rosbridge bağlantısını, reconnect
mekanizmasını, manuel sürüş güvenlik kilitlerini, mapping/lokalizasyon akışını
ve mevcut ekran tasarımını koru. Yeni ve ayrı bir demo uygulama ya da ikinci
bir rota editörü oluşturma.

Mevcut saha, harita, node ve route ekranlarındaki yerel draft/stub veri
kaynağını aşağıdaki ROS API ile değiştir. Yalnız içinde bulunduğun güncel
Flutter projesini değiştir; başka bir proje yolu varsayma.

Önce mevcut kaynakları incele ve şu katmanları projenin mevcut mimarisine
uygun biçimde tamamla:

1. Aşağıdaki ROS yapıları için immutable ve tipli Dart modelleri.
2. Mevcut rosbridge client içinde topic abonelikleri ve servis metotları.
3. Mevcut service/repository/controller katmanına pass-through metotları.
4. Mevcut node/route/harita ekranlarının gerçek backend'e bağlanması.
5. Model, JSON sözleşmesi, servis request'i ve durum geçişi testleri.

## Rosbridge kuralları

- ROS 2 tip adlarını burada yazıldığı biçimde kullan:
  `marco_msgs/msg/...` ve `marco_msgs/srv/...`.
- Servis çağrısı rosbridge biçimindedir:

```json
{
  "op": "call_service",
  "id": "benzersiz_istemci_id",
  "service": "/fields/get_graph",
  "type": "marco_msgs/srv/GetFieldGraph",
  "args": {"field_name": "saha_1"}
}
```

- Standart rosbridge cevabındaki uygulama payload'ı `values` içindedir:

```json
{
  "op": "service_response",
  "id": "benzersiz_istemci_id",
  "service": "/fields/get_graph",
  "result": true,
  "values": {
    "success": true,
    "message": "Field graph loaded"
  }
}
```

- Hem rosbridge `result` değerini hem de `values.success` alanını kontrol et.
  `result=true`, uygulama işleminin başarılı olduğu anlamına tek başına gelmez.
- Timeout, socket kapanması veya reconnect sırasında bekleyen tüm servis
  future/completer'larını hata ile tamamla; eski cevabı yeni bağlantıya taşıma.
- Topic mesajı `{"op":"publish","topic":"...","msg":{...}}` zarfındaki `msg`
  alanından parse edilir.
- JSON alan adları ROS ile birebir `snake_case` olmalıdır.
- Bilinmeyen ek alanları görmezden gel; zorunlu alanların yanlış tipini sessizce
  kabul etme. Topic telemetrisi için kontrollü tolerant parser, servis
  cevapları ve kaydetme request'leri için strict parser kullan.

## Ortak alt tipler

`std_msgs/Header` JSON:

```json
{
  "stamp": {"sec": 0, "nanosec": 0},
  "frame_id": "map"
}
```

`geometry_msgs/Pose2D` JSON:

```json
{"x": 0.0, "y": 0.0, "theta": 0.0}
```

## Kanonik mesaj sözleşmeleri

### `marco_msgs/msg/FieldNode`

```text
uint64 node_id
string name
string role
string station_id
geometry_msgs/Pose2D pose
string load_rule
string approach_mode
string metadata_json
```

Örnek:

```json
{
  "node_id": 101,
  "name": "A1",
  "role": "PICKUP_DOCK",
  "station_id": "A1",
  "pose": {"x": 2.4, "y": 1.1, "theta": 3.14159},
  "load_rule": "EMPTY",
  "approach_mode": "DOCK",
  "metadata_json": "{}"
}
```

Geçerli `role` değerleri:

- `WAIT`
- `PICKUP_APPROACH`
- `PICKUP_DOCK`
- `DROPOFF_APPROACH`
- `DROPOFF_DOCK`
- `GATE_Q5`
- `QR_TRIGGER`
- `TRANSIT`

Geçerli `load_rule`: `ANY`, `EMPTY`, `LOADED`.

Geçerli `approach_mode`: `NAVIGATE`, `DOCK`, `PASS_THROUGH`, `TRIGGER`.

Backend enumları büyük/küçük harfe duyarsız kabul eder ve küçük harfle saklar.
`theta` radyandır. `metadata_json` geçerli bir JSON object metni olmalıdır;
boş metadata için `"{}"` gönder.

### `marco_msgs/msg/FieldEdge`

```text
uint64 edge_id
uint64 start_node_id
uint64 end_node_id
bool bidirectional
float64 cost
float64 max_speed
string load_rule
string movement_direction
string gate_event
string metadata_json
```

Örnek:

```json
{
  "edge_id": 5001,
  "start_node_id": 101,
  "end_node_id": 102,
  "bidirectional": true,
  "cost": 1.0,
  "max_speed": 0.2,
  "load_rule": "ANY",
  "movement_direction": "FORWARD",
  "gate_event": "",
  "metadata_json": "{}"
}
```

Kurallar:

- `cost > 0`.
- `max_speed` mutlak m/s değeridir ve `0.05..0.50` aralığındadır.
- `movement_direction`: `FORWARD`, `REVERSE` veya `EITHER`.
- `load_rule=LOADED` kenarlar `movement_direction=REVERSE` olmalıdır.
- q5 düğümüne giren veya çıkan kenarlarda `gate_event` boş olamaz.
- `bidirectional=true`, backend tarafında iki yönlü Nav2 feature üretir; Flutter
  ikinci bir ters edge oluşturmamalıdır.

### `marco_msgs/msg/FieldPackageStatus`

```text
uint8 STATE_DRAFT=0
uint8 STATE_VALID=1
uint8 STATE_ACTIVE=2
uint8 STATE_ARCHIVED=3
uint8 STATE_ERROR=4

std_msgs/Header header
uint8 state
string field_name
string package_hash
uint32 node_count
uint32 edge_count
string[] errors
string[] warnings
string message
```

`errors` ve `warnings` kullanıcıya gösterilmelidir. Sadece ilk hatayı gösterip
diğerlerini kaybetme.

### `marco_msgs/msg/ActiveField`

```text
std_msgs/Header header
bool active
string field_name
string package_version
string package_hash
string graph_file
string activated_at
string message
```

`graph_file` Orange Pi üzerindeki tanı bilgisidir. Flutter bu dosyayı doğrudan
okumamalı; graph için `/fields/get_graph` kullanmalıdır.

### `marco_msgs/msg/FieldInfo`

```text
string field_name
string field_directory
string map_yaml
string preview_png
string created_at
bool map_ready
bool initial_pose_ready
bool localization_ready
bool route_ready
bool validation_passed
string route_hash
bool active
string package_version
string package_hash
string message
```

`field_directory`, `map_yaml` ve `preview_png` Orange Pi dosya yollarıdır;
Flutter'ın lokal dosya yolları değildir.

### `marco_msgs/msg/RobotStatus` Faz 3 ek alanları

Mevcut `RobotStatus` parser'ına şu alanları ekle:

```text
bool active_field_ready
string active_field_name
string active_field_version
string active_field_hash
```

Var olan RobotStatus alanlarını veya stale-status güvenlik davranışını kaldırma.

## Topic'ler

### `/fields/active`

- Tip: `marco_msgs/msg/ActiveField`
- QoS: transient-local, reliable, depth 1
- Rosbridge subscribe:

```json
{
  "op": "subscribe",
  "topic": "/fields/active",
  "type": "marco_msgs/msg/ActiveField",
  "queue_length": 1
}
```

### `/fields/package_status`

- Tip: `marco_msgs/msg/FieldPackageStatus`
- QoS: transient-local, reliable, depth 1

Reconnect sonrasında topic'in son değerini beklemekle yetinme;
`/fields/get_active` çağırarak aktif saha durumunu tekrar eşitle.
Disconnect olduğunda eski active/status modelini “güncel” göstermeyi bırak.

## Servis sözleşmeleri

Her blokta `---` öncesi request, sonrası response alanlarıdır.

### `/fields/list` — `marco_msgs/srv/ListFields`

```text
---
bool success
string message
marco_msgs/FieldInfo[] fields
```

Request `{}` gönderilir.

Bu servis `localization_manager` tarafından sunulur ve saha hazırlama için
`mapping_control.launch.py` akışında kullanılabilir. Yalnız görev/runtime
launch'ında servis bulunmuyorsa bunu bağlantı kopması gibi yorumlama;
`/fields/get_active` ve transient-local topic'ler çalışmaya devam eder. Saha
listesi ekranında servis kullanılamıyor durumunu açıkça göster.

### `/fields/get_graph` — `marco_msgs/srv/GetFieldGraph`

```text
string field_name
---
bool success
string message
marco_msgs/FieldNode[] nodes
marco_msgs/FieldEdge[] edges
marco_msgs/FieldPackageStatus status
```

### `/fields/save_node` — `marco_msgs/srv/SaveFieldNode`

```text
string field_name
marco_msgs/FieldNode node
---
bool success
string message
marco_msgs/FieldNode saved_node
string package_hash
```

### `/fields/save_current_pose_node` — `marco_msgs/srv/SaveCurrentPoseNode`

```text
string field_name
marco_msgs/FieldNode node
---
bool success
string message
marco_msgs/FieldNode saved_node
string package_hash
```

Request içindeki semantik alanlar kullanılır; `pose` backend tarafından güncel
`map -> base_footprint` TF pozu ve yaw ile değiştirilir.

### `/fields/delete_node` — `marco_msgs/srv/DeleteFieldNode`

```text
string field_name
uint64 node_id
bool delete_connected_edges
---
bool success
string message
uint32 deleted_edge_count
string package_hash
```

Bağlı edge varken `delete_connected_edges=false` çağrısı reddedilir. Kullanıcıya
bağlı edge'leri de silmek istediğini sor.

### `/fields/save_edge` — `marco_msgs/srv/SaveFieldEdge`

```text
string field_name
marco_msgs/FieldEdge edge
---
bool success
string message
marco_msgs/FieldEdge saved_edge
string package_hash
```

### `/fields/delete_edge` — `marco_msgs/srv/DeleteFieldEdge`

```text
string field_name
uint64 edge_id
---
bool success
string message
string package_hash
```

### `/fields/pixel_to_map` — `marco_msgs/srv/PixelToMap`

```text
string field_name
float64 pixel_x
float64 pixel_y
float64 screen_yaw
---
bool success
string message
geometry_msgs/Pose2D pose
bool inside_map
uint32 map_width
uint32 map_height
```

Flutter map koordinatını kendi başına yeniden hesaplamamalıdır. Harita
tıklaması ve ekrandaki yön oku bu servise gönderilir. `success=true` olsa bile
`inside_map=false` ise node kaydetme düğmesini devre dışı bırak.

### `/fields/validate` — `marco_msgs/srv/ValidateField`

```text
string field_name
---
bool success
string message
marco_msgs/FieldPackageStatus status
```

Başarılı doğrulamadaki `status.package_hash`, aktivasyonda kullanılacak tek
hash'tir.

### `/fields/activate` — `marco_msgs/srv/ActivateField`

```text
string field_name
string expected_hash
---
bool success
string message
marco_msgs/ActiveField active_field
marco_msgs/FieldPackageStatus status
```

`expected_hash`, son başarılı `/fields/validate` cevabındaki hash olmalıdır.
Boş veya eski hash kullanma. Görev, mapping veya araç hareketi sırasında
backend aktivasyonu reddeder.

### `/fields/archive` — `marco_msgs/srv/ArchiveField`

```text
string field_name
---
bool success
string message
string archive_directory
```

Aktif saha arşivlenemez. Bu işlem gerçek silme değildir.

### `/fields/get_active` — `marco_msgs/srv/GetActiveField`

```text
---
bool success
string message
marco_msgs/ActiveField active_field
marco_msgs/FieldPackageStatus status
```

Request `{}` gönderilir.

## Mevcut mapping/lokalizasyon akışıyla bağlantı

Yeni saha klasörü rota editöründe oluşturulmaz. Mevcut mapping akışı kullanılır:

### `/mapping/start` — `marco_msgs/srv/StartMapping`

```text
string field_name
---
bool accepted
string message
```

### `/mapping/save` — `marco_msgs/srv/SaveMapping`

```text
---
bool success
string message
string field_directory
string map_yaml
```

Mapping kaydı tamamlanınca backend boş `route.geojson` ve `stations.yaml`
şablonlarını da oluşturur. Ardından `/fields/list` ve `/fields/get_graph`
yenilenmelidir.

Mevcut `/mapping/stop`, `/localization/start` ve `/localization/stop`
entegrasyonunu koru. Mapping ile lokalizasyonun aynı anda başlamasını sağlayan
bir UI akışı oluşturma.

## UI durum makinesi

1. Bağlantı kurulunca `/fields/list` ve `/fields/get_active` çağır.
2. Kullanıcı bir saha seçince `/fields/get_graph` çağır.
3. `FieldInfo.active=true` olan saha salt okunur gösterilmelidir; backend aktif
   sahada CRUD işlemlerini zaten reddeder.
4. Her node/edge kaydı veya silme işleminden sonra önceki validation ve
   activation hash'ini geçersiz say; aktivasyon düğmesini kapat.
5. CRUD cevabı başarılıysa dönen `package_hash` değerini sakla ve graph'ı
   backend'den yeniden yükle.
6. Validate cevabındaki tüm hata/uyarıları göster.
7. Yalnız `validate.success=true`, `status.state=STATE_VALID` ve eldeki graph
   son doğrulamadan beri değişmemişse Activate düğmesini aç.
8. Activate request'inde doğrulamadaki exact `status.package_hash` değerini
   `expected_hash` olarak gönder.
9. `/fields/active` topic'i veya başarılı activate cevabı geldiğinde saha
   listesini ve graph durumunu yenile.
10. Reconnect sonrasında yerel hash'e güvenme; list/get_active/get_graph ile
    backend durumunu yeniden kur.

## Yarışma profili form kuralları

UI şu semantik düğümleri tanımlamayı kolaylaştırmalıdır:

- Bir `WAIT` istasyonu ve `role=WAIT`
- `A1`, `A2`, `A3`: `role=PICKUP_DOCK`
- `B1`, `B2`, `B3`: `role=DROPOFF_DOCK`
- q5 kapısı: `role=GATE_Q5`

Validator ayrıca şunları kontrol eder:

- Benzersiz node adları ve geçerli yaw
- Harita sınırı ve araç footprint geçişi
- WAIT → A1..A3 → B1..B3 → WAIT yönlü erişilebilirliği
- Her A→B rotasının q5 üzerinden geçmesi; q5 bypass/kestirme olmaması
- q5 edge'lerinde kapı olayı
- Yüklü hareketin reverse/yük arkada kuralı
- `stations.yaml` ile graph tutarlılığı

UI validator mantığını backend yerine yeniden yazmamalıdır. Formda hızlı geri
bildirim verilebilir, fakat nihai karar yalnız `/fields/validate` cevabıdır.

## Kimlik güvenliği

ROS alanları `uint64` olsa da JSON ve Flutter Web, `2^53-1` üzerindeki sayıları
kayıpsız taşıyamaz. Bu nedenle Flutter tarafından üretilen `node_id` ve
`edge_id` değerlerini şu aralıkla sınırla:

```text
0 <= id <= 9007199254740991
```

- ID'leri `double` üzerinden üretme veya parse etme.
- Timestamp tabanlı ID kullanılıyorsa sonucu bu güvenli aralıkta tut.
- Gelen sayı integral değilse, negatifse veya güvenli aralığı aşıyorsa kaydetme
  ve kullanıcıya sözleşme hatası göster.
- ROS request'inde ID'yi JSON number/int olarak gönder; string gönderme.
- Nav2 GeoJSON feature ID'leri backend tarafından üretilir. Flutter logical
  ID'yi feature ID olarak yorumlamamalıdır.

## Hata ve güvenlik davranışı

- Backend `message`, `errors` ve `warnings` metinlerini gizleme.
- Başarısız işlemden sonra optimistic local modeli başarılı gibi bırakma.
- Aktif sahayı düzenlemeye çalışma.
- Mapping/görev/hareket sırasında aktivasyonu UI'da da kapat; backend reddi yine
  nihai güvenlik katmanıdır.
- Disconnect veya stale `RobotStatus` sırasında manuel hız komutunu kesen mevcut
  davranışı koru.
- Flutter hiçbir zaman `active.yaml`, `route.geojson`, `map.yaml` veya
  `stations.yaml` dosyasını doğrudan yazmamalıdır.
- Pixel→map, validation, hash ve aktivasyon kararları yalnız ROS backend'dedir.

## Zorunlu testler

En az şu testleri ekle veya güncelle:

1. Tüm mesaj modellerinin strict parse ve `snake_case` serialize round-trip'i.
2. Eksik/yanlış tip alanların kontrollü reddi.
3. `node_id`/`edge_id` güvenli sayı sınırı.
4. On iki field servisinin exact service adı, ROS tipi ve request alanları.
5. `station_id` alanının kullanılması; eski `station` alanının gönderilmemesi.
6. Validate hash'i olmadan activate düğmesinin kapalı olması.
7. CRUD sonrası önceki validation hash'inin geçersizleşmesi.
8. Reconnect sonrası get_active/list/get_graph yeniden eşitlemesi.
9. `inside_map=false` durumunda node kaydının engellenmesi.
10. Backend `errors` ve `warnings` dizilerinin tamamının UI'da korunması.
11. Mevcut stale-status ve manuel sürüş güvenlik testlerinin bozulmaması.

Sonunda şunları çalıştır:

```bash
dart format lib test
flutter analyze
flutter test
```

Araçlar veya bağımlılıklar yoksa bunu açıkça raporla; testleri çalıştırmış gibi
gösterme.

## Teslim kriterleri

- Yerel node/route stub'ları artık çalışma zamanında gerçek veri kaynağı değil.
- Kullanıcı haritadan veya güncel robot pozundan semantik node kaydedebiliyor.
- Yaw düzenleme, edge CRUD, çift yön, hız, yük/yön ve q5 event alanları gerçek
  servislere bağlı.
- Validation hataları görünür ve hash-bound activation uygulanıyor.
- Aktif saha adı, sürümü ve hash'i GUI'de görülebiliyor.
- Reconnect sonrasında yanlış/stale saha aktif görünmüyor.
- Mevcut mapping, localization, mission, manuel güvenlik ve ekran akışları
  korunuyor.
- Flutter kaynakları doğrudan ROS workspace dosyalarına bağımlı değil.

## Fiziksel kabul kontrol listesi

Bu bölüm otomatik testlerin yerine geçmez:

1. LiDAR ve STM32 bağlıyken GUI'den yeni saha mapping'i başlat ve kaydet.
2. `/fields/list` içinde yeni sahanın görünmesini doğrula.
3. Harita tıklaması ve robotun güncel pozuyla node kaydet.
4. WAIT, A1..A3, B1..B3 ve q5 düğümlerini; yaw ve edge metadata'sını tamamla.
5. Validate çalıştır; tüm hataları düzelt ve PASS hash'ini görüntüle.
6. Görev/mapping sırasında Activate'in reddedildiğini doğrula.
7. Araç sabitken aktive et; active topic, saha listesi ve RobotStatus aynı
   saha adı/sürüm/hash'i göstermelidir.
8. Gerçek sistem açılışında AMCL map'i ile Route Server graph'ının aynı aktif
   saha paketinden geldiğini doğrula.
