# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synthesia is a real-time audio-to-visual system that generates reactive visuals from sound input. It combines audio analysis with visual generation, including integration with AI models like Stable Diffusion.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run basic visualizer
python audio_visual_prototype.py

# Run advanced system (with SD support)
python audio_visual_sd.py
```

## Architecture

### Core Components

1. **AudioAnalyzer** - Real-time audio processing
   - FFT frequency analysis (bass/mid/high bands)
   - RMS amplitude detection
   - Beat/onset detection (planned)

2. **VisualEngine** - Visual generation system
   - Procedural generation for real-time response
   - Keyframe generation (SD integration point)
   - Frame interpolation based on audio features

3. **PromptGenerator** - Audio-to-text mapping
   - Maps audio features to descriptive prompts
   - Energy levels → intensity modifiers
   - Frequency bands → color mappings

### Key Design Patterns

- **Streaming Architecture**: Audio queue → Feature extraction → Visual generation
- **Async Keyframe Generation**: Background thread generates expensive frames
- **Interpolation Strategy**: Smooth transitions between keyframes at 30+ fps
- **Modular Design**: Easy to swap visual generators (procedural/SD/ComfyUI)

## Integration Points

- **Stable Diffusion**: Via diffusers library in KeyframeGenerator
- **ComfyUI**: Can export workflow or use as custom node
- **Audio Input**: PyAudio for real-time capture
- **Visual Output**: OpenCV for display/streaming

## Performance Considerations

- Target 30+ fps for smooth visuals
- Keyframe generation every 1-2 seconds
- Audio analysis must be <5ms per frame
- Frame interpolation handles real-time requirements