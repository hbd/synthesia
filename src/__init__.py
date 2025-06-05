"""Synthesia - Audio-Reactive Visual Generation System"""

__version__ = "1.0.0"

# Import main components for easy access
from .analyzers import EnhancedAudioAnalyzer, AudioFeatures, FileAudioAnalyzer
from .generators import (
    KeyframeManager, Keyframe, FrameInterpolator,
    StableDiffusionGenerator, create_sd_generator
)
from .synthesia import (
    AudioVisualSDSystem,
    AudioVisualSystem,
    AudioFileToVideoSystem
)

__all__ = [
    # Analyzers
    'EnhancedAudioAnalyzer', 'AudioFeatures', 'FileAudioAnalyzer',
    # Generators
    'KeyframeManager', 'Keyframe', 'FrameInterpolator',
    'StableDiffusionGenerator', 'create_sd_generator',
    # Main Systems
    'AudioVisualSDSystem', 'AudioVisualSystem', 'AudioFileToVideoSystem'
]