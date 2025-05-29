# Audio to AI Visuals: Architecture & Approaches

## Overview

This document outlines various approaches for creating real-time audio-reactive visuals using AI image generation models like Stable Diffusion, FLUX, and Mochi.

## Core Challenge: Timing Constraints

- **Target**: 30+ fps (33ms per frame) for smooth visuals
- **Stable Diffusion**: ~1-5 seconds per image
- **Gap**: 30-150x too slow for real-time generation

## Approach 1: Keyframe + Interpolation (Most Practical)

### Architecture
```
Audio Stream → Audio Analysis → Keyframe Generation (every 1-2s) → Frame Interpolation
     ↓              ↓                    ↓                              ↓
  44.1kHz      FFT/Features         SD/FLUX Image              Morph/Blend/Warp
```

### Implementation Details
- Generate "anchor" images every 1-2 seconds
- Use audio features to control morphing between keyframes
- Audio-reactive parameters:
  - Bass intensity → Zoom/scale effects
  - High frequencies → Rotation speed
  - Beat detection → Transition triggers
  - Overall energy → Interpolation speed

### Advantages
- Achievable on 1-2 GPUs
- Smooth visual output
- Good balance of quality and performance

## Approach 2: Audio to Prompt Mapping

### Simple Rule-Based Mapping
```python
Audio Features → Text Descriptors → Prompts
- High energy → "explosive, dynamic, chaotic"
- Low energy → "calm, flowing, serene"
- Bass dominant → "deep red, powerful, heavy"
- Mid dominant → "warm, organic, vibrant"
- High dominant → "sparkly, crystalline, sharp"
```

### Advanced ML-Based Mapping
- Train audio encoder to map to CLIP embedding space
- Use models like CLAP (Contrastive Language-Audio Pretraining)
- Music genre/mood detection → style modifiers

### Prompt Scheduling
- Queue prompts based on audio analysis
- Smooth transitions between prompt styles
- Beat-synchronized prompt changes

## Approach 3: Latent Space Manipulation

### Concept
Instead of generating new images, manipulate existing ones in latent space:
```
Base Image → VAE Encode → Latent Manipulation → VAE Decode
                              ↓
                    Audio modulates latent vectors
```

### Techniques
- Latent blending between multiple images
- Directional manipulation (found via audio features)
- Latent space interpolation along audio-defined paths

## Approach 4: ComfyUI Integration

### Workflow Architecture
```
[Audio File/Stream Input]
         ↓
[Audio Analysis Node]
    ├─→ [Beat Detection] → [Transition Trigger]
    ├─→ [FFT Analysis] → [Prompt Modifiers]
    └─→ [Energy Levels] → [Interpolation Speed]
         ↓
[Dynamic Prompt Builder]
         ↓
[Checkpoint Loader] → [KSampler] → [Image Buffer]
                                          ↓
                            [Frame Interpolation Node]
                                          ↓
                               [Audio-Reactive Effects]
                                          ↓
                                   [Video Output]
```

### Custom Nodes Required
1. **Audio Analysis Suite**
   - Real-time FFT
   - Beat/onset detection
   - Frequency band extraction
   - Tempo estimation

2. **Prompt Generation**
   - Audio feature → text mapping
   - Prompt interpolation
   - Style mixing based on audio

3. **Frame Processing**
   - Smart frame caching
   - Audio-driven interpolation
   - Effect intensity mapping

## Approach 5: Hybrid Strategies

### Pre-generated Image Library
- Create diverse image set offline
- Audio selects and morphs between them
- Lower latency, less dynamic

### ControlNet Audio Integration
- Audio drives ControlNet inputs:
  - OpenPose for "dancing" figures
  - Depth maps for 3D effects
  - Canny edges for structure morphing

### AnimateDiff with Audio Sync
- Generate video clips with AnimateDiff
- Audio controls playback speed/direction
- Blend between different clips

### Video Model Integration (Mochi)
- Use Mochi for 5-10 second generations
- Audio analysis determines prompts
- Shorter clips for faster response

## Performance Optimization Strategies

### Model Selection
- **SDXL-Turbo**: 1-4 steps, ~100ms/image
- **LCM (Latent Consistency Models)**: Fast sampling
- **TensorRT optimization**: 2-3x speedup
- **Resolution scaling**: Generate at 512x512, upscale

### Pipeline Optimization
- Async generation (queue system)
- Multi-GPU setup (one generates, one interpolates)
- Aggressive caching
- Frame prediction/pre-generation

### Quality vs Speed Tradeoffs
| Approach | Quality | Latency | GPU Requirements |
|----------|---------|---------|------------------|
| Every frame generation | Highest | 1-5s | 8+ GPUs |
| Keyframe interpolation | High | 100ms | 1-2 GPUs |
| Latent manipulation | Medium | 50ms | 1 GPU |
| Pre-generated library | Variable | <16ms | 1 GPU |

## Recommended Architecture for Synthesia

### Phase 1: Proof of Concept
1. Use procedural visuals for immediate feedback
2. Generate SD images every 2 seconds
3. Simple crossfade between images
4. Audio controls fade timing

### Phase 2: Enhanced Interpolation
1. Implement optical flow between frames
2. Add audio-reactive warping effects
3. Multi-layer compositing
4. Beat-synchronized transitions

### Phase 3: Advanced Integration
1. ComfyUI custom nodes
2. Multiple model support (SD, FLUX, Mochi)
3. Real-time prompt evolution
4. Latent space exploration

## Technical Considerations

### Audio Analysis Requirements
- Latency: <5ms for responsiveness
- Frequency resolution: 20Hz-20kHz
- Temporal resolution: ~50ms windows
- Features: RMS, spectral centroid, onset detection

### Visual Generation Pipeline
- Frame buffer: 2-3 seconds ahead
- Interpolation: 60fps capability
- Effect processing: GPU shaders
- Output: NDI/Spout/Virtual camera

### Synchronization
- Audio-visual sync tolerance: <40ms
- Beat alignment precision: <20ms
- Transition smoothness: No frame drops

## Future Explorations

### Audio-Native Models
- Train models on audio-image pairs
- Direct audio embedding → image generation
- Skip text prompt intermediate step

### Real-time Model Adaptations
- Distilled models for speed
- Progressive rendering
- Adaptive quality based on motion

### Interactive Elements
- MIDI input for live control
- OSC integration for VJing
- Feedback loops (generated images influence audio)