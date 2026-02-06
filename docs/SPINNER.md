# Code AI Spinner Animations

## Overview

Code AI features beautiful animated spinners that provide visual feedback while processing your queries. The animations are inspired by professional CLI tools like Ampcode.

## The "Black Hole" Effect

The default spinner uses a "growing circle" animation that creates a mesmerizing pulsing effect:

```
Frame 1: ○  (empty circle)
Frame 2: ◔  (quarter filled)
Frame 3: ◑  (half filled)
Frame 4: ◕  (three-quarters filled)
Frame 5: ●  (fully filled)
Frame 6: ◕  (three-quarters filled)
Frame 7: ◑  (half filled)
Frame 8: ◔  (quarter filled)
... repeats ...
```

This creates a smooth, continuous animation that resembles:
- A pulsing sphere
- A rotating black hole
- A breathing circle
- A loading orb

## Live Example

When you run a query:

```bash
$ codeai "What is Python?"
● Thinking...
```

The circle smoothly animates through its phases while waiting for the AI response.

## Testing the Animations

Run the test script to see all available spinner styles:

```bash
python test_spinner.py
```

This will demonstrate:
1. **dots** - Braille pattern spinner (⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
2. **circle** - Rotating circle (◐ ◓ ◑ ◒)
3. **bounce** - Bouncing dots (⠁ ⠂ ⠄ ⡀ ⢀ ⠠ ⠐ ⠈)
4. **pulse** - Pulsing dot (● ◉ ○ ◉)
5. **growing** - Growing/pulsing circle (○ ◔ ◑ ◕ ●) ⭐ **Default**

## Technical Details

### Implementation

The spinner runs in a separate daemon thread to avoid blocking the main application:

```python
class Spinner:
    def _spin(self):
        for frame in itertools.cycle(self.frames):
            if not self.spinner_active:
                break
            sys.stdout.write(f'\r{GREEN}{frame}{RESET} {message}...')
            sys.stdout.flush()
            time.sleep(0.1)
```

### Features

- ✅ Non-blocking: Runs in background thread
- ✅ TTY-aware: Only shows in interactive terminals
- ✅ Clean exit: Properly clears the line when done
- ✅ Context manager: Use with `with` statement
- ✅ Colorized: Green spinner with dimmed text
- ✅ Smooth: 100ms frame rate for fluid animation

### Usage in Code

```python
# Method 1: Context manager (recommended)
with Spinner("Processing", style="growing"):
    result = do_long_operation()

# Method 2: Manual control
spinner = Spinner("Loading", style="circle")
spinner.start()
try:
    result = do_long_operation()
finally:
    spinner.stop()
```

## Customization

To change the default spinner style, modify the `style` parameter:

```python
spinner = Spinner("Thinking", style="pulse")  # Use pulsing dot
spinner = Spinner("Loading", style="dots")    # Use braille dots
spinner = Spinner("Working", style="growing") # Use black hole effect (default)
```

## Why It Matters

Good visual feedback:
- **Reduces perceived wait time** - Users know something is happening
- **Prevents confusion** - Clear indication that app isn't frozen
- **Professional appearance** - Polished UX like commercial tools
- **Engaging** - The animation is pleasant to watch

## Comparison with Ampcode

| Feature | Ampcode | Code AI |
|---------|---------|--------|
| Loading Animation | ✓ Green spinner | ✓ Green spinner |
| Style | Custom | Growing circle |
| Frame Rate | ~100ms | 100ms |
| Color | Green | Green |
| Effect | Rotating | Pulsing "black hole" |

Both tools prioritize smooth, professional visual feedback that makes waiting for AI responses more pleasant.
