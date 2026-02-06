#!/usr/bin/env bash
set -euo pipefail

# Code AI CLI Installation Script
# Installs Code AI using pip or pipx

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Display banner
show_banner() {
  echo -e "${CYAN}${BOLD}"
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║                                                               ║"
  echo "║   ${MAGENTA}░█▀▀░█▀█░█▀▄░█▀▀░▀█▀░█▀█  ${CYAN}AI-Powered Data Assistant      ${CYAN}║"
  echo "║   ${MAGENTA}░█░░░█░█░█░█░█▀▀░░█░░█░█  ${CYAN}Cheaper • Faster • Collaborative${CYAN}║"
  echo "║   ${MAGENTA}░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀▀▀░▀▀▀  ${CYAN}                               ${CYAN}║"
  echo "║                                                               ║"
  echo "║                    Installation Script                        ║"
  echo "╚═══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

log() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
  exit 1
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Main installation function
main() {
  show_banner
  
  log "Checking for Python installation..."
  
  if ! command_exists python3 && ! command_exists python; then
    error "Python 3 is required but not installed. Please install Python 3.10 or higher."
  fi
  
  # Determine Python command
  PYTHON_CMD="python3"
  if ! command_exists python3; then
    PYTHON_CMD="python"
  fi
  
  # Check Python version
  PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
  log "Found Python $PYTHON_VERSION"
  
  # Try to install with pipx first (isolated environment)
  if command_exists pipx; then
    log "Installing Code AI with pipx (recommended)..."
    pipx install codeai || pipx install git+https://github.com/datalayer/codeai.git
    success "Code AI installed successfully with pipx!"
  # Fall back to pip
  elif command_exists pip3 || command_exists pip; then
    warn "pipx not found, falling back to pip (less isolated)"
    log "Installing Code AI with pip..."
    
    PIP_CMD="pip3"
    if ! command_exists pip3; then
      PIP_CMD="pip"
    fi
    
    $PIP_CMD install --user codeai || $PIP_CMD install --user git+https://github.com/datalayer/codeai.git
    success "Code AI installed successfully with pip!"
    
    # Check if user's pip bin directory is in PATH
    USER_BIN="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
      warn "Make sure $USER_BIN is in your PATH:"
      echo -e "${YELLOW}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
      echo ""
    fi
  else
    error "Neither pipx nor pip found. Please install pip or pipx first."
  fi
  
  # Check for OpenAI API key
  echo ""
  if [ -z "${OPENAI_API_KEY:-}" ]; then
    warn "Don't forget to set your OPENAI_API_KEY environment variable:"
    echo -e "${YELLOW}  export OPENAI_API_KEY='your-api-key-here'${NC}"
    echo ""
  else
    log "OpenAI API key detected ✓"
  fi
  
  # Print usage information
  echo -e "${GREEN}${BOLD}Installation complete!${NC}"
  echo ""
  echo -e "${CYAN}Get started with:${NC}"
  echo -e "  ${BOLD}codeai${NC}                          # Interactive mode"
  echo -e "  ${BOLD}codeai \"your question here\"${NC}    # Single query mode"
  echo ""
  echo -e "${CYAN}Visit https://datalayer.ai for more information${NC}"
}

# Run main function
main "$@"
