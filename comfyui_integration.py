"""
ComfyUI Custom Node for Audio-Reactive Generation
Place in ComfyUI/custom_nodes/synthesia/
"""

class AudioAnalysisNode:
    """Analyzes audio and outputs features for prompt generation"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_file": ("STRING", {"default": ""}),
                "live_input": ("BOOLEAN", {"default": False}),
                "chunk_size": ("INT", {"default": 2048, "min": 512, "max": 8192}),
            }
        }
    
    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT", "FLOAT", "STRING")
    RETURN_NAMES = ("rms", "bass", "mid", "high", "prompt_modifier")
    FUNCTION = "analyze"
    CATEGORY = "audio"
    
    def analyze(self, audio_file, live_input, chunk_size):
        # Implementation would go here
        # Returns: (rms, bass, mid, high, prompt_modifier)
        pass

class AudioToPromptNode:
    """Converts audio features to dynamic prompts"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_prompt": ("STRING", {"multiline": True}),
                "rms": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
                "bass": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
                "mid": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
                "high": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_prompt"
    CATEGORY = "audio"
    
    def generate_prompt(self, base_prompt, rms, bass, mid, high):
        # Map audio to prompt modifiers
        energy_level = "intense" if rms > 0.7 else "flowing" if rms > 0.3 else "calm"
        
        # Dominant frequency determines color
        if bass > mid and bass > high:
            color = "warm red orange"
        elif mid > high:
            color = "vibrant green yellow"
        else:
            color = "cool blue violet"
        
        return (f"{energy_level} {color} {base_prompt}",)

class FrameInterpolationNode:
    """Interpolates between generated frames based on audio"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "interpolation": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "audio_modulation": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "interpolate"
    CATEGORY = "audio/visual"
    
    def interpolate(self, image1, image2, interpolation, audio_modulation):
        # Modulate interpolation with audio
        alpha = max(0, min(1, interpolation + audio_modulation))
        
        # Blend images
        result = image1 * (1 - alpha) + image2 * alpha
        return (result,)

# ComfyUI node registration
NODE_CLASS_MAPPINGS = {
    "AudioAnalysis": AudioAnalysisNode,
    "AudioToPrompt": AudioToPromptNode,
    "FrameInterpolation": FrameInterpolationNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioAnalysis": "Audio Analysis",
    "AudioToPrompt": "Audio to Prompt",
    "FrameInterpolation": "Audio Frame Interpolation",
}