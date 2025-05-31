"""Utility modules for integrations"""

# ComfyUI integration nodes (when placed in ComfyUI custom_nodes directory)
try:
    from .comfyui_integration import (
        AudioAnalysisNode,
        AudioToPromptNode, 
        FrameInterpolationNode,
        NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS
    )
    COMFYUI_AVAILABLE = True
except ImportError:
    COMFYUI_AVAILABLE = False

__all__ = ['COMFYUI_AVAILABLE']

if COMFYUI_AVAILABLE:
    __all__.extend([
        'AudioAnalysisNode',
        'AudioToPromptNode',
        'FrameInterpolationNode',
        'NODE_CLASS_MAPPINGS',
        'NODE_DISPLAY_NAME_MAPPINGS'
    ])