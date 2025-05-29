#!/usr/bin/env python3
"""
Keyframe Manager for timed image generation
Handles keyframe generation, caching, and scheduling for smooth interpolation
"""

import numpy as np
import cv2
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Callable, Any
import queue
from enhanced_audio_analyzer import AudioFeatures

@dataclass
class Keyframe:
    image: np.ndarray
    timestamp: float
    audio_features: AudioFeatures
    prompt: str = ""
    generation_time: float = 0.0

class PromptGenerator:
    """Enhanced prompt generator using audio features"""
    
    def __init__(self):
        self.base_prompts = {
            "low": [
                "serene flowing abstract art",
                "gentle watercolor waves", 
                "soft pastel gradients",
                "calm minimalist composition"
            ],
            "medium": [
                "dynamic flowing energy patterns",
                "vibrant abstract expressionism",
                "rhythmic geometric forms",
                "colorful liquid motion"
            ],
            "high": [
                "explosive abstract energy burst",
                "chaotic lightning patterns",
                "intense fractal structures",
                "dramatic high-contrast forms"
            ]
        }
        
        self.style_modifiers = {
            "bass": ["deep reds", "warm oranges", "rich purples", "earthy tones"],
            "mid": ["vibrant greens", "golden yellows", "bright cyans", "organic colors"],
            "high": ["electric blues", "pure whites", "silver highlights", "crystalline"]
        }
        
        self.tempo_modifiers = {
            "slow": ["flowing", "graceful", "smooth"],
            "medium": ["pulsing", "rhythmic", "balanced"], 
            "fast": ["rapid", "staccato", "energetic"]
        }
    
    def generate_prompt(self, features: AudioFeatures) -> str:
        """Generate a detailed prompt based on audio features"""
        # Base prompt from energy level
        base = np.random.choice(self.base_prompts[features.energy_level])
        
        # Dominant frequency determines color palette
        if features.bass > max(features.mid, features.high):
            colors = np.random.choice(self.style_modifiers["bass"])
        elif features.mid > features.high:
            colors = np.random.choice(self.style_modifiers["mid"])
        else:
            colors = np.random.choice(self.style_modifiers["high"])
        
        # Tempo-based movement modifier
        if features.tempo_bpm < 80:
            movement = np.random.choice(self.tempo_modifiers["slow"])
        elif features.tempo_bpm < 140:
            movement = np.random.choice(self.tempo_modifiers["medium"])
        else:
            movement = np.random.choice(self.tempo_modifiers["fast"])
        
        # Special modifiers for onsets
        onset_modifier = ""
        if features.onset_detected and features.beat_confidence > 1.5:
            onset_modifier = ", explosive burst, radiating energy"
        
        # Construct final prompt
        prompt = f"{movement} {colors} {base}{onset_modifier}, high quality, 4k, abstract art"
        
        return prompt

class ProceduralGenerator:
    """Fallback procedural image generator"""
    
    def __init__(self, size=(512, 512)):
        self.size = size
        
    def generate(self, features: AudioFeatures, prompt: str) -> np.ndarray:
        """Generate procedural image based on audio features"""
        h, w = self.size
        img = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Color mapping from audio features
        r = int(np.clip(features.bass * 255, 0, 255))
        g = int(np.clip(features.mid * 255, 0, 255))
        b = int(np.clip(features.high * 255, 0, 255))
        
        # Energy-based background pattern
        if features.energy_level == "low":
            # Gentle gradient
            for y in range(h):
                fade = y / h
                intensity = 0.3 + 0.4 * np.sin(fade * np.pi)
                img[y, :] = [r * intensity, g * intensity, b * intensity]
                
        elif features.energy_level == "medium":
            # Circular patterns
            center_x, center_y = w // 2, h // 2
            for y in range(h):
                for x in range(w):
                    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    intensity = 0.5 + 0.5 * np.sin(dist * 0.02 + features.rms * 10)
                    img[y, x] = [r * intensity, g * intensity, b * intensity]
                    
        else:  # high energy
            # Chaotic noise pattern
            noise = np.random.rand(h, w, 3)
            img = ((noise * 0.7 + 0.3) * [r, g, b]).astype(np.uint8)
        
        # Add reactive elements based on spectral features
        center_x, center_y = w // 2, h // 2
        
        # Bass circle
        if features.bass > 0.1:
            radius = int(20 + features.bass * 80)
            color = (min(255, r + 50), g // 2, b // 2)
            cv2.circle(img, (center_x - 60, center_y), radius, color, -1)
        
        # Mid frequency square
        if features.mid > 0.1:
            size = int(30 + features.mid * 60)
            color = (r // 2, min(255, g + 50), b // 2)
            cv2.rectangle(img, 
                         (center_x - size//2, center_y - size//2),
                         (center_x + size//2, center_y + size//2),
                         color, -1)
        
        # High frequency details
        if features.high > 0.1:
            num_points = int(3 + features.high * 10)
            for _ in range(num_points):
                x = np.random.randint(0, w)
                y = np.random.randint(0, h)
                radius = int(2 + features.high * 8)
                color = (r // 2, g // 2, min(255, b + 50))
                cv2.circle(img, (x, y), radius, color, -1)
        
        # Beat-reactive flash
        if features.onset_detected and features.beat_confidence > 1.3:
            flash_intensity = min(100, int(features.beat_confidence * 30))
            img = np.clip(img.astype(np.float32) + flash_intensity, 0, 255).astype(np.uint8)
        
        return img

class KeyframeManager:
    """Manages keyframe generation, caching, and timing"""
    
    def __init__(self, 
                 generator_func: Optional[Callable] = None,
                 max_cache_size: int = 4,
                 generation_timeout: float = 5.0):
        
        self.generator_func = generator_func
        self.procedural_gen = ProceduralGenerator()
        self.prompt_gen = PromptGenerator()
        
        # Keyframe storage
        self.keyframes = deque(maxlen=max_cache_size)
        self.generation_queue = queue.Queue()
        self.generation_timeout = generation_timeout
        
        # Threading for async generation
        self.generation_thread = None
        self.is_generating = False
        self.should_stop = False
        
        # Performance tracking
        self.generation_times = deque(maxlen=10)
        self.last_generation_start = None
        
        # Start background generation thread
        self._start_generation_thread()
    
    def _start_generation_thread(self):
        """Start the background image generation thread"""
        self.generation_thread = threading.Thread(
            target=self._generation_worker,
            daemon=True
        )
        self.generation_thread.start()
    
    def _generation_worker(self):
        """Background worker for image generation"""
        while not self.should_stop:
            try:
                # Wait for generation request
                request = self.generation_queue.get(timeout=1.0)
                features, timestamp = request
                
                self.is_generating = True
                gen_start_time = time.time()
                
                # Generate prompt
                prompt = self.prompt_gen.generate_prompt(features)
                
                # Generate image
                image = None
                if self.generator_func:
                    try:
                        # Try custom generator (SD/FLUX) with timeout
                        image = self.generator_func(features, prompt)
                    except Exception as e:
                        print(f"Custom generator failed: {e}")
                        image = None
                
                # Fallback to procedural generation
                if image is None:
                    image = self.procedural_gen.generate(features, prompt)
                
                generation_time = time.time() - gen_start_time
                self.generation_times.append(generation_time)
                
                # Create keyframe
                keyframe = Keyframe(
                    image=image,
                    timestamp=timestamp,
                    audio_features=features,
                    prompt=prompt,
                    generation_time=generation_time
                )
                
                # Add to cache
                self.keyframes.append(keyframe)
                self.is_generating = False
                
                # Mark task as done
                self.generation_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Generation error: {e}")
                self.is_generating = False
                
    def request_keyframe(self, features: AudioFeatures) -> bool:
        """Request a new keyframe generation"""
        if self.is_generating or self.generation_queue.qsize() > 2:
            return False  # Skip if busy or queue full
        
        timestamp = time.time()
        try:
            self.generation_queue.put_nowait((features, timestamp))
            return True
        except queue.Full:
            return False
    
    def get_latest_keyframes(self, count: int = 2) -> List[Keyframe]:
        """Get the most recent keyframes for interpolation"""
        if len(self.keyframes) < count:
            return list(self.keyframes)
        return list(self.keyframes)[-count:]
    
    def get_keyframe_for_time(self, timestamp: float) -> Optional[Keyframe]:
        """Get the best keyframe for a given timestamp"""
        if not self.keyframes:
            return None
        
        # Find the keyframe with timestamp closest to requested time
        best_keyframe = min(self.keyframes, 
                           key=lambda kf: abs(kf.timestamp - timestamp))
        return best_keyframe
    
    def get_interpolation_pair(self, current_time: float) -> tuple[Optional[Keyframe], Optional[Keyframe]]:
        """Get a pair of keyframes for interpolation at current time"""
        if len(self.keyframes) < 2:
            if len(self.keyframes) == 1:
                return self.keyframes[0], self.keyframes[0]
            return None, None
        
        # Sort keyframes by timestamp
        sorted_keyframes = sorted(self.keyframes, key=lambda kf: kf.timestamp)
        
        # Find the two keyframes to interpolate between
        prev_kf, next_kf = None, None
        
        for i in range(len(sorted_keyframes) - 1):
            if (sorted_keyframes[i].timestamp <= current_time <= 
                sorted_keyframes[i + 1].timestamp):
                prev_kf = sorted_keyframes[i]
                next_kf = sorted_keyframes[i + 1]
                break
        
        # If we're past all keyframes, use the last two
        if prev_kf is None:
            prev_kf = sorted_keyframes[-2]
            next_kf = sorted_keyframes[-1]
        
        return prev_kf, next_kf
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        return {
            "cached_keyframes": len(self.keyframes),
            "is_generating": self.is_generating,
            "queue_size": self.generation_queue.qsize(),
            "avg_generation_time": np.mean(self.generation_times) if self.generation_times else 0,
            "max_generation_time": np.max(self.generation_times) if self.generation_times else 0
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.should_stop = True
        if self.generation_thread and self.generation_thread.is_alive():
            self.generation_thread.join(timeout=2.0)

if __name__ == "__main__":
    # Test the keyframe manager
    from enhanced_audio_analyzer import EnhancedAudioAnalyzer
    
    print("Testing Keyframe Manager...")
    print("Press Ctrl+C to stop")
    
    analyzer = EnhancedAudioAnalyzer()
    manager = KeyframeManager()
    
    analyzer.stream.start_stream()
    
    try:
        while True:
            features = analyzer.get_features()
            if features:
                if features.should_generate_keyframe:
                    success = manager.request_keyframe(features)
                    print(f"Keyframe requested: {success}")
                
                stats = manager.get_stats()
                print(f"Cache: {stats['cached_keyframes']}, "
                      f"Gen: {stats['is_generating']}, "
                      f"Avg time: {stats['avg_generation_time']:.2f}s")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        analyzer.cleanup()
        manager.cleanup()