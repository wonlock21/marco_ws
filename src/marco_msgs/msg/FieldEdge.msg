# Directed semantic route edge. edge_id is logical and may be uint64.
uint64 edge_id
uint64 start_node_id
uint64 end_node_id
bool bidirectional
float64 cost
# Serialized as Nav2 abs_speed_limit; valid range is 0.05..0.50 m/s.
float64 max_speed
# ANY, EMPTY or LOADED.
string load_rule
# FORWARD, REVERSE or EITHER.
string movement_direction
string gate_event
string metadata_json
