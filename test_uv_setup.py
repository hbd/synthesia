#!/usr/bin/env python3
"""Test that the reorganized project structure works correctly with uv"""

try:
    # Test imports from src
    from src.analyzers import EnhancedAudioAnalyzer, AudioFeatures
    from src.generators import KeyframeManager, StableDiffusionGenerator
    from src.synthesia import AudioVisualSDSystem
    
    print("✅ All imports successful!")
    print("\nProject structure is working correctly with uv!")
    print("\nYou can now run:")
    print("  uv run synthesia")
    print("  uv run synthesia-file audio.mp3")
    print("  uv run python -m src.synthesia.audio_file_to_video song.mp3")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure to run: uv sync")