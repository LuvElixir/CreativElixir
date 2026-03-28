# CreativElixir

AI-powered development assistant for Godot 4.6 — context-aware chat, agent actions, and art prompt generation.

## Features

### Chat & Context Awareness
- Dock panel in editor sidebar + floating window mode
- Two context modes: **Smart** (current scene/script) and **Full Scan** (entire project)
- Auto-captures editor viewport screenshots for Vision API
- Chat history persisted across sessions
- Supports Chinese (中文) and English

### AI Agent Actions
- Create / delete / modify nodes in the scene tree
- Write and overwrite GDScript files
- Save scenes, generate resources (ShaderMaterial, SpriteFrames, etc.)
- All actions are **undoable** (Ctrl+Z) via EditorUndoRedoManager
- One-click "Apply Code" from chat responses

### Art Prompt Generator
- Analyzes project art style (color palette, pixel art detection)
- Generates optimized prompts for **Midjourney**, **即梦 Seedream**, **Nano Banana**
- Batch variant generation (colors × poses × expressions)
- Reference image analysis
- Procedural placeholder resources (GradientTexture2D, SpriteFrames, ShaderMaterial)
- Godot import workflow guides with code snippets

### LLM Support
- **OpenAI-compatible API** — works with OpenAI, DeepSeek, Together, OpenRouter, etc.
- **Anthropic API** — Claude models with custom Base URL
- Custom Base URL for any provider (Chinese/international)
- Encrypted API key storage (AES-256, per-project)
- Test Connection button in settings

## Installation

1. Copy the `addons/creativelixir/` folder into your Godot project's `addons/` directory
2. Open your project in Godot 4.6
3. Go to **Project → Project Settings → Plugins**
4. Enable **CreativElixir**
5. Click **Settings** in the CreativElixir dock to configure your API keys

## Configuration

### API Keys
API keys are stored encrypted in `user://creativelixir_keys.cfg` — they are **never** saved in your project directory and won't be committed to version control.

### Settings Location
| Setting | Location | Shared with team? |
|---------|----------|-------------------|
| Provider, model, base URL | `project.godot` | Yes |
| API keys | `user://` (encrypted) | No |
| Chat history | `addons/creativelixir/.chat_history/` | Optional |
| Project style profile | `addons/creativelixir/.project_style.json` | Yes |

## Usage

### Chat
Type a message and press **Ctrl+Enter** or click **Send**. The AI understands your current scene, open script, and selected nodes.

### Agent Actions
Ask the AI to make changes: *"Add a Sprite2D at position (100, 200)"* or *"Write a player movement script"*. Actions execute automatically and can be undone.

### Art Prompts
Click the **Art** button to open the Art Prompt Generator. Analyze your project's style, describe what you need, and get optimized prompts for your preferred AI art tool.

## Requirements
- Godot 4.6+
- An API key from OpenAI, Anthropic, or any compatible provider

## License
MIT
