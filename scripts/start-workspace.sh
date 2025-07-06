#!/usr/bin/env bash
set -euo pipefail

session="workspace"

# Attach if the session already exists
if tmux has-session -t "$session" 2>/dev/null; then
    exec tmux attach -t "$session"
fi

# Start new detached session
TMUX= tmux new-session -d -s "$session"

# Layout: big pane on the left, two stacked panes on the right, two panes on the bottom row
# Create right column
TMUX= tmux split-window -h -t "$session":0
# Split right column into two
TMUX= tmux split-window -v -t "$session":0.1
# Split left pane horizontally to create bottom-left
TMUX= tmux select-pane -t "$session":0.0
TMUX= tmux split-window -v -t "$session":0.0
# Split bottom-right pane vertically for fifth pane
TMUX= tmux select-pane -t "$session":0.2
TMUX= tmux split-window -h -t "$session":0.2

TMUX= tmux select-pane -t "$session":0
exec tmux attach -t "$session"
