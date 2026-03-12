# Terminal Operations Reference

> **Doc scope:** This document is an operational reference for terminal setup and troubleshooting. It is **not** a project bio.

## Terminal modernization goals

The terminal stack is being standardized so shell startup, editor ergonomics, and terminal rendering behavior are predictable across hosts.

Primary goals:

- Keep one canonical setup path for shell + tmux + Neovim + terminal provider.
- Separate shared defaults from machine-specific host overrides.
- Validate renderer/provider behavior through a capability contract.
- Catch common regressions early (slow startup, unsupported renderer keys, missing plugins/assets).

## Architecture

The terminal experience is composed of four layers:

1. **Shell (`zsh`)**
   - Interactive runtime entrypoint from managed dotfiles.
   - Loads shared defaults and optional host overrides.
   - Prompt initialization is Starship-only via `starship init ...`.

### Prompt configuration source of truth

- `dotfiles/shell/.config/starship.toml` is the single prompt configuration source for all supported shells.
- `dotfiles/shell/.zshrc` owns the zsh prompt bootstrap (`eval "$(starship init zsh)"`).
- `powershell/user_profile.ps1` owns the PowerShell prompt bootstrap (`starship init powershell`) and points `STARSHIP_CONFIG` at the tracked Starship config.
- Keep prompt behavior Starship-only across managed shell profiles.

2. **Multiplexer (`tmux`)**
   - Stable session management and keybinding layer.
   - TPM-managed plugin/bootstrap expectations are provisioned during install.

3. **Editor (`nvim`)**
   - Headless provisioning for plugin + Mason/LSP assets.
   - Setup is handled by a dedicated script so installs remain reproducible.

4. **Terminal provider (Ghostty/WezTerm/Kitty/Alacritty/Windows Terminal)**
   - Provider-specific setup/rendering is routed through one script.
   - Shared profile defaults are interpreted through renderer capability contracts.

### Canonical provider policy

Provider defaults are policy-driven and deterministic:

- **Linux/macOS desktop hosts:** canonical provider is **Ghostty**.
- **Windows hosts:** canonical provider is **Windows Terminal**.
- **WezTerm, Kitty, and Alacritty** are supported as **fallback/compatibility targets** when the canonical provider is unavailable or when explicitly requested.

Implementation details:

- `dotfiles/terminal/.config/tino/terminal-profile.sh --canonical-provider` resolves the host canonical provider.
- `scripts/setup-terminal-provider.sh` logs provider resolution decisions and uses explicit fallback logs when it must deviate from the requested/canonical provider.
- `scripts/qa_terminal_modernization.sh` warns when active host defaults (`TINO_TERMINAL_PROVIDER` from defaults + host override) do not match canonical provider policy.

## Host overrides model (`hosts/desktop`, `hosts/work_laptop`)

Configuration precedence is:

1. Base defaults: `dotfiles/terminal/.config/tino/terminal-defaults.sh`
2. Optional host overlay: `hosts/<host>/.config/tino/host-overrides.sh`
3. Explicit CLI provider flag (if passed during install)

Use overlays to keep per-machine deltas small:

- `hosts/desktop`: higher visual fidelity/high-refresh-friendly defaults.
- `hosts/work_laptop`: balanced settings for battery and thermals.

This model ensures you can keep a single operational workflow while still tuning ergonomics per device.

## Canonical commands

From repository root:

```bash
# 1) Common bootstrap entrypoint
./scripts/install_common.sh

# 2) Terminal provider setup (explicit provider)
./scripts/setup-terminal-provider.sh ghostty

# 3) Neovim provisioning (plugins + Mason/LSP assets)
./scripts/setup-nvim.sh
```

Recommended flow:

1. Run `install_common.sh` for baseline dependencies and managed dotfiles.
2. Run `setup-terminal-provider.sh <provider>` if you need to switch or re-render provider configs.
3. Run `setup-nvim.sh` after Neovim/plugin ecosystem changes.

## Validation checklist

Use this checklist after install/update and before considering terminal setup complete.

For any shell/tmux/nvim/terminal-profile config change, run the canonical acceptance gate:

```bash
./scripts/qa_terminal_modernization.sh
```

The gate emits a human-readable summary to stdout and a machine-readable JSON report at `.cache/tino/qa-terminal-modernization/report.json` for CI ingestion.

Neovim startup threshold resolution in `qa_terminal_modernization.sh` is deterministic:

1. `TINO_QA_NVIM_MAX_STARTUP_MS` (QA-only hard override)
2. `TINO_NVIM_MAX_STARTUP_MS` (global benchmark override)
3. Host profile default from `hosts/<profile>/.config/tino/host-overrides.sh`
   - desktop profile default: `100ms`
   - work_laptop profile default: `140ms`
4. Fallback baseline when no host profile is detected: `100ms`

Use `TINO_NVIM_MAX_STARTUP_MS` to temporarily tighten or relax the startup SLO without editing host profiles.

### 1) Startup timing

- Run warm-start timing checks for interactive shell startup.
- Verify startup remains within your local warm/cold budget targets.
- Re-check after plugin or shell init changes.

### 2) Renderer contract checks

Validate capability behavior (for example, FPS/opacity/effects support) with:

```bash
dotfiles/terminal/.config/tino/validate-renderer-contract.sh --report-format json --report-file .cache/tino/terminal-capability-report.json
dotfiles/terminal/.config/tino/validate-renderer-contract.sh --report-format markdown --report-file docs/generated/terminal-capability-matrix.md
```

Ensure the selected provider reports expected support and that unsupported features degrade gracefully.

### 3) Missing plugin detection

- Confirm shell plugin directories exist (or were cloned by bootstrap).
- Confirm tmux plugin manager assets are present (`~/.tmux/plugins/tpm/tpm`).
- Confirm Neovim headless setup completed without missing provider/plugin errors.

If any plugin class is missing, re-run the canonical setup scripts above in order.
For TPM specifically, `./scripts/install_common.sh` is the canonical recovery path.


## Starship prompt modules and cloud-context toggles

`dotfiles/shell/.config/starship.toml` keeps only these always-on core modules in the prompt format:

- `directory`
- `git_branch`
- `git_status`
- `status`
- `time`

Cloud modules are context-gated so they do not appear in unrelated shells:

- `kubernetes` appears when kube context environment is present (`KUBECONFIG`) or when explicitly enabled via `STARSHIP_ENABLE_K8S`.
- `aws` appears when AWS context environment is present (`AWS_PROFILE` or `AWS_VAULT`) or when explicitly enabled via `STARSHIP_ENABLE_AWS`.

### Recommended profile defaults

Use host overlays to set stable defaults based on machine role:

- **desktop profile (`hosts/desktop`)**
  - Keep cloud toggles opt-in by default to reduce prompt noise in general development shells.
  - Enable per-session when needed:
    - `export STARSHIP_ENABLE_K8S=1`
    - `export STARSHIP_ENABLE_AWS=1`
- **work laptop profile (`hosts/work_laptop`)**
  - Keep cloud toggles opt-in unless your daily workflow is cloud-heavy.
  - If cloud tooling is routine, set one or both toggles in host overrides so context is visible automatically:
    - `export STARSHIP_ENABLE_K8S=1`
    - `export STARSHIP_ENABLE_AWS=1`

Tip: prefer setting these in host-specific override files instead of global shell defaults so behavior stays intentional per machine.

## Troubleshooting

### Terminal settings not applying

- Re-run `./scripts/setup-terminal-provider.sh <provider>`.
- Check whether host overrides are unintentionally overriding a base default.
- Validate provider capabilities to confirm the setting is actually supported.

### Slow startup after updates

- Re-profile interactive shell startup.
- Check for newly added plugin init on the prompt-critical path.
- Ensure deferred/non-critical init remains deferred.

### Neovim plugins/LSP tooling missing

- Re-run `./scripts/setup-nvim.sh`.
- Verify network/package manager access used by plugin managers/Mason.
- Re-open Neovim and check health diagnostics.
