# Laptop profile: keep visuals tasteful while reducing battery impact.
# Keep Ghostty as the canonical/default provider; prefer WezTerm first when fallback is needed.
export TINO_TERMINAL_PROVIDER_PREFERENCES="wezterm kitty alacritty"
export TINO_TERMINAL_OPACITY="0.96"
export TINO_TERMINAL_FPS="90"
export TINO_TERMINAL_EFFECTS="balanced"

# Host-only metadata.
export TINO_HOST_PROFILE="work_laptop"
export TINO_POWER_MODE="balanced"

# Neovim startup SLO guardrail defaults for this host profile.
export TINO_NVIM_PROFILE_DEFAULT_MAX_STARTUP_MS="140"
# Cloud prompt opt-ins (accepted true values: 1|true|yes|on; false values: 0|false|no|off).
# export STARSHIP_ENABLE_K8S="1"
# export STARSHIP_ENABLE_AWS="1"

