#!/usr/bin/env python3
"""
Stable Diffusion Integration for Real-time Audio-Reactive Generation
Uses SDXL-Turbo for fast inference suitable for keyframe generation
"""

import torch
import numpy as np
from PIL import Image
import time
import cv2
from typing import Optional, Dict, Any
import warnings

# Suppress some warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler
    from diffusers.utils import logging
    logging.set_verbosity_error()
    DIFFUSERS_AVAILABLE = True
except ImportError:
    print("Warning: diffusers not installed. Run: pip install diffusers")
    DIFFUSERS_AVAILABLE = False

from enhanced_audio_analyzer import AudioFeatures

class StableDiffusionGenerator:
    """Fast Stable Diffusion generator optimized for real-time keyframe generation"""
    
    def __init__(self, 
                 model_id: str = "stabilityai/sdxl-turbo",
                 device: Optional[str] = None,
                 torch_dtype=torch.float16,
                 enable_cpu_offload: bool = False):
        
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("diffusers library not available. Install with: pip install diffusers")
        
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.torch_dtype = torch_dtype
        self.enable_cpu_offload = enable_cpu_offload
        
        print(f"Initializing Stable Diffusion on {self.device}...")
        print(f"Model: {model_id}")
        
        # Initialize pipeline
        self.pipe = None
        self.is_loaded = False
        self.generation_stats = {
            "total_generations": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "last_generation_time": 0.0
        }
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load the Stable Diffusion model"""
        try:
            start_time = time.time()
            
            # Load pipeline
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                variant="fp16" if self.torch_dtype == torch.float16 else None,
                use_safetensors=True
            )
            
            # Move to device
            if self.device != "cpu":
                self.pipe = self.pipe.to(self.device)
            
            # Enable CPU offload if requested (saves VRAM)
            if self.enable_cpu_offload and hasattr(self.pipe, 'enable_model_cpu_offload'):
                self.pipe.enable_model_cpu_offload()
            
            # Optimize for speed
            if hasattr(self.pipe, 'enable_attention_slicing'):
                self.pipe.enable_attention_slicing()
            
            # Compile model for faster inference (PyTorch 2.0+)
            if hasattr(torch, 'compile') and self.device == "cuda":
                try:
                    self.pipe.unet = torch.compile(self.pipe.unet, mode="reduce-overhead", fullgraph=True)
                    print("Model compiled for faster inference")
                except Exception as e:
                    print(f"Could not compile model: {e}")
            
            load_time = time.time() - start_time
            print(f"Model loaded in {load_time:.2f}s")
            
            # Warm-up generation
            print("Warming up model...")
            self._warmup()
            
            self.is_loaded = True
            
        except Exception as e:
            print(f"Failed to load Stable Diffusion model: {e}")
            print("Falling back to procedural generation")
            self.is_loaded = False
    
    def _warmup(self):
        """Perform warmup generation to optimize inference"""
        try:
            warmup_prompt = "abstract art, colorful, simple"
            start_time = time.time()
            
            _ = self.pipe(
                prompt=warmup_prompt,
                num_inference_steps=1,
                height=512,
                width=512,
                guidance_scale=0.0,  # Disable guidance for speed
                output_type="pil"
            ).images[0]
            
            warmup_time = time.time() - start_time
            print(f"Warmup completed in {warmup_time:.2f}s")
            
        except Exception as e:
            print(f"Warmup failed: {e}")
    
    def generate_image(self, 
                      audio_features: AudioFeatures, 
                      prompt: str,
                      size: tuple = (512, 512),
                      num_inference_steps: int = 1,
                      guidance_scale: float = 0.0) -> Optional[np.ndarray]:
        """Generate image based on audio features and prompt"""
        
        if not self.is_loaded or self.pipe is None:
            return None
        
        try:
            start_time = time.time()
            
            # Adjust generation parameters based on audio
            # Higher energy = more inference steps for better quality
            if audio_features.energy_level == "high":
                steps = min(4, num_inference_steps + 2)
            elif audio_features.energy_level == "low":
                steps = max(1, num_inference_steps - 1)
            else:
                steps = num_inference_steps
            
            # Beat detection can trigger more dramatic generation
            if audio_features.onset_detected and audio_features.beat_confidence > 1.5:
                guidance_scale = min(2.0, guidance_scale + 0.5)  # Slight guidance for beats
            
            # Generate image
            result = self.pipe(
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted",
                num_inference_steps=steps,
                height=size[1],
                width=size[0],
                guidance_scale=guidance_scale,
                output_type="pil"
            )
            
            image = result.images[0]
            
            # Convert to numpy array
            img_array = np.array(image)
            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]  # Drop alpha channel
            
            # BGR for OpenCV
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Update stats
            generation_time = time.time() - start_time
            self._update_stats(generation_time)
            
            return img_array
            
        except Exception as e:
            print(f"SD generation failed: {e}")
            return None
    
    def _update_stats(self, generation_time: float):
        """Update generation statistics"""
        self.generation_stats["total_generations"] += 1
        self.generation_stats["total_time"] += generation_time
        self.generation_stats["last_generation_time"] = generation_time
        self.generation_stats["average_time"] = (
            self.generation_stats["total_time"] / 
            self.generation_stats["total_generations"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            **self.generation_stats,
            "model_loaded": self.is_loaded,
            "device": self.device,
            "model_id": self.model_id
        }
    
    def cleanup(self):
        """Clean up GPU memory"""
        if self.pipe is not None:
            del self.pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.is_loaded = False

# Factory function for easy integration
def create_sd_generator(model_type: str = "turbo", **kwargs) -> StableDiffusionGenerator:
    """Create SD generator with preset configurations"""
    
    configs = {
        "turbo": {
            "model_id": "stabilityai/sdxl-turbo",
            "torch_dtype": torch.float16,
            "enable_cpu_offload": False
        },
        "lightning": {
            "model_id": "ByteDance/SDXL-Lightning",
            "torch_dtype": torch.float16,
            "enable_cpu_offload": False
        },
        "base": {
            "model_id": "stabilityai/stable-diffusion-xl-base-1.0", 
            "torch_dtype": torch.float16,
            "enable_cpu_offload": True
        }
    }
    
    if model_type not in configs:
        raise ValueError(f"Unknown model type: {model_type}. Available: {list(configs.keys())}")
    
    config = configs[model_type]
    config.update(kwargs)  # Override with user settings
    
    return StableDiffusionGenerator(**config)

# Integration function for keyframe manager
def sd_keyframe_generator(features: AudioFeatures, prompt: str, generator=None) -> Optional[np.ndarray]:
    """Generator function that can be passed to KeyframeManager"""
    if generator is None:
        print("No SD generator provided")
        return None
    
    return generator.generate_image(features, prompt)

if __name__ == "__main__":
    # Test SD generation
    import cv2
    from enhanced_audio_analyzer import EnhancedAudioAnalyzer
    
    print("Testing Stable Diffusion integration...")
    
    # Create generator
    try:
        generator = create_sd_generator("turbo")
        
        if generator.is_loaded:
            print("SD loaded successfully! Testing generation...")
            
            # Create dummy audio features
            features = AudioFeatures(
                rms=0.5,
                bass=0.3,
                mid=0.4,
                high=0.2,
                energy_level="medium",
                onset_detected=False
            )
            
            prompt = "vibrant abstract energy patterns, flowing colors, digital art"
            
            # Generate test image
            print(f"Generating: {prompt}")
            image = generator.generate_image(features, prompt)
            
            if image is not None:
                print("Generation successful!")
                cv2.imshow("SD Test", image)
                cv2.waitKey(3000)
                cv2.destroyAllWindows()
                
                stats = generator.get_stats()
                print(f"Generation time: {stats['last_generation_time']:.2f}s")
            else:
                print("Generation failed")
        
        generator.cleanup()
        
    except Exception as e:
        print(f"SD test failed: {e}")
        print("Make sure you have diffusers installed: pip install diffusers")