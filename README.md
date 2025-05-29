# Synthesia - Audio to Visual Streaming

Real-time audio analysis and visual generation system that creates reactive visuals from sound input.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# macOS users may need:
brew install portaudio
```

## Quick Start

```bash
# Run basic visualizer
python audio_visual_prototype.py
```

## Architecture

1. **Audio Analysis**: Real-time FFT analysis extracting bass/mid/high frequencies
2. **Visual Generation**: OpenCV-based reactive visuals (will integrate SD/FLUX)
3. **Parameter Mapping**: Maps audio features to visual parameters

## Next Steps

- Add beat detection
- Integrate Stable Diffusion for keyframe generation
- Add ComfyUI workflow support
- Implement frame interpolation