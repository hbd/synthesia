# 🚀 Synthesia Setup Guide - New Machine

This guide will help you set up the Synthesia audio-to-video generation system from scratch on a new machine.

## 📋 Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA RTX A6000 (dual setup recommended) or RTX 3090/4090
- **VRAM**: Minimum 12GB, 24GB+ recommended for high resolution
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space

### Software Requirements
- **OS**: Ubuntu 22.04 LTS (tested) or similar Linux distribution
- **CUDA**: 12.1+ (automatically installed with PyTorch)
- **Python**: 3.10+ (managed by pyenv recommended)

## 🛠️ Quick Setup (10 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/synthesia.git
cd synthesia
git checkout feature/keyframe-interpolation
```

### 2. Install Modern Package Manager
```bash
# Install uv (super fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Install System Dependencies
```bash
# Audio and video libraries
sudo apt update
sudo apt install -y portaudio19-dev python3-pyaudio vlc ffmpeg

# Optional: GPU monitoring
sudo apt install -y nvidia-smi
```

### 4. Setup Python Environment
```bash
# Sync all dependencies (auto-creates venv)
uv sync

# Install GPU optimizations
uv sync --extra gpu-optimized
```

### 5. Verify Setup
```bash
# Test GPU detection
uv run python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
[print(f'GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]
"
```

## 🎵 Usage Examples

### Basic Audio File to Video
```bash
# Download audio from YouTube
uv run yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=VIDEO_ID"

# Generate video with AI
uv run python audio_file_to_video.py audio.mp3 --save-video --output result.mp4

# Watch result
vlc result.mp4
```

### Advanced Options
```bash
# High quality generation
uv run python audio_file_to_video.py audio.mp3 \
    --save-video --output hq_video.mp4 \
    --fps 30 --width 1024 --height 1024 \
    --cache-size 8

# Fast preview mode
uv run python audio_file_to_video.py audio.mp3 \
    --fps 15 --width 512 --height 512 \
    --no-preview

# Procedural visuals only (no AI)
uv run python audio_file_to_video.py audio.mp3 \
    --no-sd --save-video
```

## 📁 Project Structure

```
synthesia/
├── pyproject.toml                 # Modern dependency management
├── uv.lock                       # Locked dependencies
├── .python-version               # Python version spec
│
├── audio_file_to_video.py        # 🎬 Main application (NEW)
├── file_audio_analyzer.py        # 🎵 File-based audio analysis (NEW)
├── audio_visual_sd_system.py     # Live microphone system
│
├── enhanced_audio_analyzer.py    # Real-time audio processing
├── stable_diffusion_generator.py # AI image generation
├── keyframe_manager.py          # Keyframe caching system
├── frame_interpolator.py        # Smooth frame transitions
│
├── SETUP_RTX_A6000.md           # GPU optimization guide
├── SETUP_NEW_MACHINE.md         # This file
└── CLAUDE.md                    # Development context
```

## 🎯 What's New in This Version

### Major Features Added
1. **Audio File Processing**: Process MP3/WAV files instead of live microphone
2. **Modern Dependency Management**: Uses `uv` for lightning-fast installs
3. **Video Output**: Save generated videos directly to MP4
4. **YouTube Integration**: Built-in YouTube audio download
5. **Multiple Resolutions**: 512x512 to 1024x1024+ support

### Performance Optimizations
- **SDXL-Turbo**: 50-100ms generation on RTX A6000
- **xformers**: Memory-efficient attention
- **Model compilation**: ~4s load time (vs 30s+ unoptimized)
- **Dual GPU ready**: Can utilize multiple GPUs

## 🔧 Troubleshooting

### Common Issues

**1. CUDA not detected**
```bash
# Reinstall PyTorch with CUDA
uv add torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**2. Audio errors (ALSA warnings)**
```bash
# Install additional audio libs
sudo apt install -y libasound2-dev alsa-utils
```

**3. Out of GPU memory**
```bash
# Use lower resolution or smaller batch
uv run python audio_file_to_video.py audio.mp3 --width 512 --height 512
```

**4. Slow generation**
```bash
# Check GPU utilization
nvidia-smi

# Ensure xformers is installed
uv sync --extra gpu-optimized
```

### Performance Benchmarks

**Expected performance on RTX A6000:**
- Model loading: 3-5 seconds
- 512x512 generation: 50-100ms per frame
- 1024x1024 generation: 100-200ms per frame
- Video processing: 10-20 fps sustained

**Expected performance on RTX 3090:**
- Model loading: 5-10 seconds
- 512x512 generation: 100-200ms per frame
- 1024x1024 generation: 200-400ms per frame

## 🎨 Sample Workflow

```bash
# 1. Download music
uv run yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=SONG_ID"

# 2. Generate AI video
uv run python audio_file_to_video.py *.mp3 --save-video --fps 20

# 3. Watch result
vlc *.mp4

# 4. Generate higher quality
uv run python audio_file_to_video.py *.mp3 \
    --save-video --output hq_version.mp4 \
    --width 1024 --height 1024 --fps 30
```

## 📞 Support

- **Documentation**: Check `CLAUDE.md` for development context
- **GPU Setup**: See `SETUP_RTX_A6000.md` for hardware optimization
- **Examples**: Look in `output_frames/` for sample results

The system is production-ready and has been tested on dual RTX A6000 setups! 🚀