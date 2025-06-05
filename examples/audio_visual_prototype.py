#!/usr/bin/env python3
"""
Real-time audio to visual prototype
Streams audio input and generates reactive visuals
"""

import numpy as np
import cv2
import pyaudio
import threading
import queue
from scipy.fft import rfft, rfftfreq
import time

class AudioAnalyzer:
    def __init__(self, rate=44100, chunk_size=2048):
        self.rate = rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=rate,
            input=True,
            frames_per_buffer=chunk_size,
            stream_callback=self._audio_callback
        )
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)
    
    def get_features(self):
        """Extract audio features in real-time"""
        if self.audio_queue.empty():
            return None
            
        audio_data = self.audio_queue.get()
        
        # Basic features
        rms = np.sqrt(np.mean(audio_data**2))  # Volume
        
        # Frequency analysis
        fft = rfft(audio_data)
        freqs = rfftfreq(self.chunk_size, 1/self.rate)
        
        # Band analysis (bass, mid, high)
        bass = np.mean(np.abs(fft[(freqs > 20) & (freqs < 250)]))
        mid = np.mean(np.abs(fft[(freqs > 250) & (freqs < 4000)]))
        high = np.mean(np.abs(fft[(freqs > 4000) & (freqs < 20000)]))
        
        return {
            'rms': rms,
            'bass': bass,
            'mid': mid,
            'high': high
        }

class VisualEngine:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.frame = np.zeros((height, width, 3), dtype=np.uint8)
        
    def update(self, audio_features):
        """Generate visuals based on audio features"""
        if not audio_features:
            return self.frame
            
        # Clear with color based on bass
        bass_color = int(audio_features['bass'] * 1000) % 255
        self.frame[:] = (bass_color//4, bass_color//8, bass_color//2)
        
        # Center circle reacts to RMS (volume)
        radius = int(50 + audio_features['rms'] * 500)
        cv2.circle(self.frame, 
                  (self.width//2, self.height//2), 
                  radius, 
                  (255, 255, 255), 
                  -1)
        
        # Side bars for frequency bands
        bar_width = 50
        bass_height = int(audio_features['bass'] * 2000) % self.height
        mid_height = int(audio_features['mid'] * 2000) % self.height
        high_height = int(audio_features['high'] * 2000) % self.height
        
        # Draw frequency bars
        cv2.rectangle(self.frame, (0, self.height-bass_height), 
                     (bar_width, self.height), (255, 0, 0), -1)
        cv2.rectangle(self.frame, (bar_width, self.height-mid_height), 
                     (bar_width*2, self.height), (0, 255, 0), -1)
        cv2.rectangle(self.frame, (bar_width*2, self.height-high_height), 
                     (bar_width*3, self.height), (0, 0, 255), -1)
        
        return self.frame

def main():
    print("Starting audio-visual stream...")
    print("Press 'q' to quit")
    
    analyzer = AudioAnalyzer()
    visual = VisualEngine()
    
    # Start audio stream
    analyzer.stream.start_stream()
    
    try:
        while True:
            # Get audio features
            features = analyzer.get_features()
            
            # Generate visuals
            frame = visual.update(features)
            
            # Display
            cv2.imshow('Audio Visualizer', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        analyzer.stream.stop_stream()
        analyzer.stream.close()
        analyzer.p.terminate()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()