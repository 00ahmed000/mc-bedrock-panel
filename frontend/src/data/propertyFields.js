// Drives PropertiesView.vue: one entry per FullServerProperties field on
// the backend (see backend/app/schemas.py — key names must match
// exactly). Keeping this data-driven means the whole form is ~40 lines
// of template instead of 38 hand-written inputs.

export const propertyGroups = [
  {
    title: 'General',
    fields: [
      { key: 'server_name', label: 'Server name', type: 'text' },
      { key: 'level_name', label: 'World name', type: 'text' },
      { key: 'level_seed', label: 'World seed', type: 'text', help: 'Leave blank for a random seed on first generation.' },
      { key: 'gamemode', label: 'Game mode', type: 'select', options: ['survival', 'creative', 'adventure'] },
      { key: 'difficulty', label: 'Difficulty', type: 'select', options: ['peaceful', 'easy', 'normal', 'hard'] },
      { key: 'force_gamemode', label: 'Force game mode on join', type: 'boolean' },
      { key: 'allow_cheats', label: 'Allow cheats', type: 'boolean' },
      { key: 'default_player_permission_level', label: 'Default permission for new players', type: 'select', options: ['visitor', 'member', 'operator'] },
    ],
  },
  {
    title: 'Network & Access',
    fields: [
      { key: 'server_port', label: 'Server port (IPv4)', type: 'number', min: 1, max: 65535 },
      { key: 'server_portv6', label: 'Server port (IPv6)', type: 'number', min: 1, max: 65535 },
      { key: 'max_players', label: 'Max players', type: 'number', min: 1, max: 2000 },
      { key: 'online_mode', label: 'Require Xbox Live authentication', type: 'boolean' },
      { key: 'enable_lan_visibility', label: 'Visible on LAN', type: 'boolean' },
      { key: 'allow_list', label: 'Enforce allowlist', type: 'boolean', help: 'Manage who\u2019s on it from the Allowlist tab.' },
      { key: 'compression_threshold', label: 'Compression threshold (bytes)', type: 'number', min: 0, max: 65535 },
      { key: 'compression_algorithm', label: 'Compression algorithm', type: 'select', options: ['zlib', 'snappy'] },
      { key: 'client_inactivity_timeout', label: 'Client inactivity timeout', type: 'number', min: 0 },
    ],
  },
  {
    title: 'World Performance',
    fields: [
      { key: 'view_distance', label: 'View distance (chunks)', type: 'number', min: 5, max: 96 },
      { key: 'tick_distance', label: 'Tick distance (chunks)', type: 'number', min: 2, max: 12 },
      { key: 'player_idle_timeout', label: 'Idle kick timeout (minutes, 0 = never)', type: 'number', min: 0 },
      { key: 'max_threads', label: 'Max worker threads (0 = auto)', type: 'number', min: 0 },
      { key: 'client_side_chunk_generation_enabled', label: 'Allow client-side chunk generation', type: 'boolean' },
    ],
  },
  {
    title: 'Anti-Cheat & Movement',
    fields: [
      { key: 'server_authoritative_movement', label: 'Movement authority', type: 'select', options: ['client-auth', 'server-auth', 'server-auth-with-rewind'] },
      { key: 'correct_player_movement', label: 'Correct player position on mismatch', type: 'boolean' },
      { key: 'server_authoritative_block_breaking', label: 'Server-authoritative block breaking', type: 'boolean' },
      { key: 'server_authoritative_sound', label: 'Server-authoritative sound', type: 'boolean' },
      { key: 'player_movement_score_threshold', label: 'Movement score threshold', type: 'number', min: 0 },
      { key: 'player_movement_distance_threshold', label: 'Movement distance threshold', type: 'number', min: 0, step: 0.01 },
      { key: 'player_movement_duration_threshold_in_ms', label: 'Movement duration threshold (ms)', type: 'number', min: 0 },
    ],
  },
  {
    title: 'Appearance & Privacy',
    fields: [
      { key: 'texturepack_required', label: 'Require server texture pack', type: 'boolean' },
      { key: 'chat_restriction', label: 'Chat restriction', type: 'select', options: ['None', 'Dropped', 'Disabled'] },
      { key: 'disable_player_interaction', label: 'Disable player-to-player interaction', type: 'boolean' },
      { key: 'disable_custom_skins', label: 'Disable custom skins', type: 'boolean' },
      { key: 'disable_custom_skins_untrusted', label: 'Disable untrusted custom skins', type: 'boolean' },
      { key: 'disable_persona_skins', label: 'Disable persona skins', type: 'boolean' },
      { key: 'disable_client_mods', label: 'Disable client mods', type: 'boolean' },
      { key: 'content_log_file_enabled', label: 'Log content errors to file', type: 'boolean' },
      { key: 'emit_server_telemetry', label: 'Send telemetry to Mojang', type: 'boolean' },
    ],
  },
]
