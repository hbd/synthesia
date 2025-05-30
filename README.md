# 🎵 Synthesia - AI Audio-to-Video Generation

Real-time audio analysis and visual generation system that creates reactive visuals from sound input using **Stable Diffusion** and advanced audio processing.

![Demo](output_frames/frame_000000.png)

## ✨ Features

- 🎵 **Audio File Processing**: MP3/WAV input with beat detection
- 🎨 **AI Visual Generation**: SDXL-Turbo for 50-100ms image generation  
- 🎬 **Video Output**: Direct MP4 export with customizable resolution
- ⚡ **GPU Optimized**: RTX A6000 dual-GPU support, <4s model loading
- 🎯 **Real-time Reactive**: Visuals respond to beats, energy, and frequency
- 📺 **YouTube Integration**: Built-in audio download from videos

## 🚀 Quick Start

```bash
# 1. Setup (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/your-org/synthesia.git
cd synthesia
uv sync --extra gpu-optimized

# 2. Generate video from YouTube
uv run yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
uv run python audio_file_to_video.py *.mp3 --save-video

# 3. Watch result
vlc *.mp4
```

## 📋 Requirements

- **GPU**: NVIDIA RTX 3090/4090/A6000 (12GB+ VRAM)
- **OS**: Ubuntu 22.04+ or similar Linux
- **Python**: 3.10+ (auto-managed)

## 🎯 Usage Examples

### Basic Generation
```bash
uv run python audio_file_to_video.py song.mp3 --save-video
```

### High Quality  
```bash
uv run python audio_file_to_video.py song.mp3 \
    --save-video --fps 30 --width 1024 --height 1024
```

### Fast Preview
```bash
uv run python audio_file_to_video.py song.mp3 \
    --fps 15 --width 512 --height 512 --no-preview
```

## 🏗️ Architecture

- **Enhanced Audio Analyzer**: FFT analysis, beat detection, energy mapping
- **Keyframe Manager**: AI-generated keyframes with intelligent caching  
- **Frame Interpolator**: Smooth 30+ fps transitions between keyframes
- **Stable Diffusion Integration**: SDXL-Turbo for fast visual generation

## 📖 Documentation

- **[Setup Guide](SETUP_NEW_MACHINE.md)**: Complete installation instructions
- **[GPU Optimization](SETUP_RTX_A6000.md)**: RTX A6000 performance tuning
- **[Development Context](CLAUDE.md)**: Technical details and architecture

## 🎬 Sample Output

The system generates AI visuals that react to:
- **Beat Detection**: New keyframes on musical beats
- **Energy Levels**: Colors respond to bass/mid/high frequencies  
- **Tempo**: 123 BPM detection for rhythmic generation
- **Musical Structure**: Automatic style changes on transitions

## ⚡ Performance

**RTX A6000 Benchmarks:**
- Model loading: 3-4 seconds
- 512x512 generation: 50-100ms  
- 1024x1024 generation: 100-200ms
- Sustained throughput: 20-30 fps

## 🔧 Development

```bash
# Install development dependencies
uv sync --extra dev

# Run with different models
uv run python audio_file_to_video.py song.mp3 --sd-model turbo
uv run python audio_file_to_video.py song.mp3 --sd-model lightning

# Procedural mode (no AI)
uv run python audio_file_to_video.py song.mp3 --no-sd
```

---

**Built with:** Python, PyTorch, Diffusers, Librosa, OpenCV, and ❤️

**Optimized for:** NVIDIA RTX A6000, Dual-GPU setups, Production use