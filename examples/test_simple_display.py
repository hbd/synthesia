#!/usr/bin/env python3
"""
Simple test to verify the audio-visual system works
"""

import cv2
import time
import numpy as np
from src.analyzers.enhanced_audio_analyzer import EnhancedAudioAnalyzer

def main():
    print("Testing simple audio-visual display...")
    print("You should see:")
    print("1. A window titled 'Audio Test' appear")
    print("2. Audio level bars that react to sound")
    print("3. Background that changes with audio")
    print("4. Beat indicators when you make noise")
    print("\nMake some noise (clap, speak, play music) to see reactions!")
    print("Press 'q' in the window to quit\n")
    
    analyzer = EnhancedAudioAnalyzer()
    analyzer.stream.start_stream()
    
    try:
        while True:
            features = analyzer.get_features()
            
            if features:
                # Create a simple visualization
                img = np.zeros((400, 600, 3), dtype=np.uint8)
                
                # Background color based on audio
                bg_color = int(features.rms * 100)
                img[:] = (bg_color, bg_color//2, bg_color//3)
                
                # Audio level bars
                bar_height = 300
                bar_width = 50
                
                # Bass bar (red)
                bass_h = int(features.bass * bar_height)
                cv2.rectangle(img, (50, 350-bass_h), (50+bar_width, 350), (0, 0, 255), -1)
                cv2.putText(img, 'BASS', (55, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Mid bar (green) 
                mid_h = int(features.mid * bar_height)
                cv2.rectangle(img, (150, 350-mid_h), (150+bar_width, 350), (0, 255, 0), -1)
                cv2.putText(img, 'MID', (160, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # High bar (blue)
                high_h = int(features.high * bar_height)
                cv2.rectangle(img, (250, 350-high_h), (250+bar_width, 350), (255, 0, 0), -1)
                cv2.putText(img, 'HIGH', (255, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Beat indicator
                if features.onset_detected:
                    cv2.circle(img, (500, 100), 50, (255, 255, 0), -1)
                    cv2.putText(img, 'BEAT!', (460, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                
                # Info text
                cv2.putText(img, f'RMS: {features.rms:.3f}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, f'Energy: {features.energy_level}', (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, f'BPM: {features.tempo_bpm:.1f}', (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if features.should_generate_keyframe:
                    cv2.putText(img, 'KEYFRAME!', (350, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                
                cv2.imshow('Audio Test', img)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            time.sleep(0.03)  # ~30 fps
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        analyzer.cleanup()
        cv2.destroyAllWindows()
        print("Test complete!")

if __name__ == "__main__":
    main()