# Basic shell settings that should work everywhere

# Only continue if running interactively
case $- in
    *i*) ;;
      *) return ;;
esac

# History settings
export HISTSIZE=1000
export HISTFILESIZE=2000
export HISTCONTROL=ignoredups:erasedups
shopt -s histappend

# Useful aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Simple prompt
PS1='\u@\h:\w\$ '
