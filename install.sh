#!/bin/bash

# Modified version of https://stackoverflow.com/a/3330834/5509575
sp='/-\|'
spin() {
	printf '\b%.1s' "$sp"
	sp=${sp#?}${sp%???}
}
endspin() {
	printf '\r%s\n' "$@"
}

runin() {
	# Runs the arguments and spins once per line of stdout (tee'd to logfile), also piping stderr to logfile
	{ "$@" 2>>../hikka-install.log || return $?; } | while read -r line; do
		spin
		printf "%s\n" "$line" >>../hikka-install.log
	done
}

runout() {
	# Runs the arguments and spins once per line of stdout (tee'd to logfile), also piping stderr to logfile
	{ "$@" 2>>hikka-install.log || return $?; } | while read -r line; do
		spin
		printf "%s\n" "$line" >>hikka-install.log
	done
}

errorin() {
	endspin "$@"
	cat ../hikka-install.log
}
errorout() {
	endspin "$@"
	cat hikka-install.log
}

##############################################################################

clear
clear
# Adapted from https://github.com/Silejonu/bash_loading_animations/blob/main/bash_loading_animations.sh

BLA_metro=('[       ]' '[=      ]' '[==     ]' '[===    ]' '[====   ]' '[=====  ]' '[ ===== ]' '[ ======]' '[  =====]' '[   ====]' '[    ===]' '[     ==]' '[      =]' '[       ]' '[ ======]' '[ ===== ]' '[=====  ]' '[====   ]' '[===    ]' '[==     ]' '[=      ]' '[       ]')

BLA::play_loading_animation_loop() {
  while true ; do
    for frame in ${!BLA_metro[*]} ; do
      printf "\r%s" " ${BLA_metro[$frame]}"
      sleep "0.05"
    done
  done
}

BLA::start_loading_animation() {
  tput civis # Hide the terminal cursor
  BLA::play_loading_animation_loop &
  BLA_loading_animation_pid="${!}"
}

BLA::stop_loading_animation() {
  kill "${BLA_loading_animation_pid}" &> /dev/null
  printf "\r%s" "                    "
  printf "\n"
  tput cnorm # Restore the terminal cursor
}

printf "\n\e[1;35;47m                   \e[0m"
printf "\n\e[1;35;47m █ █ █ █▄▀ █▄▀ ▄▀█ \e[0m"
printf "\n\e[1;35;47m █▀█ █ █ █ █ █ █▀█ \e[0m"
printf "\n\e[1;35;47m                   \e[0m"
printf "\n\n\e[3;34;40m Installing...\e[0m\n\n"
BLA::start_loading_animation

##############################################################################

spin

touch hikka-install.log
if [ ! x"$SUDO_USER" = x"" ]; then
	chown "$SUDO_USER:" hikka-install.log
fi

if [ ! x"" = x"$DYNO" ] && ! command -v python >/dev/null; then
	# We are running in a heroku dyno without python, time to get ugly!
	runout git clone https://github.com/heroku/heroku-buildpack-python || {
		endspin "Bootstrap download failed!"
		BLA::stop_loading_animation
		exit 1
	}
	rm -rf .heroku .cache .profile.d requirements.txt runtime.txt .env
	mkdir .cache .env
	echo "python-3.9.6" >runtime.txt
	echo "pip" >requirements.txt
	STACK=heroku-18 runout bash heroku-buildpack-python/bin/compile /app /app/.cache /app/.env ||
		{
			endspin "Bootstrap install failed!"
			BLA::stop_loading_animation
			exit 1
		}
	rm -rf .cache
	export PATH="/app/.heroku/python/bin:$PATH" # Prefer the bootstrapped python, incl. pip, over the system one.
fi
runout pip install gitpython gitdb grapheme Telethon-Mod pythondialog meval aiogram aiohttp aiohttp_jinja2 requests Jinja2 websockets uvloop
if [ -d "Hikka/hikka" ]; then
	cd Hikka || {
		endspin "Error: Install git package and re-run installer"
		BLA::stop_loading_animation
		exit 6
	}
	DIR_CHANGED="yes"
fi
if [ -f ".setup_complete" ] || [ -d "hikka" -a ! x"" = x"$DYNO" ]; then
	# If hikka is already installed by this script, or its in Heroku and installed
	PYVER=""
	if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
		PYVER="3"
	fi
	endspin "Existing installation detected"
	clear
	banner
	"python$PYVER" -m hikka "$@"
	BLA::stop_loading_animation
	exit $?
elif [ "$DIR_CHANGED" = "yes" ]; then
	cd ..
fi

##############################################################################

echo "Installing..." >hikka-install.log
declare -A osInfo;
osInfo[/etc/redhat-release]='yum -y install' 
osInfo[/etc/arch-release]="sudo pacman -Sy --noconfirm"
osInfo[/etc/SuSE-release]='zypper install --non-interactive'
osInfo[/etc/debian_version]='sudo apt-get install -y'
for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        PKGMGR=${osInfo[$f]}
    fi
done
##############################################################################

runout $PKGMGR "python$PYVER" git || {  # skipcq
	errorout "Core install failed."
	BLA::stop_loading_animation
	exit 2
}

if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
	runout $PKGMGR "python$PYVER-dev"  # skipcq
	runout $PKGMGR "python$PYVER-pip"  # skipcq
	runout $PKGMGR python3 python3-pip git python3-dev libwebp-dev libz-dev libjpeg-dev libopenjp2-7 libtiff5 ffmpeg imamgemagick libffi-dev libcairo2  # skipcq
elif echo "$OSTYPE" | grep -qE '^linux-android.*'; then
	runout $PKGMGR openssl libjpeg-turbo libwebp libffi libcairo build-essential libxslt libiconv  # skipcq
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
	runout $PKGMGR jpeg webp  # skipcq
fi

runout $PKGMGR neofetch dialog  # skipcq

##############################################################################

SUDO_CMD=""
if [ ! x"$SUDO_USER" = x"" ]; then
	if command -v sudo >/dev/null; then
		SUDO_CMD="sudo -u $SUDO_USER "
	fi
fi

# shellcheck disable=SC2086
${SUDO_CMD}rm -rf Hikka
# shellcheck disable=SC2086
runout ${SUDO_CMD}git clone https://github.com/hikariatama/Hikka/ || {
	errorout "Clone failed."
	BLA::stop_loading_animation
	exit 3
}
cd Hikka || {
	endspin "Error: Install git package and re-run installer"
	BLA::stop_loading_animation
	exit 7
}
# shellcheck disable=SC2086
runin ${SUDO_CMD}"python$PYVER" -m pip install --upgrade pip setuptools wheel --user
# shellcheck disable=SC2086
runin ${SUDO_CMD}"python$PYVER" -m pip install -r requirements.txt --upgrade --user --no-warn-script-location --disable-pip-version-check || {
	errorin "Requirements failed!"
	BLA::stop_loading_animation
	exit 4
}
endspin "Installation successful. Launching setup interface..."
rm -f ../hikka-install.log
touch .setup_complete
BLA::stop_loading_animation
# shellcheck disable=SC2086,SC2015
${SUDO_CMD}"python$PYVER" -m hikka "$@" || {
	echo "Python scripts failed"
	exit 5
}
