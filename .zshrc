export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Applications/Postgres.app/Contents/Versions/latest/bin"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/lib/postgresql@14"
export CPPFLAGS="-I/opt/homebrew/include/postgresql@14"

export PATH="$PATH:/Applications/microchip/xc8/v2.46/bin"
eval "$(/opt/homebrew/bin/brew shellenv)"


[ -f "/Users/williampark/.ghcup/env" ] && . "/Users/williampark/.ghcup/env" 
export PATH="$PATH:/opt/gradle/gradle-8.8/bin"


# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/anaconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

