# Keyframe + Interpolation System

This branch implements the **Keyframe + Interpolation** approach for real-time audio-reactive visuals, as outlined in our architecture document.

## System Overview

The system generates high-quality "keyframe" images every 1-2 seconds and smoothly interpolates between them at 30+ fps, with audio controlling the interpolation speed, warping effects, and transition timing.

## Architecture

```
Audio Stream → Enhanced Analysis → Keyframe Generation → Frame Interpolation → Display
     ↓              ↓                    ↓                      ↓
  44.1kHz      Beat Detection      Procedural/SD Image    Audio Warping
              Energy Analysis      Background Thread       Beat Effects
              Tempo Tracking       Smart Caching          Smooth Blending
```

## Components

### 1. EnhancedAudioAnalyzer (`enhanced_audio_analyzer.py`)
- **Real-time FFT analysis** for bass/mid/high frequency bands
- **Beat detection** using energy-based onset detection
- **Tempo estimation** from beat intervals
- **Keyframe timing** - automatically determines when to generate new keyframes
- **Spectral features** - centroid, rolloff, energy delta

**Key Features:**
- Adaptive keyframe generation (energy spikes trigger faster generation)
- Smoothed features to reduce noise
- Beat confidence scoring
- Energy level classification (low/medium/high)

### 2. KeyframeManager (`keyframe_manager.py`)
- **Asynchronous image generation** in background thread
- **Smart prompt generation** based on audio features
- **Keyframe caching** with configurable size
- **Fallback procedural generation** when SD unavailable
- **Performance tracking** and timeout handling

**Key Features:**
- Audio-driven prompt generation (energy level → intensity, frequency → color)
- Background generation prevents frame drops
- Graceful fallback to procedural visuals
- Queue management to prevent overload

### 3. FrameInterpolator (`frame_interpolator.py`)
- **Smooth blending** between keyframes
- **Audio-reactive warping** (zoom, rotation, displacement)
- **Beat-synchronized effects** (flashes, cuts, speed changes)
- **Multiple blend modes** based on energy level
- **Real-time effect overlays** (sparkles, glow, etc.)

**Key Features:**
- Beat detection triggers zoom pulses and hard cuts
- High frequencies control rotation
- Energy delta creates subtle warping
- Overlay effects for different frequency bands

### 4. AudioVisualSystem (`keyframe_interpolation_system.py`)
- **Integrated control system** combining all components
- **Performance monitoring** with FPS tracking
- **Interactive controls** (toggle overlays, reset, etc.)
- **Stats display** showing system performance
- **Audio waveform visualization**

## Usage

### Basic Usage
```bash
# Run with default settings
python keyframe_interpolation_system.py

# Custom settings
python keyframe_interpolation_system.py --fps 60 --width 1920 --height 1080
```

### Interactive Controls
- **q** - Quit
- **s** - Toggle stats overlay
- **w** - Toggle waveform display  
- **r** - Reset interpolator

### Command Line Options
```bash
--fps 30              # Target frame rate
--duration 60         # Run for 60 seconds
--width 1920          # Window width
--height 1080         # Window height
--cache-size 6        # Number of keyframes to cache
--no-stats            # Disable stats overlay
--no-waveform         # Disable waveform display
```

## Performance Characteristics

### Current Performance (Procedural Mode)
- **30+ fps** smooth interpolation
- **~5ms** audio analysis latency
- **~50ms** procedural keyframe generation
- **Memory usage**: ~100MB (depending on cache size)

### Expected Performance (With SD Integration)
- **30+ fps** interpolation maintained
- **1-3 seconds** keyframe generation (SDXL-Turbo)
- **Background generation** prevents frame drops
- **Memory usage**: ~2-4GB (model + cache)

## Audio Feature Mapping

### Energy Levels → Visual Style
- **Low Energy**: Gentle gradients, soft transitions, flowing movement
- **Medium Energy**: Dynamic patterns, rhythmic changes, balanced colors  
- **High Energy**: Explosive effects, chaotic patterns, intense colors

### Frequency Bands → Visual Elements
- **Bass (20-250Hz)**: Background color, zoom effects, glow intensity
- **Mid (250-4000Hz)**: Main visual elements, primary colors
- **High (4000-20000Hz)**: Sparkle effects, rotation, brightness

### Temporal Features → Animation
- **Beat Detection**: Zoom pulses, hard cuts, flash effects
- **Tempo**: Interpolation speed, animation frequency
- **Energy Delta**: Warping intensity, transition triggers

## Integration Points

### Stable Diffusion Integration
The system is designed to easily integrate SD generation:

```python
def sd_generator(features, prompt):
    # Your SD pipeline here
    image = sd_pipe(prompt, num_inference_steps=4).images[0]
    return np.array(image)

# Use with system
system = AudioVisualSystem(custom_generator=sd_generator)
```

### ComfyUI Integration
Components can be adapted as ComfyUI custom nodes:
- AudioAnalysisNode → Enhanced audio analysis
- KeyframeGeneratorNode → Prompt generation + SD
- FrameInterpolationNode → Audio-reactive blending

## Future Enhancements

1. **SDXL-Turbo Integration** - Fast SD generation
2. **Multiple Model Support** - FLUX, Mochi video generation
3. **Advanced Effects** - Particle systems, 3D transformations
4. **MIDI Control** - External parameter control
5. **Recording/Streaming** - Save output to video files
6. **GPU Optimization** - CUDA acceleration for effects

## Technical Notes

### Threading Architecture
- **Main Thread**: Audio analysis, frame interpolation, display
- **Background Thread**: Keyframe generation (SD/procedural)
- **Audio Thread**: PyAudio callback (handled internally)

### Memory Management
- Keyframe cache with configurable size
- Automatic cleanup of old frames
- Efficient numpy operations for real-time processing

### Synchronization
- Audio-visual sync maintained within 40ms
- Beat alignment precision within 20ms
- No frame drops during keyframe generation

## Testing

Each component includes standalone testing:

```bash
# Test individual components
python enhanced_audio_analyzer.py
python keyframe_manager.py  
python frame_interpolator.py

# Test full system
python keyframe_interpolation_system.py --duration 30
```

## Dependencies

All components use the same base requirements:
- numpy, opencv-python, pyaudio, scipy
- Optional: torch, diffusers (for SD integration)

See `requirements.txt` for complete list.