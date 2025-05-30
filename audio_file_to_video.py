#!/usr/bin/env python3
"""
Audio File to Video Generator
Process MP3/WAV files and generate real-time audio-reactive visuals
"""

import cv2
import time
import numpy as np
import argparse
import traceback
import os
from typing import Optional

from file_audio_analyzer import FileAudioAnalyzer
from keyframe_manager import KeyframeManager, Keyframe
from frame_interpolator import FrameInterpolator

# Import SD generator with fallback
try:
    from stable_diffusion_generator import create_sd_generator, StableDiffusionGenerator
    SD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Stable Diffusion not available: {e}")
    SD_AVAILABLE = False

class AudioFileToVideoSystem:
    """Generate video from audio files using Stable Diffusion"""
    
    def __init__(self,
                 audio_file: str,
                 use_sd: bool = True,
                 sd_model: str = "turbo",
                 target_fps: int = 30,
                 keyframe_cache_size: int = 4,
                 output_size: tuple = (1024, 768),
                 save_video: bool = False,
                 output_path: str = "output.mp4"):
        
        print(f"Initializing Audio File to Video System...")
        print(f"Input: {audio_file}")
        print(f"Output: {output_path if save_video else 'Live Preview'}")
        
        # Validate audio file
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Initialize file audio analyzer
        self.audio_analyzer = FileAudioAnalyzer(audio_file, target_fps=target_fps)
        
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
        def custom_generator(features, prompt: str) -> Optional[np.ndarray]:
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
        self.output_size = output_size
        self.save_video = save_video
        self.output_path = output_path
        
        # Video writer
        self.video_writer = None
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                output_path, fourcc, target_fps, output_size
            )
            print(f"Video will be saved to: {output_path}")
        
        # Performance monitoring
        self.frame_count = 0
        self.start_time = None
        
        print(f"System initialized - SD: {'ON' if self.use_sd else 'OFF'}")
    
    def _create_stats_overlay(self, frame: np.ndarray, features, current_time: float) -> np.ndarray:
        """Add performance and audio stats overlay"""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
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
        y_offset = 25
        line_height = 18
        
        stats_lines = [
            f"Time: {current_time:.1f}s / {self.audio_analyzer.duration:.1f}s",
            f"FPS: {fps_stats['fps']:.1f} / {self.target_fps}",
            f"Keyframes: {manager_stats['cached_keyframes']} cached",
            f"Generating: {'Yes' if manager_stats['is_generating'] else 'No'}",
            "",
            f"Audio RMS: {features.rms:.3f}" if features else "No audio",
            f"Energy: {features.energy_level}" if features else "",
            f"Beat: {'Yes' if features and features.onset_detected else 'No'}",
        ]
        
        # Draw text
        for i, line in enumerate(stats_lines):
            if line:  # Skip empty lines
                cv2.putText(frame, line, (15, y_offset + i * line_height), 
                           font, font_scale, color, thickness)
        
        return frame
    
    def process_audio_file(self, show_preview: bool = True, save_frames: bool = False):
        """Process the audio file and generate video"""
        print(f"\\nStarting audio file processing...")
        print("Controls: Press 'q' to quit, 's' to toggle stats")
        
        self.start_time = time.time()
        frame_count = 0
        
        # Start audio analysis
        self.audio_analyzer.start_playback()
        
        # Create output directory for frames if needed
        if save_frames:
            os.makedirs("output_frames", exist_ok=True)
        
        try:
            while not self.audio_analyzer.is_finished():
                frame_start_time = time.time()
                
                # Get audio features
                features = self.audio_analyzer.get_smoothed_features()
                current_time = self.audio_analyzer.get_current_time()
                
                if features:
                    # Request new keyframes when needed
                    if features.should_generate_keyframe:
                        success = self.keyframe_manager.request_keyframe(features)
                        if success:
                            generation_type = "SD" if self.use_sd else "Procedural"
                            print(f"{generation_type} keyframe @ {current_time:.1f}s - "
                                  f"Energy: {features.energy_level}, "
                                  f"Beat: {features.onset_detected}")
                    
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
                        # Resize to target size
                        if frame.shape[:2] != (self.output_size[1], self.output_size[0]):
                            frame = cv2.resize(frame, self.output_size)
                        
                        # Add stats overlay
                        frame = self._create_stats_overlay(frame, features, current_time)
                        
                        # Save frame if requested
                        if save_frames:
                            frame_filename = f"output_frames/frame_{frame_count:06d}.png"
                            cv2.imwrite(frame_filename, frame)
                        
                        # Write to video file
                        if self.video_writer:
                            self.video_writer.write(frame)
                        
                        # Show preview
                        if show_preview:
                            cv2.imshow('Synthesia - Audio File to Video', frame)
                            
                            # Handle keyboard input
                            key = cv2.waitKey(1) & 0xFF
                            if key == ord('q'):
                                break
                        
                        frame_count += 1
                        
                        # Progress update
                        if frame_count % (self.target_fps * 5) == 0:  # Every 5 seconds
                            progress = (current_time / self.audio_analyzer.duration) * 100
                            print(f"Progress: {progress:.1f}% ({current_time:.1f}s)")
                
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
            
        # Final stats
        total_time = time.time() - self.start_time
        print(f"\\nProcessing complete!")
        print(f"Generated {frame_count} frames in {total_time:.1f}s")
        print(f"Average FPS: {frame_count / total_time:.1f}")
        
        if save_frames:
            print(f"Frames saved to: output_frames/")
        if self.save_video:
            print(f"Video saved to: {self.output_path}")
    
    def cleanup(self):
        """Clean up all system resources"""
        print("\\nCleaning up...")
        
        if hasattr(self, 'audio_analyzer'):
            self.audio_analyzer.cleanup()
        
        if hasattr(self, 'keyframe_manager'):
            self.keyframe_manager.cleanup()
        
        if hasattr(self, 'sd_generator') and self.sd_generator:
            self.sd_generator.cleanup()
            
        if self.video_writer:
            self.video_writer.release()
        
        cv2.destroyAllWindows()
        print("Cleanup complete")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate video from audio files using AI')
    parser.add_argument('audio_file', help='Path to MP3/WAV audio file')
    parser.add_argument('--no-sd', action='store_true', help='Disable Stable Diffusion')
    parser.add_argument('--sd-model', choices=['turbo', 'lightning', 'base'], 
                       default='turbo', help='SD model to use (default: turbo)')
    parser.add_argument('--fps', type=int, default=30, help='Target FPS (default: 30)')
    parser.add_argument('--width', type=int, default=1024, help='Output width (default: 1024)')
    parser.add_argument('--height', type=int, default=768, help='Output height (default: 768)')
    parser.add_argument('--output', type=str, default='output.mp4', help='Output video file')
    parser.add_argument('--save-video', action='store_true', help='Save video to file')
    parser.add_argument('--save-frames', action='store_true', help='Save individual frames')
    parser.add_argument('--no-preview', action='store_true', help='Disable live preview')
    parser.add_argument('--cache-size', type=int, default=6, help='Keyframe cache size')
    
    args = parser.parse_args()
    
    # Create system
    system = AudioFileToVideoSystem(
        audio_file=args.audio_file,
        use_sd=not args.no_sd,
        sd_model=args.sd_model,
        target_fps=args.fps,
        output_size=(args.width, args.height),
        save_video=args.save_video,
        output_path=args.output,
        keyframe_cache_size=args.cache_size
    )
    
    # Process the file
    system.process_audio_file(
        show_preview=not args.no_preview,
        save_frames=args.save_frames
    )

if __name__ == "__main__":
    main()