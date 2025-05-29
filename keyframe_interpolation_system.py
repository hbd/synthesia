#!/usr/bin/env python3
"""
Integrated Keyframe + Interpolation System
Combines all components for real-time audio-reactive visual generation
"""

import cv2
import time
import numpy as np
from typing import Optional, Callable
import argparse

from enhanced_audio_analyzer import EnhancedAudioAnalyzer, AudioFeatures
from keyframe_manager import KeyframeManager, Keyframe
from frame_interpolator import FrameInterpolator

class AudioVisualSystem:
    """Main system integrating audio analysis, keyframe generation, and interpolation"""
    
    def __init__(self, 
                 custom_generator: Optional[Callable] = None,
                 target_fps: int = 30,
                 keyframe_cache_size: int = 4,
                 window_size: tuple = (800, 600)):
        
        # Initialize components
        self.analyzer = EnhancedAudioAnalyzer()
        self.keyframe_manager = KeyframeManager(
            generator_func=custom_generator,
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
        self.stats_interval = 2.0  # Show stats every 2 seconds
        
        # Display settings
        self.show_stats_overlay = True
        self.show_audio_waveform = True
        
    def _create_stats_overlay(self, frame: np.ndarray, 
                             audio_features: AudioFeatures) -> np.ndarray:
        """Add performance stats and audio info overlay to frame"""
        if not self.show_stats_overlay:
            return frame
        
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Semi-transparent background for text
        cv2.rectangle(overlay, (10, 10), (300, 150), (0, 0, 0), -1)
        cv2.addWeighted(frame, 0.7, overlay, 0.3, 0, frame)
        
        # Get system stats
        fps_stats = self.interpolator.get_fps_stats()
        manager_stats = self.keyframe_manager.get_stats()
        
        # Text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (255, 255, 255)
        thickness = 1
        
        # Display stats
        y_offset = 30
        line_height = 20
        
        stats_lines = [
            f"FPS: {fps_stats['fps']:.1f} / {self.target_fps}",
            f"Frame Time: {fps_stats['avg_frame_time']*1000:.1f}ms",
            f"Keyframes: {manager_stats['cached_keyframes']}",
            f"Generating: {'Yes' if manager_stats['is_generating'] else 'No'}",
            f"Gen Time: {manager_stats['avg_generation_time']:.2f}s",
            f"Audio RMS: {audio_features.rms:.3f}" if audio_features else "",
            f"Energy: {audio_features.energy_level}" if audio_features else "",
            f"BPM: {audio_features.tempo_bpm:.1f}" if audio_features else ""
        ]
        
        for i, line in enumerate(stats_lines):
            if line:  # Skip empty lines
                cv2.putText(frame, line, (15, y_offset + i * line_height), 
                           font, font_scale, color, thickness)
        
        return frame
    
    def _create_audio_waveform(self, frame: np.ndarray, 
                              audio_features: AudioFeatures) -> np.ndarray:
        """Add audio waveform visualization to frame"""
        if not self.show_audio_waveform or not audio_features:
            return frame
        
        h, w = frame.shape[:2]
        
        # Waveform area at bottom
        waveform_height = 60
        waveform_y = h - waveform_height - 10
        
        # Background for waveform
        cv2.rectangle(frame, (10, waveform_y), (w - 10, h - 10), (20, 20, 20), -1)
        
        # Audio level bars
        bar_width = (w - 40) // 3
        bar_spacing = 10
        
        # Bass bar (red)
        bass_height = int(audio_features.bass * (waveform_height - 20))
        cv2.rectangle(frame, 
                     (20, waveform_y + waveform_height - 10 - bass_height),
                     (20 + bar_width, waveform_y + waveform_height - 10),
                     (0, 0, 255), -1)
        cv2.putText(frame, "BASS", (25, waveform_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Mid bar (green)
        mid_height = int(audio_features.mid * (waveform_height - 20))
        mid_x = 30 + bar_width + bar_spacing
        cv2.rectangle(frame, 
                     (mid_x, waveform_y + waveform_height - 10 - mid_height),
                     (mid_x + bar_width, waveform_y + waveform_height - 10),
                     (0, 255, 0), -1)
        cv2.putText(frame, "MID", (mid_x + 5, waveform_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # High bar (blue)
        high_height = int(audio_features.high * (waveform_height - 20))
        high_x = 40 + 2 * (bar_width + bar_spacing)
        cv2.rectangle(frame, 
                     (high_x, waveform_y + waveform_height - 10 - high_height),
                     (high_x + bar_width, waveform_y + waveform_height - 10),
                     (255, 0, 0), -1)
        cv2.putText(frame, "HIGH", (high_x + 5, waveform_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Beat indicator
        if audio_features.onset_detected:
            cv2.circle(frame, (w - 30, waveform_y + 20), 15, (255, 255, 0), -1)
            cv2.putText(frame, "BEAT", (w - 60, waveform_y + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def run(self, duration: Optional[float] = None):
        """Run the audio-visual system"""
        print("Starting Audio-Visual Keyframe Interpolation System...")
        print("Controls:")
        print("  q - Quit")
        print("  s - Toggle stats overlay")
        print("  w - Toggle waveform display")
        print("  r - Reset interpolator")
        print()
        
        self.running = True
        start_time = time.time()
        
        # Start audio stream
        self.analyzer.stream.start_stream()
        
        # Generate initial keyframe
        print("Generating initial keyframe...")
        time.sleep(0.5)  # Let audio data accumulate
        
        try:
            while self.running:
                frame_start_time = time.time()
                
                # Check duration limit
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Get audio features
                features = self.analyzer.get_smoothed_features()
                
                if features:
                    # Request new keyframes when needed
                    if features.should_generate_keyframe:
                        success = self.keyframe_manager.request_keyframe(features)
                        if success:
                            print(f"New keyframe requested - Energy: {features.energy_level}, "
                                  f"Beat: {features.onset_detected}")
                    
                    # Update interpolator with latest keyframes
                    keyframes = self.keyframe_manager.get_latest_keyframes(2)
                    
                    if len(keyframes) >= 2:
                        # Check if we need to update keyframes
                        if (self.interpolator.current_keyframe != keyframes[-2] or 
                            self.interpolator.next_keyframe != keyframes[-1]):
                            self.interpolator.set_keyframes(keyframes[-2], keyframes[-1])
                            print(f"Updated interpolation keyframes")
                    
                    elif len(keyframes) == 1:
                        # Single keyframe - just apply effects
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
                        frame = self._create_stats_overlay(frame, features)
                        frame = self._create_audio_waveform(frame, features)
                        
                        # Display frame
                        cv2.imshow('Audio-Visual Keyframe System', frame)
                        self.frame_count += 1
                        
                        # Show periodic stats
                        if time.time() - self.last_stats_time > self.stats_interval:
                            fps_stats = self.interpolator.get_fps_stats()
                            manager_stats = self.keyframe_manager.get_stats()
                            print(f"Performance - FPS: {fps_stats['fps']:.1f}, "
                                  f"Keyframes: {manager_stats['cached_keyframes']}, "
                                  f"Avg Gen Time: {manager_stats['avg_generation_time']:.2f}s")
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
                
                # Frame rate limiting
                frame_time = time.time() - frame_start_time
                sleep_time = max(0, self.frame_time - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\\nInterrupted by user")
        
        except Exception as e:
            print(f"\\nError: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all system resources"""
        print("Cleaning up...")
        self.running = False
        
        if hasattr(self, 'analyzer'):
            self.analyzer.cleanup()
        
        if hasattr(self, 'keyframe_manager'):
            self.keyframe_manager.cleanup()
        
        cv2.destroyAllWindows()
        print("Cleanup complete")

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Audio-Visual Keyframe Interpolation System')
    parser.add_argument('--fps', type=int, default=30, help='Target FPS (default: 30)')
    parser.add_argument('--duration', type=float, help='Run duration in seconds')
    parser.add_argument('--width', type=int, default=800, help='Window width (default: 800)')
    parser.add_argument('--height', type=int, default=600, help='Window height (default: 600)')
    parser.add_argument('--cache-size', type=int, default=4, help='Keyframe cache size (default: 4)')
    parser.add_argument('--no-stats', action='store_true', help='Disable stats overlay')
    parser.add_argument('--no-waveform', action='store_true', help='Disable waveform display')
    
    args = parser.parse_args()
    
    # Create and configure system
    system = AudioVisualSystem(
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