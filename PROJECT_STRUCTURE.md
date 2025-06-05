# 📁 Synthesia Project Structure

The project has been reorganized for better maintainability and clarity:

```
synthesia/
├── src/                      # Main source code
│   ├── analyzers/           # Audio analysis modules
│   │   ├── __init__.py
│   │   ├── enhanced_audio_analyzer.py  # Real-time audio analysis
│   │   └── file_audio_analyzer.py      # File-based audio analysis
│   │
│   ├── generators/          # Visual generation modules
│   │   ├── __init__.py
│   │   ├── frame_interpolator.py       # Real-time frame interpolation
│   │   ├── keyframe_manager.py         # Keyframe generation & caching
│   │   └── stable_diffusion_generator.py # AI image generation
│   │
│   ├── synthesia/           # Main application modules
│   │   ├── __init__.py
│   │   ├── audio_visual_sd_system.py   # Live audio reactive system
│   │   ├── audio_file_to_video.py      # File to video conversion
│   │   └── keyframe_interpolation_system.py # Keyframe system
│   │
│   └── utils/               # Utility modules
│       ├── __init__.py
│       └── comfyui_integration.py      # ComfyUI custom nodes
│
├── examples/                # Example implementations
│   ├── audio_visual_prototype.py       # Basic prototype
│   ├── audio_visual_sd.py              # SD integration example
│   └── test_simple_display.py          # Simple test script
│
├── docs/                    # Documentation
│   ├── guides/             # Setup and usage guides
│   │   ├── GPU_SETUP_GUIDE.md
│   │   ├── README_keyframe_interpolation.md
│   │   ├── RUN_GUIDE.md
│   │   ├── SETUP_NEW_MACHINE.md
│   │   ├── SETUP_RTX_A6000.md
│   │   └── view_output.md
│   └── audio-to-ai-visuals-architecture.md
│
├── output/                  # Generated outputs
│   ├── audio_visual_demo.zip
│   └── output_frames/      # Generated frames
│
├── scripts/                 # Utility scripts
│   ├── setup.sh            # Legacy setup script
│   └── update_imports.py   # Import update utility
│
├── tests/                   # Test suite (to be added)
│
├── pyproject.toml          # Modern Python project config
├── uv.lock                 # Locked dependencies
├── requirements.txt        # Legacy requirements
├── README.md              # Main documentation
├── CLAUDE.md              # AI assistant context
└── .gitignore             # Git ignore rules
```

## 🚀 Usage with UV

The project is configured to work with `uv` for fast dependency management:

```bash
# Install dependencies
uv sync

# Install with GPU optimizations
uv sync --extra gpu-optimized

# Run main applications
uv run synthesia                    # Live audio-reactive system
uv run synthesia-file audio.mp3     # Convert audio file to video
uv run synthesia-basic              # Basic prototype

# Or run directly
uv run python -m src.synthesia.audio_file_to_video song.mp3
```

## 📦 Package Structure

The `src/` directory is configured as the main package, allowing:
- Clean imports between modules
- Proper package distribution
- Clear separation of concerns

### Import Examples

```python
# From within src/generators/
from ..analyzers.enhanced_audio_analyzer import AudioFeatures

# From within src/synthesia/
from ..generators.keyframe_manager import KeyframeManager
from ..analyzers.file_audio_analyzer import FileAudioAnalyzer

# From examples or external scripts
from src.analyzers import EnhancedAudioAnalyzer
from src.generators import StableDiffusionGenerator
```

## 🔧 Development

When developing new features:
1. Audio analysis code → `src/analyzers/`
2. Visual generation → `src/generators/`
3. Main applications → `src/synthesia/`
4. Utilities/integrations → `src/utils/`
5. Documentation → `docs/`
6. Test files → `tests/`

This structure promotes:
- ✅ Clear module boundaries
- ✅ Easy testing and mocking
- ✅ Reusable components
- ✅ Clean dependency management
- ✅ Professional organization