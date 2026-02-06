# Code AI CLI Visuals

This document showcases the visual elements of Code AI.

## Welcome Banner

When you launch `codeai` in interactive mode, you'll see:

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ░█▀▀░█▀█░█▀▄░█▀▀░█▀█░▀█▀  AI-Powered Data Assistant         ║
║   ░█░░░█░█░█░█░█▀▀░█▀█░░█░  Cheaper • Faster • Collaborative  ║
║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀░▀▀▀                                    ║
║                                                               ║
║   ✨ Data Analysis  📊 Data Science  📓 Jupyter               ║
║                                                               ║
║   Type /exit to quit  •  Type / for commands                  ║
╚═══════════════════════════════════════════════════════════════╝

Powered by Datalayer  •  https://datalayer.ai
```

## Installation Script Banner

The installation script displays a similar banner with colorized output:

- **Cyan**: Box border and main text
- **Magenta**: ASCII art logo
- **Green**: Success messages
- **Blue**: Info messages
- **Yellow**: Warnings

## Loading Animation

While processing your queries, Code AI displays an animated spinner:

```
● Thinking...
```

The spinner uses a "growing circle" animation that creates a pulsing effect:
- `○` → `◔` → `◑` → `◕` → `●` → `◕` → `◑` → `◔` → (repeat)

This creates a smooth, mesmerizing animation similar to a rotating sphere or "black hole" effect.

### Available Spinner Styles

- **growing** (default): `○ ◔ ◑ ◕ ●` - Pulsing circle
- **circle**: `◐ ◓ ◑ ◒` - Rotating circle
- **dots**: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` - Braille dots
- **pulse**: `● ◉ ○` - Pulsing dot
- **bounce**: `⠁ ⠂ ⠄ ⡀ ⢀ ⠠ ⠐ ⠈` - Bouncing effect

## CLI Features

### Interactive Commands

- `/exit` - Exit the session
- `/markdown` - Show last response in markdown
- `/multiline` - Toggle multiline input mode
- `/cp` - Copy last response to clipboard

### Color-Coded Messages

- **Info** (Blue): General information
- **Success** (Green): Operations completed successfully
- **Warning** (Yellow): Important notices
- **Error** (Red): Error messages
- **Spinner** (Green): Loading animation

## Inspiration

The visual design is inspired by professional CLI tools like [Ampcode](https://ampcode.com), combining:
- ASCII art branding
- Box drawing characters for structure
- ANSI color codes for visual appeal
- Clear, concise information display
