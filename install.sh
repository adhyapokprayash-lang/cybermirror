#!/bin/bash

# SiteMirror - Installation Script
# Author: Cyber Anxhu
# For authorized security testing only

set -e

GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
CYAN='\033[96m'
MAGENTA='\033[95m'
BOLD='\033[1m'
DIM='\033[2m'
END='\033[0m'

echo -e "${MAGENTA}${BOLD}"
echo " ██████  ██    ██ ██████  ███████ ██████   ███    ███ ██ ██████  ██████   ██████  ██████"
echo "██       ██    ██ ██   ██ ██      ██   ██ ████  ████ ██ ██   ██ ██   ██ ██    ██ ██   ██"
echo "██   ███ ██    ██ ██████  █████   ██████  ██ ████ ██ ██ ██████  ██████  ██    ██ ██████"
echo "██    ██ ██    ██ ██      ██      ██   ██ ██  ██  ██ ██ ██   ██ ██   ██ ██    ██ ██   ██"
echo " ██████   ██████  ██      ███████ ██   ██ ██      ██ ██ ██   ██ ██   ██  ██████  ██   ██"
echo -e "${END}"
echo -e "${GREEN}${BOLD}           SiteMirror - Installation Script${END}"
echo -e "${CYAN}                   Author: Cyber Anxhu${END}"
echo ""

# Detect OS
OS="unknown"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
elif [ -d /data/data/com.termux ]; then
    OS="termux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo -e "${YELLOW}[*] Detected OS: ${OS}${END}"

install_python_deps() {
    echo -e "${YELLOW}[*] Installing Python and dependencies...${END}"
    
    if [ "$OS" == "termux" ]; then
        pkg update -y
        pkg install -y python python-pip git wget
    elif [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ] || [ "$OS" == "kali" ]; then
        sudo apt update -y
        sudo apt install -y python3 python3-pip git wget curl
    elif [ "$OS" == "macos" ]; then
        brew install python3 git wget
    elif [ "$OS" == "arch" ]; then
        sudo pacman -S --noconfirm python python-pip git wget
    else
        echo -e "${RED}[-] Unsupported OS. Install Python 3 manually.${END}"
        exit 1
    fi
    
    pip3 install requests beautifulsoup4 urllib3 --break-system-packages 2>/dev/null || pip install requests beautifulsoup4 urllib3
    echo -e "${GREEN}[+] Python dependencies installed${END}"
}

install_cloudflared() {
    echo -e "${YELLOW}[*] Installing cloudflared...${END}"
    
    if command -v cloudflared &> /dev/null; then
        echo -e "${GREEN}[+] cloudflared already installed${END}"
        return
    fi
    
    if [ "$OS" == "termux" ]; then
        pkg install -y golang
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
        chmod +x cloudflared-linux-arm64
        mv cloudflared-linux-arm64 $PREFIX/bin/cloudflared
    elif [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ] || [ "$OS" == "kali" ]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
        chmod +x cloudflared-linux-amd64
        sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
    elif [ "$OS" == "macos" ]; then
        brew install cloudflared
    elif [ "$OS" == "arch" ]; then
        yay -S cloudflared-bin
    fi
    
    echo -e "${GREEN}[+] cloudflared installed${END}"
}

install_ngrok() {
    echo -e "${YELLOW}[*] Installing ngrok (fallback tunnel)...${END}"
    
    if command -v ngrok &> /dev/null; then
        echo -e "${GREEN}[+] ngrok already installed${END}"
        return
    fi
    
    ARCH=$(uname -m)
    
    if [ "$OS" == "termux" ] || [ "$ARCH" == "aarch64" ]; then
        wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
        tar -xzf ngrok-v3-stable-linux-arm64.tgz
        mv ngrok $PREFIX/bin/ 2>/dev/null || sudo mv ngrok /usr/local/bin/
        chmod +x $PREFIX/bin/ngrok 2>/dev/null || sudo chmod +x /usr/local/bin/ngrok
        rm -f ngrok-v3-stable-linux-arm64.tgz
    else
        wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar -xzf ngrok-v3-stable-linux-amd64.tgz
        sudo mv ngrok /usr/local/bin/
        sudo chmod +x /usr/local/bin/ngrok
        rm -f ngrok-v3-stable-linux-amd64.tgz
    fi
    
    echo -e "${GREEN}[+] ngrok installed${END}"
}

install_python_deps
install_cloudflared
install_ngrok

echo ""
echo -e "${GREEN}${BOLD}[+] Installation complete!${END}"
echo -e "${YELLOW}[*] Run the tool with:${END}"
echo -e "    ${CYAN}python3 sitemirror.py${END}"
echo ""
echo -e "${DIM}For authorized security testing only.${END}"
