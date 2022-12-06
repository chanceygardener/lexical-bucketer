#!/bin/zsh
#
e=${1:-.env};
autoload -U add-zsh-hook
load-local-conf() {
     # check file exists, is regular file and is readable:
     if [[ -f .env && -r .env ]]; then
       source .env
     fi
}
add-zsh-hook chpwd load-local-conf

echo "Loaded variables from $e";