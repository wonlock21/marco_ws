# Semantic route node. node_id is logical; Nav2 feature IDs are package-local uint16.
uint64 node_id
string name
# WAIT, PICKUP_APPROACH, PICKUP_DOCK, DROPOFF_APPROACH, DROPOFF_DOCK,
# GATE_Q5, QR_TRIGGER or TRANSIT (case-insensitive).
string role
string station_id
geometry_msgs/Pose2D pose
# ANY, EMPTY or LOADED.
string load_rule
# NAVIGATE, DOCK, PASS_THROUGH or TRIGGER.
string approach_mode
string metadata_json
