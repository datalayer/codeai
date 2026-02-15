# Copyright (c) 2025-2026 Datalayer, Inc.
#
# BSD 3-Clause License

"""Terminal UX (TUX) for Code AI - Claude Code inspired interface."""

import asyncio
import getpass
import json
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Any

import httpx
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style as PTStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner as RichSpinner
from rich.style import Style
from rich.box import ROUNDED, HEAVY

from .banner import (
    GREEN_DARK,
    GREEN_MEDIUM,
    GREEN_LIGHT,
    GRAY,
    WHITE,
    RESET,
    GOODBYE_MESSAGE,
)
from .animations import rain_animation, about_animation, gif_animation

# Rich styles matching Datalayer brand
# Brand color reference (from BRAND_MANUAL.md):
# - Green brand #16A085 (dark) - Brand accent, icons, dividers, headings
# - Green accent #1ABC9C (medium) - Icons, charts, highlights on dark surfaces
# - Green text #117A65 - Accessible green for text & buttons
# - Green bright #2ECC71 (light) - Highlights and glow on dark backgrounds
# - Gray #59595C - Supporting text, hints, metadata
#
# For dark terminal backgrounds, use brighter greens (#1ABC9C, #2ECC71) for visibility
STYLE_PRIMARY = Style(color="rgb(26,188,156)")  # Green accent #1ABC9C - primary accent in dark mode
STYLE_SECONDARY = Style(color="rgb(22,160,133)")  # Green brand #16A085 - secondary accent
STYLE_ACCENT = Style(color="rgb(46,204,113)")  # Green bright #2ECC71 - highlights
STYLE_MUTED = Style(color="rgb(89,89,92)")  # Gray #59595C - supporting text
STYLE_WHITE = Style(color="white")  # Primary text in dark mode
STYLE_ERROR = Style(color="red")  # Error states
STYLE_WARNING = Style(color="yellow")  # Warning states

# Context grid symbols
SYMBOL_SYSTEM = "⛁"
SYMBOL_TOOLS = "⛀"
SYMBOL_MESSAGES = "⛁"
SYMBOL_FREE = "⛶"
SYMBOL_BUFFER = "⛝"


@dataclass
class SlashCommand:
    """Definition of a slash command."""
    name: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    handler: Optional[Callable] = None
    shortcut: Optional[str] = None  # e.g., "c-e" for Ctrl+E


class SlashCommandCompleter(Completer):
    """Completer for slash commands with menu-style display."""
    
    def __init__(self, commands: dict[str, "SlashCommand"]):
        self.commands = commands
    
    def get_completions(self, document, complete_event):
        """Yield completions for slash commands."""
        text = document.text_before_cursor
        
        # Only show completions when input starts with /
        if not text.startswith("/"):
            return
        
        # Get the partial command (without the leading /)
        partial = text[1:].lower()
        
        # Track which commands we've shown (to avoid duplicates from aliases)
        shown = set()
        
        for name, cmd in sorted(self.commands.items()):
            # Only show primary command names, not aliases
            if cmd.name in shown:
                continue
            
            # Match if partial matches start of command name or is empty
            if name.startswith(partial) and cmd.name == name:
                shown.add(cmd.name)
                
                # Truncate description to fit in menu
                desc = cmd.description
                if len(desc) > 70:
                    desc = desc[:67] + "..."
                
                yield Completion(
                    text=f"/{cmd.name}",
                    start_position=-len(text),
                    display=HTML(f"<ansicyan>/{cmd.name}</ansicyan>"),
                    display_meta=HTML(f"<ansibrightblack>{desc}</ansibrightblack>"),
                )


@dataclass
class ToolCallInfo:
    """Information about a tool call."""
    tool_call_id: str
    tool_name: str
    args_json: str = ""
    result: Optional[str] = None
    status: str = "in_progress"  # in_progress, complete, error
    expanded: bool = False
    
    def format_args(self, max_value_len: int = 40) -> str:
        """Format arguments for display."""
        if not self.args_json:
            return ""
        try:
            args = json.loads(self.args_json)
            if isinstance(args, dict):
                # Show key=value pairs with truncated values
                items = list(args.items())[:3]
                parts = []
                for k, v in items:
                    val_str = str(v).replace("\n", " ")
                    if len(val_str) > max_value_len:
                        val_str = val_str[:max_value_len - 3] + "..."
                    parts.append(f"{k}={val_str}")
                summary = ", ".join(parts)
                if len(args) > 3:
                    summary += f" (+{len(args) - 3} more)"
                return summary
            return self.args_json[:60] + "..." if len(self.args_json) > 60 else self.args_json
        except json.JSONDecodeError:
            return self.args_json[:60] + "..." if len(self.args_json) > 60 else self.args_json


@dataclass
class SessionStats:
    """Session statistics for token tracking."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    messages: int = 0
    tool_calls: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens


class CodeAITux:
    """Terminal UX for Code AI with Claude Code inspired interface."""
    
    def __init__(
        self,
        agent_url: str,
        server_url: str = "http://127.0.0.1:8000",
        agent_id: str = "codeai",
        eggs: bool = False,
        jupyter_url: Optional[str] = None,
    ):
        """Initialize the TUX.
        
        Args:
            agent_url: URL of the AG-UI agent endpoint
            server_url: Base URL of the agent-runtimes server
            agent_id: Agent ID for API calls
            eggs: Enable Easter egg commands
            jupyter_url: Jupyter server URL (only set when sandbox is jupyter)
        """
        self.agent_url = agent_url
        self.server_url = server_url.rstrip("/")
        self.agent_id = agent_id
        self.eggs = eggs
        self.jupyter_url = jupyter_url
        self.console = Console()
        self.stats = SessionStats()
        self.running = False
        self.model_name: str = "unknown"
        self.context_window: int = 128000
        self.tool_calls: list[ToolCallInfo] = []  # Track tool calls from last response
        self._agui_client: Optional[Any] = None  # Persistent AG-UI client for conversation history
        
        # Initialize slash commands
        self.commands: dict[str, SlashCommand] = {}
        self._register_commands()
        
        # Initialize prompt session with slash command completer
        # Style for the completion menu matching Datalayer brand colors
        self.prompt_style = PTStyle.from_dict({
            "prompt": "#1ABC9C bold",  # Green accent
            "completion-menu.completion": "bg:#2d2d2d #ffffff",
            "completion-menu.completion.current": "bg:#16A085 #ffffff bold",
            "completion-menu.meta.completion": "bg:#2d2d2d #59595C",
            "completion-menu.meta.completion.current": "bg:#16A085 #ffffff",
            "scrollbar.background": "bg:#444444",
            "scrollbar.button": "bg:#16A085",
        })
        self.prompt_session: Optional[PromptSession] = None
    
    def _register_commands(self) -> None:
        """Register all slash commands.
        
        Keyboard shortcuts use Escape sequences (press Escape then the key)
        to avoid conflicts with terminal control characters like:
        - Ctrl+M = Enter, Ctrl+H = Backspace, Ctrl+D = EOF
        - Ctrl+A = Start of line, Ctrl+E = End of line, Ctrl+L = Clear
        """
        commands = [
            SlashCommand(
                name="context",
                description="Visualize current context usage as a colored grid",
                handler=self._cmd_context,
                shortcut="escape x",  # Esc, X
            ),
            SlashCommand(
                name="clear",
                aliases=["reset", "new"],
                description="Clear conversation history and free up context",
                handler=self._cmd_clear,
                shortcut="escape c",  # Esc, C
            ),
            SlashCommand(
                name="help",
                aliases=["?"],
                description="Show available commands",
                handler=self._cmd_help,
                shortcut="escape h",  # Esc, H
            ),
            SlashCommand(
                name="status",
                description="Show Code AI status including model, tokens, and connectivity",
                handler=self._cmd_status,
                shortcut="escape s",  # Esc, S
            ),
            SlashCommand(
                name="exit",
                aliases=["quit", "q"],
                description="Exit Code AI",
                handler=self._cmd_exit,
                shortcut="escape q",  # Esc, Q
            ),
            SlashCommand(
                name="agents",
                description="List available agents on the server",
                handler=self._cmd_agents,
                shortcut="escape a",  # Esc, A
            ),
            SlashCommand(
                name="tools",
                description="List available tools for the current agent",
                handler=self._cmd_tools,
                shortcut="escape t",  # Esc, T
            ),
            SlashCommand(
                name="mcp-servers",
                aliases=["mcp"],
                description="List MCP servers and their status",
                handler=self._cmd_mcp_servers,
                shortcut="escape m",  # Esc, M
            ),
            SlashCommand(
                name="skills",
                description="List available skills (requires codemode enabled)",
                handler=self._cmd_skills,
                shortcut="escape k",  # Esc, K (sKills)
            ),
            SlashCommand(
                name="codemode-toggle",
                aliases=["codemode"],
                description="Toggle codemode on/off for enhanced code capabilities",
                handler=self._cmd_codemode_toggle,
                shortcut="escape o",  # Esc, O (cOdemode)
            ),
            SlashCommand(
                name="context-export",
                aliases=["export"],
                description="Export the current context to a CSV file",
                handler=self._cmd_context_export,
                shortcut="escape e",  # Esc, E
            ),
            SlashCommand(
                name="tools-last",
                aliases=["tl"],
                description="Show details of tool calls from last response",
                handler=self._cmd_tools_last,
                shortcut="escape l",  # Esc, L (Last)
            ),
            SlashCommand(
                name="cls",
                description="Clear the screen",
                handler=self._cmd_cls,
            ),
        ]
        
        # Add Easter egg commands if enabled
        if self.eggs:
            commands.extend([
                SlashCommand(
                    name="rain",
                    description="Matrix rain animation",
                    handler=self._cmd_rain,
                    shortcut="escape r",  # Esc, R
                ),
                SlashCommand(
                    name="about",
                    description="About Datalayer",
                    handler=self._cmd_about,
                    shortcut="escape l",  # Esc, L
                ),
                SlashCommand(
                    name="gif",
                    description="Black hole spinning animation",
                    handler=self._cmd_gif,
                    shortcut="escape g",  # Esc, G
                ),
            ])
        
        # Add /jupyter command only when a Jupyter sandbox is active
        if self.jupyter_url:
            commands.append(
                SlashCommand(
                    name="jupyter",
                    description="Open the Jupyter server in your browser",
                    handler=self._cmd_jupyter,
                    shortcut="escape j",  # Esc, J
                ),
            )

        # /browser opens the web-based chat UI served by the agent-runtimes server
        commands.append(
            SlashCommand(
                name="browser",
                description="Open the Agent chat UI in your browser",
                handler=self._cmd_browser,
                shortcut="escape w",  # Esc, W (web)
            ),
        )

        for cmd in commands:
            self.commands[cmd.name] = cmd
            for alias in cmd.aliases:
                self.commands[alias] = cmd
    
    def _format_tokens(self, tokens: int) -> str:
        """Format token count with K suffix for thousands."""
        if tokens >= 1000:
            return f"{tokens / 1000:.1f}k"
        return str(tokens)
    
    def _get_username(self) -> str:
        """Get the current username."""
        return getpass.getuser()
    
    def _get_cwd(self) -> str:
        """Get current working directory, shortened if needed."""
        cwd = Path.cwd()
        home = Path.home()
        try:
            return f"~/{cwd.relative_to(home)}"
        except ValueError:
            return str(cwd)
    
    def show_welcome(self) -> None:
        """Display the welcome banner similar to Claude Code."""
        username = self._get_username()
        cwd = self._get_cwd()
        
        from . import __version__
        version = __version__.__version__
        
        # ASCII art logo - Datalayer inspired (3 horizontal bars + feet)
        # Compact version: 6 chars wide
        # Row 1: short (2) + long (4) = 6 total
        # Row 2: equal (3 + 3) = 6 total
        # Row 3: long (4) + short (2) = 6 total
        # Row 4: feet - one char on each side
        logo = Text()
        logo.append("   ▄▄", style=STYLE_ACCENT)
        logo.append("▄▄▄▄\n", style=STYLE_SECONDARY)
        logo.append("   ▄▄▄", style=STYLE_ACCENT)
        logo.append("▄▄▄\n", style=STYLE_SECONDARY)
        logo.append("   ▄▄▄▄", style=STYLE_ACCENT)
        logo.append("▄▄\n", style=STYLE_SECONDARY)
        logo.append("   ▀", style=STYLE_ACCENT)
        logo.append("    ▀\n", style=STYLE_SECONDARY)
        
        # Left panel content
        left_content = Text()
        left_content.append(f"\n  Welcome back {username}!\n\n", style=STYLE_WHITE)
        left_content.append(logo)
        left_content.append(f"\n  codeai\n", style=STYLE_MUTED)
        left_content.append(f"  {cwd}\n", style=STYLE_MUTED)
        
        # Right panel content - tips
        right_content = Text()
        right_content.append("Tips for getting started\n", style=STYLE_WHITE)
        right_content.append("Type ", style=STYLE_MUTED)
        right_content.append("/", style=STYLE_PRIMARY)
        right_content.append(" to see all commands\n", style=STYLE_MUTED)
        right_content.append("─" * 40 + "\n", style=STYLE_MUTED)
        right_content.append("Slash Commands\n", style=STYLE_WHITE)
        right_content.append("/context - View context usage\n", style=STYLE_MUTED)
        right_content.append("/status - Check connection status\n", style=STYLE_MUTED)
        right_content.append("/clear - Start fresh conversation\n", style=STYLE_MUTED)
        right_content.append("/exit - Exit from codeai\n", style=STYLE_MUTED)
        
        # Create side-by-side layout
        left_panel = Panel(
            left_content,
            border_style=STYLE_SECONDARY,
            width=40,
        )
        right_panel = Panel(
            right_content,
            border_style=STYLE_SECONDARY,
            width=50,
        )
        
        # Create the main panel
        title = f" Code AI {version} "
        
        main_panel = Panel(
            Columns([left_panel, right_panel], equal=False, expand=True),
            title=title,
            title_align="left",
            border_style=STYLE_PRIMARY,
            box=ROUNDED,
        )
        
        self.console.print(main_panel)
        self.console.print()
    
    def _create_key_bindings(self) -> KeyBindings:
        """Create keyboard shortcuts for slash commands.
        
        Uses Meta/Alt key combinations (e.g., 'escape', 'x' for Alt+X).
        """
        kb = KeyBindings()
        
        # Map shortcuts to command names
        # Shortcuts are stored as tuples for multi-key sequences
        shortcut_map = {}
        for cmd in self.commands.values():
            if cmd.shortcut and cmd.name not in shortcut_map.values():
                # Parse shortcut string into tuple (e.g., "escape x" -> ("escape", "x"))
                keys = tuple(cmd.shortcut.split())
                shortcut_map[keys] = cmd.name
        
        # Create a handler that returns the command string
        def make_handler(cmd_name: str):
            async def handler(event):
                # Set the buffer to the command and accept it
                event.current_buffer.text = f"/{cmd_name}"
                event.current_buffer.validate_and_handle()
            return handler
        
        # Register each shortcut - unpack tuple as separate arguments
        for keys, cmd_name in shortcut_map.items():
            kb.add(*keys)(make_handler(cmd_name))
        
        return kb
    
    async def show_prompt(self) -> str:
        """Display the prompt and get user input with slash command completion."""
        # Initialize prompt session lazily (after commands are registered)
        if self.prompt_session is None:
            completer = SlashCommandCompleter(self.commands)
            key_bindings = self._create_key_bindings()
            self.prompt_session = PromptSession(
                completer=completer,
                style=self.prompt_style,
                complete_while_typing=True,
                complete_in_thread=True,
                key_bindings=key_bindings,
                cursor=CursorShape.BLINKING_BLOCK,
            )
        
        try:
            # Use prompt_toolkit's async prompt method
            return (await self.prompt_session.prompt_async(
                HTML("<ansicyan>❯ </ansicyan>"),
                complete_while_typing=True,
            )).strip()
        except EOFError:
            return "/exit"
        except KeyboardInterrupt:
            return ""
    
    async def _cmd_context(self) -> None:
        """Display context usage visualization."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-table?show_context=false"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error fetching context: {e}[/red]")
            return

        if data.get("error"):
            self.console.print(f"[red]{data.get('error')}[/red]")
            return

        table_text = data.get("table", "").rstrip()
        if table_text:
            self.console.print(Text.from_ansi(table_text))
        else:
            self.console.print("[red]No table content returned.[/red]")
        return
    
    async def _cmd_cls(self) -> None:
        """Clear the screen."""
        self.console.clear()

    async def _cmd_jupyter(self) -> None:
        """Open the Jupyter server API page in the default browser."""
        import webbrowser
        if self.jupyter_url:
            # Append /api so the browser lands on the Jupyter REST API root
            sep = "&" if "?" in self.jupyter_url else "?"
            base = self.jupyter_url.split("?")[0].rstrip("/") + "/api"
            query = self.jupyter_url.split("?")[1] if "?" in self.jupyter_url else None
            url = f"{base}?{query}" if query else base
            self.console.print(f"  Opening [bold cyan]{url}[/bold cyan]")
            webbrowser.open(url)
        else:
            self.console.print("  [yellow]No Jupyter server available.[/yellow]")

    async def _cmd_browser(self) -> None:
        """Open the Agent chat web UI in the default browser."""
        import webbrowser
        url = f"{self.server_url}/static/agent.html?agent={self.agent_id}"
        self.console.print(f"  Opening [bold cyan]{url}[/bold cyan]")
        webbrowser.open(url)

    async def _cmd_clear(self) -> None:
        """Clear conversation history."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-details/reset"
                response = await client.post(url, timeout=10.0)
                response.raise_for_status()
        except Exception as e:
            self.console.print(f"[red]Error clearing context: {e}[/red]")
            return
        
        # Reset local AG-UI client to clear conversation history
        if self._agui_client is not None:
            await self._agui_client.disconnect()
            self._agui_client = None
        
        self.stats = SessionStats()
        self.console.print("● Conversation cleared. Starting fresh.", style=STYLE_PRIMARY)
    
    async def _cmd_help(self) -> None:
        """Show available commands."""
        self.console.print()
        self.console.print("Available Commands:", style=STYLE_WHITE)
        self.console.print()
        
        # Format shortcuts nicely
        def format_shortcut(shortcut: Optional[str]) -> str:
            if not shortcut:
                return ""
            # Convert "escape x" to "Esc,X"
            if shortcut.startswith("escape "):
                return f"Esc,{shortcut[7:].upper()}"
            # Convert "c-x" to "Ctrl+X"
            if shortcut.startswith("c-"):
                return f"Ctrl+{shortcut[2:].upper()}"
            return shortcut
        
        shown = set()
        for name, cmd in sorted(self.commands.items()):
            if cmd.name in shown:
                continue
            shown.add(cmd.name)
            
            # Build command name with aliases
            aliases_str = ""
            if cmd.aliases:
                aliases_str = f" ({', '.join(cmd.aliases)})"
            
            # Build shortcut indicator
            shortcut_str = ""
            if cmd.shortcut:
                shortcut_str = f" [{format_shortcut(cmd.shortcut)}]"
            
            cmd_display = f"/{cmd.name}{aliases_str}"
            self.console.print(f"  {cmd_display}", style=STYLE_PRIMARY, end="")
            
            # Calculate padding for alignment
            padding_len = max(1, 22 - len(cmd_display))
            self.console.print(" " * padding_len, end="")
            self.console.print(cmd.description, style=STYLE_MUTED, end="")
            
            if shortcut_str:
                self.console.print(f"  {shortcut_str}", style=STYLE_SECONDARY)
            else:
                self.console.print()
        
        self.console.print()
    
    async def _cmd_status(self) -> None:
        """Show status information."""
        self.console.print()
        self.console.print("● Code AI Status", style=STYLE_PRIMARY)
        self.console.print()
        
        # Version
        from . import __version__
        self.console.print(f"  Version: {__version__.__version__}", style=STYLE_MUTED)
        
        # Model
        self.console.print(f"  Model: {self.model_name}", style=STYLE_MUTED)
        
        # Server
        self.console.print(f"  Server: {self.server_url}", style=STYLE_MUTED)
        
        # Connection test
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_url}/health", timeout=5.0)
                if response.status_code == 200:
                    self.console.print("  API: [green]Connected[/green]", style=STYLE_MUTED)
                else:
                    self.console.print(f"  API: [yellow]Status {response.status_code}[/yellow]", style=STYLE_MUTED)
        except Exception:
            self.console.print("  API: [red]Disconnected[/red]", style=STYLE_MUTED)
        
        # Session stats
        self.console.print()
        self.console.print(f"  Session tokens: {self._format_tokens(self.stats.total_tokens)}", style=STYLE_MUTED)
        self.console.print(f"  Messages: {self.stats.messages}", style=STYLE_MUTED)
        self.console.print()
    
    async def _cmd_exit(self) -> None:
        """Exit the application."""
        self.running = False
        
        # Clean up AG-UI client
        if self._agui_client is not None:
            await self._agui_client.disconnect()
            self._agui_client = None
        
        self.console.print()
        self.console.print(GOODBYE_MESSAGE, style=STYLE_ACCENT)
        self.console.print("   [link=https://datalayer.ai]https://datalayer.ai[/link]", style=STYLE_MUTED)
        self.console.print()
    
    async def _cmd_agents(self) -> None:
        """List available agents with detailed information."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/agents"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error fetching agents: {e}[/red]")
            return
        
        agents_list = data.get("agents", [])
        
        if not agents_list:
            self.console.print("No agents available", style=STYLE_MUTED)
            return
        
        self.console.print()
        self.console.print(f"● Available Agents ({len(agents_list)}):", style=STYLE_PRIMARY)
        self.console.print()
        
        for agent in agents_list:
            agent_id = agent.get("id", "unknown")
            name = agent.get("name", "Unknown")
            description = agent.get("description", "")
            model = agent.get("model", "unknown")
            status = agent.get("status", "unknown")
            toolsets = agent.get("toolsets", {})
            
            # Status indicator
            status_icon = "[green]●[/green]" if status == "running" else "[red]○[/red]"
            self.console.print(f"  {status_icon} {name} ({agent_id})", style=STYLE_ACCENT)
            
            # Description
            if description:
                desc = description[:60] + "..." if len(description) > 60 else description
                self.console.print(f"    {desc}", style=STYLE_MUTED)
            
            # Model
            self.console.print(f"    Model: {model}", style=STYLE_MUTED)
            
            # Codemode
            codemode = toolsets.get("codemode", False)
            codemode_text = "enabled" if codemode else "disabled"
            codemode_style = STYLE_ACCENT if codemode else STYLE_MUTED
            self.console.print(f"    Codemode: ", style=STYLE_MUTED, end="")
            self.console.print(codemode_text, style=codemode_style)
            
            # MCP Servers
            mcp_servers = toolsets.get("mcp_servers", [])
            if mcp_servers:
                mcp_text = ", ".join(mcp_servers[:5])
                if len(mcp_servers) > 5:
                    mcp_text += f" (+{len(mcp_servers) - 5} more)"
                self.console.print(f"    MCP Servers: {mcp_text}", style=STYLE_MUTED)
            
            # Tools count
            tools_count = toolsets.get("tools_count", 0)
            if tools_count > 0:
                self.console.print(f"    Tools: {tools_count}", style=STYLE_MUTED)
            
            # Skills
            skills = toolsets.get("skills", [])
            if skills:
                skill_names = []
                for s in skills[:3]:
                    if isinstance(s, dict):
                        skill_names.append(s.get("name", "?"))
                    else:
                        skill_names.append(str(s))
                skills_text = ", ".join(skill_names)
                if len(skills) > 3:
                    skills_text += f" (+{len(skills) - 3} more)"
                self.console.print(f"    Skills: {skills_text}", style=STYLE_MUTED)
            
            self.console.print()
    
    async def _cmd_tools(self) -> None:
        """List available tools for the current agent."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-snapshot"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error fetching tools: {e}[/red]")
            return
        
        tools = data.get("tools", [])
        
        if not tools:
            self.console.print("No tools available", style=STYLE_MUTED)
            return
        
        self.console.print()
        self.console.print(f"● Available Tools ({len(tools)}):", style=STYLE_PRIMARY)
        self.console.print()
        
        for tool in tools:
            tool_name = tool.get("name", "Unknown")
            tool_desc = tool.get("description", "")
            # Truncate description if too long
            if len(tool_desc) > 60:
                tool_desc = tool_desc[:57] + "..."
            self.console.print(f"  • {tool_name}", style=STYLE_ACCENT)
            if tool_desc:
                self.console.print(f"    {tool_desc}", style=STYLE_MUTED)
        
        self.console.print()
    
    async def _cmd_mcp_servers(self) -> None:
        """List MCP servers and their status."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/mcp/servers"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                servers = response.json()
        except Exception as e:
            self.console.print(f"[red]Error fetching MCP servers: {e}[/red]")
            return
        
        if not servers:
            self.console.print("No MCP servers running", style=STYLE_MUTED)
            return
        
        self.console.print()
        self.console.print(f"● MCP Servers ({len(servers)}):", style=STYLE_PRIMARY)
        self.console.print()
        
        for server in servers:
            server_id = server.get("id", "Unknown")
            server_name = server.get("name", server_id)
            is_available = server.get("isAvailable", False)
            tools = server.get("tools", [])
            
            status = "[green]●[/green]" if is_available else "[red]●[/red]"
            self.console.print(f"  {status} {server_name}", style=STYLE_ACCENT)
            
            if tools:
                tool_names = [t.get("name", "?") for t in tools[:5]]
                tools_str = ", ".join(tool_names)
                if len(tools) > 5:
                    tools_str += f" (+{len(tools) - 5} more)"
                self.console.print(f"    Tools: {tools_str}", style=STYLE_MUTED)
        
        self.console.print()
    
    async def _cmd_skills(self) -> None:
        """List available skills (requires codemode enabled)."""
        # First check if codemode is enabled
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/codemode-status"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                status_data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error checking codemode status: {e}[/red]")
            return
        
        codemode_enabled = status_data.get("enabled", False)
        
        if not codemode_enabled:
            self.console.print()
            self.console.print("● Codemode is disabled", style=STYLE_WARNING)
            self.console.print("  Skills are only available when codemode is enabled.", style=STYLE_MUTED)
            self.console.print("  Use /codemode-toggle to enable it.", style=STYLE_MUTED)
            self.console.print()
            return
        
        # Get skills from codemode status (it includes available_skills)
        skills = status_data.get("available_skills", [])
        active_skills = {s.get("name") for s in status_data.get("skills", [])}
        
        if not skills:
            self.console.print("No skills available", style=STYLE_MUTED)
            return
        
        self.console.print()
        self.console.print(f"● Available Skills ({len(skills)}):", style=STYLE_PRIMARY)
        self.console.print()
        
        for skill in skills:
            skill_name = skill.get("name", "Unknown")
            skill_desc = skill.get("description", "")
            is_active = skill_name in active_skills
            # Truncate description if too long
            if len(skill_desc) > 60:
                skill_desc = skill_desc[:57] + "..."
            # Show active status
            status_icon = "[green]●[/green]" if is_active else "○"
            self.console.print(f"  {status_icon} {skill_name}", style=STYLE_ACCENT if is_active else STYLE_MUTED)
            if skill_desc:
                self.console.print(f"    {skill_desc}", style=STYLE_MUTED)
        
        self.console.print()
    
    async def _cmd_codemode_toggle(self) -> None:
        """Toggle codemode on/off."""
        # First get current status
        try:
            async with httpx.AsyncClient() as client:
                status_url = f"{self.server_url}/api/v1/configure/codemode-status"
                status_response = await client.get(status_url, timeout=10.0)
                status_response.raise_for_status()
                current_status = status_response.json()
        except Exception as e:
            self.console.print(f"[red]Error checking codemode status: {e}[/red]")
            return
        
        current_enabled = current_status.get("enabled", False)
        new_enabled = not current_enabled
        
        # Toggle to opposite state
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/codemode/toggle"
                response = await client.post(
                    url, 
                    json={"enabled": new_enabled},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error toggling codemode: {e}[/red]")
            return
        
        enabled = data.get("enabled", False)
        
        self.console.print()
        if enabled:
            self.console.print("● Codemode enabled", style=STYLE_ACCENT)
            self.console.print("  Enhanced code capabilities are now active.", style=STYLE_MUTED)
            self.console.print("  Use /skills to see available skills.", style=STYLE_MUTED)
        else:
            self.console.print("● Codemode disabled", style=STYLE_WARNING)
            self.console.print("  Standard mode is now active.", style=STYLE_MUTED)
        self.console.print()

    async def _cmd_context_export(self) -> None:
        """Export the current context to a CSV file."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-export"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.console.print(f"[red]Error fetching context: {e}[/red]")
            return

        if data.get("error"):
            self.console.print(f"[red]{data.get('error')}[/red]")
            return

        filename = data.get("filename", "codeai_context.csv")
        csv_content = data.get("csv", "")

        if not csv_content:
            self.console.print("[red]No CSV content returned.[/red]")
            return

        try:
            with open(filename, "w", newline="") as csvfile:
                csvfile.write(csv_content)

            tools_count = data.get("toolsCount", 0)
            messages_count = data.get("messagesCount", 0)

            self.console.print()
            self.console.print(f"● Context exported to {filename}", style=STYLE_ACCENT)
            if tools_count or messages_count:
                self.console.print(
                    f"  Contains {tools_count} tools and {messages_count} messages",
                    style=STYLE_MUTED,
                )
            self.console.print()
        except IOError as e:
            self.console.print(f"[red]Error writing file: {e}[/red]")

    async def handle_command(self, user_input: str) -> bool:
        """Handle a slash command.
        
        Returns True if a command was handled, False otherwise.
        """
        if not user_input.startswith("/"):
            return False
        
        parts = user_input[1:].split(maxsplit=1)
        cmd_name = parts[0].lower() if parts else ""
        # args = parts[1] if len(parts) > 1 else ""
        
        if cmd_name in self.commands:
            cmd = self.commands[cmd_name]
            if cmd.handler:
                await cmd.handler()
            return True
        else:
            # Unknown command - show error with hint
            self.console.print(f"Unknown command: /{cmd_name}", style=STYLE_ERROR)
            self.console.print("Type /help to see available commands, or start typing / to see suggestions.", style=STYLE_MUTED)
            return True
    
    async def send_message(self, message: str) -> None:
        """Send a message to the agent and stream the response."""
        from agent_runtimes.transports.clients import AGUIClient
        from ag_ui.core import EventType
        
        self.stats.messages += 1
        self.tool_calls = []  # Reset tool calls for this response
        current_tool_call: Optional[ToolCallInfo] = None
        
        try:
            # Create or reuse the AG-UI client for conversation history
            if self._agui_client is None:
                self._agui_client = AGUIClient(self.agent_url)
                await self._agui_client.connect()
            
            client = self._agui_client
            
            # Show thinking indicator
            with self.console.status("[bold green]Thinking...", spinner="dots"):
                # Small delay to let status appear
                await asyncio.sleep(0.1)
            
            self.console.print()
            # Use a colored bullet (blink doesn't work in most terminals)
            self.console.print("● ", style=STYLE_PRIMARY, end="")
            
            response_text = ""
            input_tokens = 0
            output_tokens = 0
            
            async for event in client.run(message):
                if event.type == EventType.TEXT_MESSAGE_CONTENT:
                    content = event.delta or ""
                    response_text += content
                    self.console.print(content, end="", markup=False)
                
                elif event.type == EventType.TOOL_CALL_START:
                    # Start of a new tool call
                    # Use event properties which handle both camelCase and snake_case
                    tool_call_id = event.tool_call_id or ""
                    tool_name = event.tool_name or "tool"
                    current_tool_call = ToolCallInfo(
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        status="in_progress",
                    )
                    self.tool_calls.append(current_tool_call)
                    tool_num = len(self.tool_calls)
                    self.stats.tool_calls += 1
                    # Show tool call indicator inline with number
                    self.console.print()
                    self.console.print(f"  ⚙ [{tool_num}] {tool_name}", style=STYLE_SECONDARY, end="")
                
                elif event.type == EventType.TOOL_CALL_ARGS:
                    # Accumulate tool arguments
                    if current_tool_call:
                        delta = event.tool_args or ""
                        current_tool_call.args_json += delta
                
                elif event.type == EventType.TOOL_CALL_END:
                    # Tool call arguments complete, now executing
                    if current_tool_call:
                        args_summary = current_tool_call.format_args(max_value_len=50)
                        if args_summary:
                            self.console.print(f"({args_summary})", style=STYLE_MUTED, end="")
                        self.console.print(" ...", style=STYLE_MUTED)
                
                elif event.type == EventType.TOOL_CALL_RESULT:
                    # Tool execution result
                    tool_call_id = event.tool_call_id or ""
                    result = event.tool_result or ""
                    # Find the matching tool call
                    for tc in self.tool_calls:
                        if tc.tool_call_id == tool_call_id:
                            tc.result = str(result) if result else ""
                            tc.status = "complete"
                            # Show completion
                            result_preview = tc.result[:80] + "..." if len(tc.result) > 80 else tc.result
                            result_preview = result_preview.replace("\n", " ")
                            self.console.print(f"    ✓ {result_preview}", style=STYLE_ACCENT)
                            break
                    current_tool_call = None
                
                elif event.type == EventType.RUN_FINISHED:
                    break
                
                elif event.type == EventType.RUN_ERROR:
                    if current_tool_call:
                        current_tool_call.status = "error"
                    self.console.print(f"\n[red]Error: {event.error}[/red]")
                    break
            
            self.console.print()
            
            # Show tool calls summary if any occurred
            if self.tool_calls:
                self._show_tool_calls_summary()
            
            # Fetch updated usage stats
            try:
                async with httpx.AsyncClient() as http_client:
                    url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-snapshot"
                    resp = await http_client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        input_tokens = data.get("sumResponseInputTokens", 0)
                        output_tokens = data.get("sumResponseOutputTokens", 0)
                        self.model_name = data.get("modelName", self.model_name) or self.model_name
                        self.context_window = data.get("contextWindow", self.context_window)
            except Exception:
                pass
            
            # Update stats
            self.stats.total_input_tokens = input_tokens
            self.stats.total_output_tokens = output_tokens
            
            # Show token usage line
            usage_line = Text()
            usage_line.append("─" * 80, style=STYLE_MUTED)
            self.console.print(usage_line)
            
            total = input_tokens + output_tokens
            self.console.print(
                f"  {self._format_tokens(total)} tokens used · "
                f"{self._format_tokens(input_tokens)} in / {self._format_tokens(output_tokens)} out",
                style=STYLE_MUTED,
            )
            self.console.print()
                
        except ConnectionRefusedError:
            self.console.print("[red]Error: Could not connect to agent server[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
    
    def _show_tool_calls_summary(self) -> None:
        """Show a brief summary line of tool calls made."""
        if not self.tool_calls:
            return
        
        completed = sum(1 for tc in self.tool_calls if tc.status == "complete")
        total = len(self.tool_calls)
        tool_names = [tc.tool_name for tc in self.tool_calls[:3]]
        tools_str = ", ".join(tool_names)
        if len(self.tool_calls) > 3:
            tools_str += f" (+{len(self.tool_calls) - 3} more)"
        
        self.console.print(
            f"  ⚙ {completed}/{total} tools executed: {tools_str}  ",
            style=STYLE_MUTED,
            end=""
        )
        self.console.print("\\[/tools-last for details]", style=Style(color="rgb(89,89,92)", italic=True))
    
    async def _cmd_tools_last(self) -> None:
        """Show detailed information about tool calls from the last response."""
        if not self.tool_calls:
            self.console.print()
            self.console.print("● No tool calls in the last response", style=STYLE_MUTED)
            self.console.print()
            return
        
        self.console.print()
        self.console.print(f"● Tool Calls from Last Response ({len(self.tool_calls)}):", style=STYLE_PRIMARY)
        self.console.print()
        
        for i, tc in enumerate(self.tool_calls, 1):
            # Status indicator
            if tc.status == "complete":
                status_icon = "[green]✓[/green]"
                status_style = STYLE_ACCENT
            elif tc.status == "error":
                status_icon = "[red]✗[/red]"
                status_style = STYLE_ERROR
            else:
                status_icon = "[yellow]●[/yellow]"
                status_style = STYLE_WARNING
            
            # Tool header
            self.console.print(f"  {status_icon} {i}. {tc.tool_name}", style=STYLE_PRIMARY)
            
            # Arguments - show complete details
            if tc.args_json:
                try:
                    args = json.loads(tc.args_json)
                    if isinstance(args, dict):
                        for key, value in args.items():
                            val_str = str(value)
                            # Show full value, preserving newlines with indentation
                            if "\n" in val_str:
                                self.console.print(f"     {key}:", style=STYLE_MUTED)
                                for line in val_str.split("\n"):
                                    self.console.print(f"       {line}", style=STYLE_MUTED)
                            else:
                                self.console.print(f"     {key}: {val_str}", style=STYLE_MUTED)
                    else:
                        self.console.print(f"     args: {tc.args_json}", style=STYLE_MUTED)
                except json.JSONDecodeError:
                    self.console.print(f"     args: {tc.args_json}", style=STYLE_MUTED)
            
            # Result - show complete details
            if tc.result:
                self.console.print("     result:", style=STYLE_MUTED)
                for line in tc.result.split("\n"):
                    self.console.print(f"       │ {line}", style=STYLE_MUTED)
            
            self.console.print()
        
        self.console.print()

    async def _cmd_rain(self) -> None:
        """Display Matrix rain animation (5 seconds)."""
        await rain_animation(self.console)

    async def _cmd_about(self) -> None:
        """Display About Datalayer animation."""
        await about_animation(self.console)

    async def _cmd_gif(self) -> None:
        """Display black hole spinning animation (5 seconds)."""
        await gif_animation(self.console)

    async def run(self) -> None:
        """Run the main TUX loop."""
        self.running = True
        
        # Fetch initial model info
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.server_url}/api/v1/configure/agents/{self.agent_id}/context-snapshot"
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    # Try to get model name from various sources
                    self.model_name = data.get("modelName") or "claude-sonnet-4"
                    self.context_window = data.get("contextWindow", 128000)
        except Exception:
            pass
        
        self.show_welcome()
        
        while self.running:
            try:
                user_input = await self.show_prompt()
                
                if not user_input:
                    continue
                
                # Check for slash commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                else:
                    await self.send_message(user_input)
                    
            except KeyboardInterrupt:
                self.console.print()
                await self._cmd_exit()
            except EOFError:
                await self._cmd_exit()


async def run_tux(
    agent_url: str,
    server_url: str = "http://127.0.0.1:8000",
    agent_id: str = "codeai",
    eggs: bool = False,
    jupyter_url: Optional[str] = None,
) -> None:
    """Run the Code AI TUX.
    
    Args:
        agent_url: URL of the AG-UI agent endpoint
        server_url: Base URL of the agent-runtimes server
        agent_id: Agent ID for API calls
        eggs: Enable Easter egg commands
        jupyter_url: Jupyter server URL (only set when sandbox is jupyter)
    """
    tux = CodeAITux(agent_url, server_url, agent_id, eggs=eggs, jupyter_url=jupyter_url)
    await tux.run()
