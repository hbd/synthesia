#!/usr/bin/env python3
"""
Frame Interpolator with audio-reactive warping
Handles smooth transitions between keyframes with real-time audio modulation
"""

import numpy as np
import cv2
from typing import Optional, Tuple
from enhanced_audio_analyzer import AudioFeatures
from keyframe_manager import Keyframe
import time

class FrameInterpolator:
    """Handles interpolation between keyframes with audio-reactive effects"""
    
    def __init__(self, target_fps: int = 30):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        
        # Current interpolation state
        self.current_keyframe: Optional[Keyframe] = None
        self.next_keyframe: Optional[Keyframe] = None
        self.interpolation_start_time: float = 0.0
        self.base_interpolation_duration: float = 2.0  # Base duration between keyframes
        
        # Audio-reactive parameters
        self.zoom_intensity = 0.1  # How much beats affect zoom
        self.rotation_intensity = 0.5  # How much high frequencies affect rotation
        self.warp_intensity = 0.3  # How much energy affects warping
        
        # Smoothing for stable effects
        self.zoom_smoothing = 0.8
        self.rotation_smoothing = 0.7
        self.current_zoom = 1.0
        self.current_rotation = 0.0
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.frame_times = []
        
    def set_keyframes(self, current: Keyframe, next_kf: Keyframe):
        """Set the keyframes to interpolate between"""
        self.current_keyframe = current
        self.next_keyframe = next_kf
        self.interpolation_start_time = time.time()
        
        # Adjust interpolation duration based on audio energy
        if current.audio_features and next_kf.audio_features:
            avg_energy = (current.audio_features.rms + next_kf.audio_features.rms) / 2
            # Higher energy = faster transitions
            energy_multiplier = 0.5 + (1.0 - avg_energy) * 0.5
            self.base_interpolation_duration = 2.0 * energy_multiplier
    
    def _calculate_interpolation_alpha(self, current_time: float, audio_features: AudioFeatures) -> float:
        """Calculate interpolation alpha with audio modulation"""
        if not self.current_keyframe or not self.next_keyframe:
            return 0.0
        
        # Base linear interpolation
        elapsed = current_time - self.interpolation_start_time
        base_alpha = min(1.0, elapsed / self.base_interpolation_duration)
        
        # Audio modulation
        if audio_features:
            # Beat detection speeds up interpolation temporarily
            beat_boost = 0.0
            if audio_features.onset_detected and audio_features.beat_confidence > 1.2:
                beat_boost = 0.1 * (audio_features.beat_confidence - 1.0)
            
            # Energy level affects overall speed
            energy_modifier = {
                "low": 0.8,
                "medium": 1.0, 
                "high": 1.3
            }.get(audio_features.energy_level, 1.0)
            
            # Apply modulations
            modulated_alpha = base_alpha * energy_modifier + beat_boost
            return np.clip(modulated_alpha, 0.0, 1.0)
        
        return base_alpha
    
    def _apply_audio_warping(self, image: np.ndarray, audio_features: AudioFeatures) -> np.ndarray:
        """Apply audio-reactive warping effects to the image"""
        if not audio_features:
            return image
        
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Calculate target zoom based on RMS energy
        target_zoom = 1.0 + audio_features.rms * self.zoom_intensity
        
        # Beat detection causes zoom pulses
        if audio_features.onset_detected and audio_features.beat_confidence > 1.3:
            beat_zoom = 1.0 + (audio_features.beat_confidence - 1.0) * 0.05
            target_zoom *= beat_zoom
        
        # Smooth zoom changes
        self.current_zoom = (self.zoom_smoothing * self.current_zoom + 
                           (1 - self.zoom_smoothing) * target_zoom)
        
        # Calculate rotation based on high frequencies and tempo
        target_rotation = (audio_features.high * self.rotation_intensity * 
                         np.sin(time.time() * audio_features.tempo_bpm / 60.0 * 0.1))
        
        # Smooth rotation changes
        self.current_rotation = (self.rotation_smoothing * self.current_rotation + 
                               (1 - self.rotation_smoothing) * target_rotation)
        
        # Apply zoom and rotation
        if abs(self.current_zoom - 1.0) > 0.001 or abs(self.current_rotation) > 0.001:
            M = cv2.getRotationMatrix2D((center_x, center_y), 
                                      self.current_rotation, 
                                      self.current_zoom)
            image = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        
        # Apply subtle warping based on energy delta
        if abs(audio_features.energy_delta) > 0.05:
            warp_strength = audio_features.energy_delta * self.warp_intensity * 10
            
            # Create displacement field for subtle warping
            if abs(warp_strength) > 0.01:
                y_indices, x_indices = np.mgrid[0:h, 0:w]
                
                # Sinusoidal displacement
                displacement_x = warp_strength * np.sin(y_indices * 0.02) * 2
                displacement_y = warp_strength * np.cos(x_indices * 0.02) * 2
                
                # Apply displacement
                new_x = (x_indices + displacement_x).astype(np.float32)
                new_y = (y_indices + displacement_y).astype(np.float32)
                
                image = cv2.remap(image, new_x, new_y, cv2.INTER_LINEAR, 
                                borderMode=cv2.BORDER_REFLECT)
        
        return image
    
    def _blend_images(self, img1: np.ndarray, img2: np.ndarray, alpha: float) -> np.ndarray:
        """Blend two images with given alpha"""
        if img1.shape != img2.shape:
            # Resize to match if shapes differ
            h, w = img1.shape[:2]
            img2 = cv2.resize(img2, (w, h))
        
        # Convert to float for blending
        img1_f = img1.astype(np.float32)
        img2_f = img2.astype(np.float32)
        
        # Blend
        blended = (1 - alpha) * img1_f + alpha * img2_f
        
        return np.clip(blended, 0, 255).astype(np.uint8)
    
    def _apply_crossfade_effect(self, img1: np.ndarray, img2: np.ndarray, 
                               alpha: float, audio_features: AudioFeatures) -> np.ndarray:
        """Apply advanced crossfade effects based on audio"""
        if not audio_features:
            return self._blend_images(img1, img2, alpha)
        
        # Different blend modes based on energy
        if audio_features.energy_level == "high" and audio_features.onset_detected:
            # Hard cut on strong beats in high energy
            return img2 if alpha > 0.5 else img1
        
        elif audio_features.energy_level == "low":
            # Soft, slow fade for low energy
            smooth_alpha = alpha ** 2  # Ease-in curve
            return self._blend_images(img1, img2, smooth_alpha)
        
        else:
            # Normal linear blend for medium energy
            return self._blend_images(img1, img2, alpha)
    
    def _add_audio_overlay_effects(self, image: np.ndarray, audio_features: AudioFeatures) -> np.ndarray:
        """Add overlay effects based on audio features"""
        if not audio_features:
            return image
        
        # Beat flash effect
        if audio_features.onset_detected and audio_features.beat_confidence > 1.5:
            flash_intensity = min(50, int((audio_features.beat_confidence - 1.0) * 30))
            # Add white flash
            overlay = np.full_like(image, flash_intensity, dtype=np.uint8)
            image = cv2.addWeighted(image, 0.9, overlay, 0.1, 0)
        
        # High frequency sparkles
        if audio_features.high > 0.3:
            h, w = image.shape[:2]
            num_sparkles = int(audio_features.high * 20)
            
            for _ in range(num_sparkles):
                x = np.random.randint(0, w)
                y = np.random.randint(0, h)
                intensity = int(audio_features.high * 255)
                cv2.circle(image, (x, y), 2, (intensity, intensity, intensity), -1)
        
        # Bass glow effect
        if audio_features.bass > 0.4:
            # Add subtle glow around edges
            glow_strength = int(audio_features.bass * 20)
            kernel = np.ones((5, 5), np.float32) / 25
            blurred = cv2.filter2D(image, -1, kernel)
            image = cv2.addWeighted(image, 0.8, blurred, 0.2 * audio_features.bass, glow_strength)
        
        return image
    
    def interpolate(self, audio_features: AudioFeatures, current_time: Optional[float] = None) -> Optional[np.ndarray]:
        """Generate interpolated frame based on current audio state"""
        if current_time is None:
            current_time = time.time()
        
        # Track frame timing
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 60:  # Keep last 60 frames
            self.frame_times.pop(0)
        self.last_frame_time = current_time
        
        # Need at least one keyframe
        if not self.current_keyframe:
            return None
        
        # If no next keyframe, just apply effects to current
        if not self.next_keyframe:
            image = self.current_keyframe.image.copy()
            image = self._apply_audio_warping(image, audio_features)
            image = self._add_audio_overlay_effects(image, audio_features)
            return image
        
        # Calculate interpolation alpha
        alpha = self._calculate_interpolation_alpha(current_time, audio_features)
        
        # Get base images
        img1 = self.current_keyframe.image.copy()
        img2 = self.next_keyframe.image.copy()
        
        # Apply audio warping to both images before blending
        img1 = self._apply_audio_warping(img1, audio_features)
        img2 = self._apply_audio_warping(img2, audio_features)
        
        # Blend images with crossfade effect
        result = self._apply_crossfade_effect(img1, img2, alpha, audio_features)
        
        # Add overlay effects
        result = self._add_audio_overlay_effects(result, audio_features)
        
        return result
    
    def get_fps_stats(self) -> dict:
        """Get frame rate statistics"""
        if not self.frame_times:
            return {"fps": 0, "avg_frame_time": 0}
        
        avg_frame_time = np.mean(self.frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        return {
            "fps": fps,
            "avg_frame_time": avg_frame_time,
            "target_fps": self.target_fps,
            "frame_time_std": np.std(self.frame_times)
        }
    
    def reset(self):
        """Reset interpolation state"""
        self.current_keyframe = None
        self.next_keyframe = None
        self.interpolation_start_time = 0.0
        self.current_zoom = 1.0
        self.current_rotation = 0.0

if __name__ == "__main__":
    # Test the frame interpolator
    from enhanced_audio_analyzer import EnhancedAudioAnalyzer
    from keyframe_manager import KeyframeManager
    
    print("Testing Frame Interpolator...")
    print("Press Ctrl+C to stop")
    
    analyzer = EnhancedAudioAnalyzer()
    manager = KeyframeManager()
    interpolator = FrameInterpolator()
    
    analyzer.stream.start_stream()
    
    # Generate initial keyframes
    time.sleep(1.0)  # Let some audio data accumulate
    
    try:
        frame_count = 0
        last_stats_time = time.time()
        
        while True:
            features = analyzer.get_features()
            if features:
                # Request new keyframes when needed
                if features.should_generate_keyframe:
                    manager.request_keyframe(features)
                
                # Get keyframes for interpolation
                keyframes = manager.get_latest_keyframes(2)
                
                if len(keyframes) >= 2:
                    if (interpolator.current_keyframe != keyframes[-2] or 
                        interpolator.next_keyframe != keyframes[-1]):
                        interpolator.set_keyframes(keyframes[-2], keyframes[-1])
                elif len(keyframes) == 1:
                    if interpolator.current_keyframe != keyframes[0]:
                        interpolator.current_keyframe = keyframes[0]
                        interpolator.next_keyframe = None
                
                # Generate interpolated frame
                frame = interpolator.interpolate(features)
                
                if frame is not None:
                    cv2.imshow('Keyframe Interpolation', frame)
                    frame_count += 1
                    
                    # Show stats every 2 seconds
                    if time.time() - last_stats_time > 2.0:
                        fps_stats = interpolator.get_fps_stats()
                        manager_stats = manager.get_stats()
                        print(f"FPS: {fps_stats['fps']:.1f}, "
                              f"Keyframes: {manager_stats['cached_keyframes']}, "
                              f"Generating: {manager_stats['is_generating']}")
                        last_stats_time = time.time()
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Small delay to target frame rate
            time.sleep(1.0 / 30.0)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        analyzer.cleanup()
        manager.cleanup()
        cv2.destroyAllWindows()