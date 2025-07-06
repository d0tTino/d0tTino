$ErrorActionPreference = 'Stop'

$session = 'workspace'

if (-not (Get-Command tmux -ErrorAction SilentlyContinue)) {
    Write-Error 'tmux is required but not installed.'
    exit 1
}

# Reattach if the session already exists
$null = tmux has-session -t $session 2>$null
if ($LASTEXITCODE -eq 0) {
    tmux attach -t $session
    exit
}

tmux new-session -d -s $session

# Layout: big pane on the left, two stacked on the right, two bottom panes

tmux split-window -h -t "$session":0

# right column split
tmux split-window -v -t "$session":0.1

# left side bottom
tmux select-pane -t "$session":0.0

tmux split-window -v -t "$session":0.0

# bottom-right split for fifth pane

tmux select-pane -t "$session":0.2

tmux split-window -h -t "$session":0.2

tmux select-pane -t "$session":0

tmux attach -t $session
