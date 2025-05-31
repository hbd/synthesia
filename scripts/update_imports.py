#!/usr/bin/env python3
"""
Update imports in all moved files for the new project structure
"""

import os
import re

# Define import mappings
IMPORT_MAPPINGS = {
    # In generators files
    'src/generators/frame_interpolator.py': [
        ('from enhanced_audio_analyzer import', 'from ..analyzers.enhanced_audio_analyzer import'),
        ('from keyframe_manager import', 'from .keyframe_manager import'),
    ],
    'src/generators/stable_diffusion_generator.py': [
        ('from enhanced_audio_analyzer import', 'from ..analyzers.enhanced_audio_analyzer import'),
    ],
    
    # In synthesia main files
    'src/synthesia/audio_visual_sd_system.py': [
        ('from enhanced_audio_analyzer import', 'from ..analyzers.enhanced_audio_analyzer import'),
        ('from keyframe_manager import', 'from ..generators.keyframe_manager import'),
        ('from frame_interpolator import', 'from ..generators.frame_interpolator import'),
        ('from stable_diffusion_generator import', 'from ..generators.stable_diffusion_generator import'),
    ],
    'src/synthesia/keyframe_interpolation_system.py': [
        ('from enhanced_audio_analyzer import', 'from ..analyzers.enhanced_audio_analyzer import'),
        ('from keyframe_manager import', 'from ..generators.keyframe_manager import'),
        ('from frame_interpolator import', 'from ..generators.frame_interpolator import'),
    ],
    'src/synthesia/audio_file_to_video.py': [
        ('from file_audio_analyzer import', 'from ..analyzers.file_audio_analyzer import'),
        ('from keyframe_manager import', 'from ..generators.keyframe_manager import'),
        ('from frame_interpolator import', 'from ..generators.frame_interpolator import'),
        ('from stable_diffusion_generator import', 'from ..generators.stable_diffusion_generator import'),
    ],
    
    # In example files
    'examples/audio_visual_prototype.py': [
        # Examples can use absolute imports
        ('import numpy', 'import numpy'),  # No change needed for external imports
    ],
    'examples/audio_visual_sd.py': [
        ('from enhanced_audio_analyzer import', 'from src.analyzers.enhanced_audio_analyzer import'),
    ],
    'examples/test_simple_display.py': [
        ('from enhanced_audio_analyzer import', 'from src.analyzers.enhanced_audio_analyzer import'),
    ],
}

def update_file_imports(filepath, mappings):
    """Update imports in a single file"""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    for old_import, new_import in mappings:
        content = content.replace(old_import, new_import)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated imports in {filepath}")
    else:
        print(f"No changes needed in {filepath}")

def main():
    """Update all imports"""
    print("Updating imports for new project structure...")
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Update imports in each file
    for filepath, mappings in IMPORT_MAPPINGS.items():
        update_file_imports(filepath, mappings)
    
    print("\nImport updates complete!")
    print("\nTo use the project with uv:")
    print("  uv sync")
    print("  uv run synthesia")
    print("  uv run synthesia-file audio.mp3")

if __name__ == "__main__":
    main()