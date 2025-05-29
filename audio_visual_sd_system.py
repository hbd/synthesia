#!/usr/bin/env python3
"""
Audio-Visual System with Stable Diffusion Integration
Real-time audio-reactive visuals using SDXL-Turbo for keyframe generation
"""

import cv2
import time
import numpy as np
from typing import Optional, Callable
import argparse
import traceback

from enhanced_audio_analyzer import EnhancedAudioAnalyzer, AudioFeatures
from keyframe_manager import KeyframeManager, Keyframe
from frame_interpolator import FrameInterpolator

# Import SD generator with fallback
try:
    from stable_diffusion_generator import create_sd_generator, StableDiffusionGenerator
    SD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Stable Diffusion not available: {e}")
    print("Install with: pip install torch torchvision diffusers")
    SD_AVAILABLE = False

class AudioVisualSDSystem:
    """Audio-Visual system with Stable Diffusion keyframe generation"""
    
    def __init__(self,
                 use_sd: bool = True,
                 sd_model: str = "turbo",
                 target_fps: int = 30,
                 keyframe_cache_size: int = 4,
                 window_size: tuple = (800, 600)):
        
        print("Initializing Audio-Visual SD System...")
        
        # Initialize audio analyzer first
        self.analyzer = EnhancedAudioAnalyzer()
        
        # Initialize SD generator
        self.sd_generator = None
        self.use_sd = use_sd and SD_AVAILABLE
        
        if self.use_sd:
            try:
                print(f"Loading Stable Diffusion ({sd_model})...")
                self.sd_generator = create_sd_generator(sd_model)
                if not self.sd_generator.is_loaded:
                    print("SD failed to load, falling back to procedural generation")
                    self.use_sd = False
            except Exception as e:
                print(f"SD initialization failed: {e}")
                print("Falling back to procedural generation")
                self.use_sd = False
        else:
            print("Using procedural generation only")
        
        # Create generator function for keyframe manager
        def custom_generator(features: AudioFeatures, prompt: str) -> Optional[np.ndarray]:
            if self.use_sd and self.sd_generator and self.sd_generator.is_loaded:
                return self.sd_generator.generate_image(features, prompt)
            return None
        
        # Initialize other components
        self.keyframe_manager = KeyframeManager(
            generator_func=custom_generator if self.use_sd else None,
            max_cache_size=keyframe_cache_size
        )
        self.interpolator = FrameInterpolator(target_fps=target_fps)
        
        # System settings
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.window_size = window_size
        self.running = False
        
        # Performance monitoring
        self.frame_count = 0
        self.last_stats_time = time.time()
        self.stats_interval = 3.0  # Show stats every 3 seconds
        
        # Display settings
        self.show_stats_overlay = True
        self.show_audio_waveform = True
        self.show_sd_stats = True
        
        print(f"System initialized - SD: {'ON' if self.use_sd else 'OFF'}")
    
    def _create_enhanced_stats_overlay(self, frame: np.ndarray, 
                                     audio_features: AudioFeatures) -> np.ndarray:
        """Enhanced stats overlay including SD performance"""
        if not self.show_stats_overlay:
            return frame
        
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Larger background for more stats
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(frame, 0.7, overlay, 0.3, 0, frame)
        
        # Get system stats
        fps_stats = self.interpolator.get_fps_stats()
        manager_stats = self.keyframe_manager.get_stats()
        
        # Text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        color = (255, 255, 255)
        thickness = 1
        
        # Display stats
        y_offset = 25
        line_height = 18
        
        stats_lines = [
            f"FPS: {fps_stats['fps']:.1f} / {self.target_fps}",
            f"Frame Time: {fps_stats['avg_frame_time']*1000:.1f}ms",
            f"Keyframes: {manager_stats['cached_keyframes']} cached",
            f"Queue: {manager_stats['queue_size']} pending",
            f"Generating: {'Yes' if manager_stats['is_generating'] else 'No'}",
            f"Avg Gen Time: {manager_stats['avg_generation_time']:.2f}s",
            ""  # Separator
        ]
        
        # Add SD-specific stats
        if self.use_sd and self.sd_generator:
            sd_stats = self.sd_generator.get_stats()
            stats_lines.extend([
                f"SD Model: {'Loaded' if sd_stats['model_loaded'] else 'Failed'}",
                f"SD Device: {sd_stats['device']}",
                f"SD Generations: {sd_stats['total_generations']}",
                f"SD Avg Time: {sd_stats['average_time']:.2f}s",
                f"SD Last Time: {sd_stats['last_generation_time']:.2f}s"
            ])
        else:
            stats_lines.append("SD: Disabled/Unavailable")
        
        # Audio stats
        if audio_features:
            stats_lines.extend([
                "",  # Separator
                f"Audio RMS: {audio_features.rms:.3f}",
                f"Energy: {audio_features.energy_level}",
                f"BPM: {audio_features.tempo_bpm:.1f}",
                f"Beat: {'Yes' if audio_features.onset_detected else 'No'}",
                f"Spectral: {audio_features.spectral_centroid:.0f}Hz"
            ])
        
        # Draw text
        for i, line in enumerate(stats_lines):
            if line:  # Skip empty lines
                cv2.putText(frame, line, (15, y_offset + i * line_height), 
                           font, font_scale, color, thickness)
        
        return frame
    
    def _create_generation_indicator(self, frame: np.ndarray) -> np.ndarray:
        """Add visual indicator when generating new keyframes"""
        manager_stats = self.keyframe_manager.get_stats()
        
        if manager_stats['is_generating']:
            h, w = frame.shape[:2]
            
            # Pulsing border to indicate generation
            pulse = int(50 + 30 * np.sin(time.time() * 8))
            border_color = (0, pulse, 255)  # Orange-red pulse
            
            cv2.rectangle(frame, (0, 0), (w-1, h-1), border_color, 3)
            
            # "GENERATING" text
            cv2.putText(frame, "GENERATING...", (w//2 - 80, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, border_color, 2)
        
        return frame
    
    def run(self, duration: Optional[float] = None):
        """Run the audio-visual system with SD integration"""
        print("\\nStarting Audio-Visual System with Stable Diffusion...")
        print("\\nControls:")
        print("  q - Quit")
        print("  s - Toggle stats overlay")
        print("  w - Toggle waveform display")
        print("  r - Reset interpolator")
        print("  g - Force generate keyframe")
        if self.use_sd:
            print("  t - Toggle SD (enable/disable)")
        print()
        
        self.running = True
        start_time = time.time()
        
        # Start audio stream
        self.analyzer.stream.start_stream()
        
        # Force initial keyframe generation
        print("Generating initial keyframe...")
        time.sleep(0.5)  # Let audio accumulate
        
        try:
            while self.running:
                frame_start_time = time.time()
                
                # Check duration limit
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Get audio features
                features = self.analyzer.get_smoothed_features()
                
                if features:
                    # Force initial keyframe if none exist
                    if len(self.keyframe_manager.keyframes) == 0:
                        self.keyframe_manager.request_keyframe(features)
                        print("Requested initial keyframe")
                    
                    # Request new keyframes when needed
                    elif features.should_generate_keyframe:
                        success = self.keyframe_manager.request_keyframe(features)
                        if success:
                            generation_type = "SD" if self.use_sd else "Procedural"
                            print(f"{generation_type} keyframe requested - "
                                  f"Energy: {features.energy_level}, "
                                  f"Beat: {features.onset_detected}, "
                                  f"RMS: {features.rms:.3f}")
                    
                    # Update interpolator with latest keyframes
                    keyframes = self.keyframe_manager.get_latest_keyframes(2)
                    
                    if len(keyframes) >= 2:
                        if (self.interpolator.current_keyframe != keyframes[-2] or 
                            self.interpolator.next_keyframe != keyframes[-1]):
                            self.interpolator.set_keyframes(keyframes[-2], keyframes[-1])
                    elif len(keyframes) == 1:
                        if self.interpolator.current_keyframe != keyframes[0]:
                            self.interpolator.current_keyframe = keyframes[0]
                            self.interpolator.next_keyframe = None
                    
                    # Generate interpolated frame
                    frame = self.interpolator.interpolate(features)
                    
                    if frame is not None:
                        # Resize to window size if needed
                        if frame.shape[:2] != (self.window_size[1], self.window_size[0]):
                            frame = cv2.resize(frame, self.window_size)
                        
                        # Add overlays
                        frame = self._create_enhanced_stats_overlay(frame, features)
                        if self.show_audio_waveform:
                            frame = self.interpolator._add_audio_overlay_effects(frame, features)
                        frame = self._create_generation_indicator(frame)
                        
                        # Display frame
                        cv2.imshow('Synthesia - Audio Visual SD System', frame)
                        self.frame_count += 1
                        
                        # Show periodic stats in console
                        if time.time() - self.last_stats_time > self.stats_interval:
                            fps_stats = self.interpolator.get_fps_stats()
                            manager_stats = self.keyframe_manager.get_stats()
                            
                            print(f"\\n--- Performance Stats ---")
                            print(f"FPS: {fps_stats['fps']:.1f}, "
                                  f"Keyframes: {manager_stats['cached_keyframes']}, "
                                  f"Generating: {manager_stats['is_generating']}")
                            
                            if self.use_sd and self.sd_generator:
                                sd_stats = self.sd_generator.get_stats()
                                print(f"SD: {sd_stats['total_generations']} images, "
                                      f"avg {sd_stats['average_time']:.2f}s")
                            
                            self.last_stats_time = time.time()
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.show_stats_overlay = not self.show_stats_overlay
                    print(f"Stats overlay: {'ON' if self.show_stats_overlay else 'OFF'}")
                elif key == ord('w'):
                    self.show_audio_waveform = not self.show_audio_waveform
                    print(f"Waveform display: {'ON' if self.show_audio_waveform else 'OFF'}")
                elif key == ord('r'):
                    self.interpolator.reset()
                    print("Interpolator reset")
                elif key == ord('g'):
                    if features:
                        self.keyframe_manager.request_keyframe(features)
                        print("Manual keyframe generation requested")
                elif key == ord('t') and self.sd_generator:
                    self.use_sd = not self.use_sd
                    print(f"SD generation: {'ON' if self.use_sd else 'OFF'}")
                
                # Frame rate limiting
                frame_time = time.time() - frame_start_time
                sleep_time = max(0, self.frame_time - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\\nInterrupted by user")
        
        except Exception as e:
            print(f"\\nError: {e}")
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all system resources"""
        print("\\nCleaning up...")
        self.running = False
        
        if hasattr(self, 'analyzer'):
            self.analyzer.cleanup()
        
        if hasattr(self, 'keyframe_manager'):
            self.keyframe_manager.cleanup()
        
        if hasattr(self, 'sd_generator') and self.sd_generator:
            self.sd_generator.cleanup()
        
        cv2.destroyAllWindows()
        print("Cleanup complete")

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Audio-Visual System with Stable Diffusion')
    parser.add_argument('--no-sd', action='store_true', help='Disable Stable Diffusion')
    parser.add_argument('--sd-model', choices=['turbo', 'lightning', 'base'], 
                       default='turbo', help='SD model to use (default: turbo)')
    parser.add_argument('--fps', type=int, default=30, help='Target FPS (default: 30)')
    parser.add_argument('--duration', type=float, help='Run duration in seconds')
    parser.add_argument('--width', type=int, default=800, help='Window width (default: 800)')
    parser.add_argument('--height', type=int, default=600, help='Window height (default: 600)')
    parser.add_argument('--cache-size', type=int, default=4, help='Keyframe cache size (default: 4)')
    parser.add_argument('--no-stats', action='store_true', help='Disable stats overlay')
    parser.add_argument('--no-waveform', action='store_true', help='Disable waveform display')
    
    args = parser.parse_args()
    
    # Create and configure system
    system = AudioVisualSDSystem(
        use_sd=not args.no_sd,
        sd_model=args.sd_model,
        target_fps=args.fps,
        keyframe_cache_size=args.cache_size,
        window_size=(args.width, args.height)
    )
    
    if args.no_stats:
        system.show_stats_overlay = False
    if args.no_waveform:
        system.show_audio_waveform = False
    
    # Run the system
    system.run(duration=args.duration)

if __name__ == "__main__":
    main()