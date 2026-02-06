#!/usr/bin/env python3
"""Test script to demonstrate Code AI spinner animations."""

import sys
import time
from pathlib import Path

# Add parent directory to path to import codeai
sys.path.insert(0, str(Path(__file__).parent))

from codeai.cli import Spinner, GREEN, CYAN, MAGENTA, YELLOW, RESET, BOLD

def test_spinner(style: str, duration: float = 3.0):
    """Test a specific spinner style."""
    print(f"\n{CYAN}{BOLD}Testing {style} spinner:{RESET}")
    spinner = Spinner(f"Loading with {style} style", style=style)
    spinner.start()
    time.sleep(duration)
    spinner.stop()
    print(f"{GREEN}✓{RESET} {style} spinner complete\n")

def main():
    """Run all spinner tests."""
    print(f"{MAGENTA}{BOLD}Code AI Spinner Animation Test{RESET}")
    print(f"{CYAN}{'='*50}{RESET}\n")
    
    # Test each spinner style
    styles = ["dots", "circle", "bounce", "pulse", "growing"]
    
    for style in styles:
        test_spinner(style, duration=2.5)
    
    print(f"\n{GREEN}{BOLD}All spinner tests completed!{RESET}")
    print(f"{YELLOW}The 'growing' style (○ ◔ ◑ ◕ ●) is the default and resembles")
    print(f"the 'black hole' effect you saw in amp.{RESET}\n")

if __name__ == "__main__":
    main()
