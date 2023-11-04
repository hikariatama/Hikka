#!/bin/bash


runin() {
	# Runs the arguments, piping stderr to logfile
	{ "$@" 2>>../huikka-install.log || return $?; } | while read -r line; do
		printf "%s\n" "$line" >>../huikka-install.log
	done
}

runout() {
	# Runs the arguments, piping stderr to logfile
	{ "$@" 2>>huikka-install.log || return $?; } | while read -r line; do
		printf "%s\n" "$line" >>huikka-install.log
	done
}

errorin() {
	cat ../huikka-install.log
}
errorout() {
	cat huikka-install.log
}

SUDO_CMD=""
if [ ! x"$SUDO_USER" = x"" ]; then
	if command -v sudo >/dev/null; then
		SUDO_CMD="sudo -u $SUDO_USER "
	fi
fi

##############################################################################

clear
clear

printf "\n\e[1;35;47m                   \e[0m"
printf "\n\e[1;35;47m █ █ █ █▄▀ █▄▀ ▄▀█ \e[0m"
printf "\n\e[1;35;47m █▀█ █ █ █ █ █ █▀█ \e[0m"
printf "\n\e[1;35;47m                   \e[0m"
printf "\n\n\e[3;34;40m Installing...\e[0m\n\n"

##############################################################################

printf "\r\033[0;34mPreparing for installation...\e[0m"

touch huikka-install.log
if [ ! x"$SUDO_USER" = x"" ]; then
	chown "$SUDO_USER:" huikka-install.log
fi

if [ -d "Huikka/huikka" ]; then
	cd Huikka || {
		printf "\rError: Install git package and re-run installer"
		exit 6
	}
	DIR_CHANGED="yes"
fi
if [ -f ".setup_complete" ]; then
	# If huikka is already installed by this script
	PYVER=""
	if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
		PYVER="3"
	fi
	printf "\rExisting installation detected"
	clear
	"python$PYVER" -m huikka "$@"
	exit $?
elif [ "$DIR_CHANGED" = "yes" ]; then
	cd ..
fi

##############################################################################

echo "Installing..." >huikka-install.log

if echo "$OSTYPE" | grep -qE '^linux-gnu.*' && [ -f '/etc/debian_version' ]; then
	PKGMGR="apt install -y"
	runout dpkg --configure -a
	runout apt update
	PYVER="3"
elif echo "$OSTYPE" | grep -qE '^linux-gnu.*' && [ -f '/etc/arch-release' ]; then
	PKGMGR="pacman -Sy --noconfirm"
	PYVER="3"
elif echo "$OSTYPE" | grep -qE '^linux-android.*'; then
	runout apt update
	PKGMGR="apt install -y"
	PYVER=""
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
	if ! command -v brew >/dev/null; then
		ruby <(curl -fsSk https://raw.github.com/mxcl/homebrew/go)
	fi
	PKGMGR="brew install"
	PYVER="3"
else
	printf "\r\033[1;31mUnrecognised OS.\e[0m Please follow 'Manual installation' at \033[0;94mhttps://github.com/hikariatama/Huikka/#-installation\e[0m"
	exit 1
fi

##############################################################################

runout "$SUDO_CMD $PKGMGR python$PYVER" git || {
	errorout "Core install failed."
	exit 2
}


printf "\r\033[K\033[0;32mPreparation complete!\e[0m"
printf "\n\r\033[0;34mInstalling linux packages...\e[0m"

if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
	runout "$SUDO_CMD $PKGMGR python$PYVER-dev"
	runout "$SUDO_CMD $PKGMGR python$PYVER-pip"
	runout "$SUDO_CMD $PKGMGR python3 python3-pip git python3-dev \
		libwebp-dev libz-dev libjpeg-dev libopenjp2-7 libtiff5 \
		ffmpeg imamgemagick libffi-dev libcairo2"
elif echo "$OSTYPE" | grep -qE '^linux-android.*'; then
	runout "$SUDO_CMD $PKGMGR openssl libjpeg-turbo libwebp libffi libcairo build-essential libxslt libiconv git ncurses-utils"
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
	runout "$SUDO_CMD$ $PKGMGR jpeg webp"
fi

printf "\r\033[K\033[0;32mPackages installed!\e[0m"
printf "\n\r\033[0;34mCloning repo...\e[0m"


##############################################################################

# shellcheck disable=SC2086
${SUDO_CMD}rm -rf Huikka
# shellcheck disable=SC2086
runout ${SUDO_CMD}git clone https://github.com/hikariatama/Huikka/ || {
	errorout "Clone failed."
	exit 3
}
cd Huikka || {
	printf "\r\033[0;33mRun: \033[1;33mpkg install git\033[0;33m and restart installer"
	exit 7
}

printf "\r\033[K\033[0;32mRepo cloned!\e[0m"
printf "\n\r\033[0;34mInstalling python dependencies...\e[0m"

# shellcheck disable=SC2086
runin "$SUDO_CMD python$PYVER" -m pip install --upgrade pip setuptools wheel --user
# shellcheck disable=SC2086
runin "$SUDO_CMD python$PYVER" -m pip install -r requirements.txt --upgrade --user --no-warn-script-location --disable-pip-version-check || {
	errorin "Requirements failed!"
	exit 4
}
rm -f ../huikka-install.log
touch .setup_complete

printf "\r\033[K\033[0;32mDependencies installed!\e[0m"
printf "\n\033[0;32mStarting...\e[0m\n\n"

${SUDO_CMD}"python$PYVER" -m huikka "$@" || {
	printf "\033[1;31mPython scripts failed\e[0m"
	exit 5
}
