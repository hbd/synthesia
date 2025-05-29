#!/usr/bin/env python3
"""
Enhanced audio analyzer with beat detection and onset analysis
Builds on the basic AudioAnalyzer with advanced features for keyframe timing
"""

import numpy as np
import pyaudio
import queue
import threading
from scipy.fft import rfft, rfftfreq
from scipy.signal import find_peaks
from collections import deque
import time
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class AudioFeatures:
    # Basic features
    rms: float = 0.0
    bass: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    
    # Advanced features
    onset_detected: bool = False
    beat_confidence: float = 0.0
    tempo_bpm: float = 120.0
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    energy_delta: float = 0.0  # Change from previous frame
    
    # For keyframe timing
    should_generate_keyframe: bool = False
    energy_level: str = "medium"  # low, medium, high

class EnhancedAudioAnalyzer:
    def __init__(self, rate=44100, chunk_size=2048, history_size=10):
        self.rate = rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        
        # Feature history for temporal analysis
        self.feature_history = deque(maxlen=history_size)
        self.rms_history = deque(maxlen=30)  # For beat detection
        
        # Beat detection parameters
        self.last_beat_time = 0
        self.beat_threshold = 1.3  # Multiplier for beat detection
        self.min_beat_interval = 0.2  # Minimum time between beats (300 BPM max)
        
        # Tempo tracking
        self.beat_times = deque(maxlen=8)
        self.tempo_bpm = 120.0
        
        # Keyframe generation timing
        self.last_keyframe_time = 0
        self.keyframe_interval = 2.0  # Base interval in seconds
        self.energy_keyframe_threshold = 0.7  # Generate on high energy
        
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
        self.audio_queue.put((audio_data, time.time()))
        return (in_data, pyaudio.paContinue)
    
    def _detect_onset(self, current_rms: float) -> bool:
        """Detect audio onsets using energy-based method"""
        if len(self.rms_history) < 3:
            return False
            
        # Calculate local energy average
        recent_avg = np.mean(list(self.rms_history)[-3:])
        
        # Onset if current energy significantly exceeds recent average
        return current_rms > recent_avg * self.beat_threshold
    
    def _estimate_tempo(self, beat_time: float):
        """Estimate tempo from beat intervals"""
        self.beat_times.append(beat_time)
        
        if len(self.beat_times) >= 4:
            intervals = np.diff(list(self.beat_times))
            # Filter out unrealistic intervals
            valid_intervals = intervals[(intervals > 0.3) & (intervals < 2.0)]
            
            if len(valid_intervals) > 0:
                avg_interval = np.mean(valid_intervals)
                self.tempo_bpm = 60.0 / avg_interval
    
    def _should_generate_keyframe(self, features: AudioFeatures) -> bool:
        """Determine if a new keyframe should be generated"""
        current_time = time.time()
        time_since_last = current_time - self.last_keyframe_time
        
        # Generate keyframe if:
        # 1. Enough time has passed (base interval)
        # 2. High energy spike detected
        # 3. Beat detected and some time has passed
        
        base_interval_met = time_since_last >= self.keyframe_interval
        energy_spike = features.rms > self.energy_keyframe_threshold
        beat_triggered = (features.onset_detected and 
                         time_since_last > 0.5)  # At least 0.5s since last
        
        if base_interval_met or energy_spike or beat_triggered:
            self.last_keyframe_time = current_time
            return True
        
        return False
    
    def _classify_energy_level(self, rms: float) -> str:
        """Classify current energy level for prompt generation"""
        if rms < 0.2:
            return "low"
        elif rms < 0.6:
            return "medium"
        else:
            return "high"
    
    def get_features(self) -> Optional[AudioFeatures]:
        """Extract comprehensive audio features"""
        if self.audio_queue.empty():
            return None
            
        audio_data, timestamp = self.audio_queue.get()
        
        # Basic features
        rms = np.sqrt(np.mean(audio_data**2))
        self.rms_history.append(rms)
        
        # Frequency analysis
        fft = rfft(audio_data)
        freqs = rfftfreq(self.chunk_size, 1/self.rate)
        magnitude = np.abs(fft)
        
        # Frequency band analysis
        bass_mask = (freqs >= 20) & (freqs < 250)
        mid_mask = (freqs >= 250) & (freqs < 4000)
        high_mask = (freqs >= 4000) & (freqs < 20000)
        
        bass = np.mean(magnitude[bass_mask]) if np.any(bass_mask) else 0
        mid = np.mean(magnitude[mid_mask]) if np.any(mid_mask) else 0
        high = np.mean(magnitude[high_mask]) if np.any(high_mask) else 0
        
        # Advanced spectral features
        # Spectral centroid (brightness)
        spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-12)
        
        # Spectral rolloff (90% of energy cutoff)
        cumsum = np.cumsum(magnitude)
        rolloff_idx = np.where(cumsum >= 0.9 * cumsum[-1])[0]
        spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
        
        # Energy delta (change from previous frame)
        energy_delta = 0.0
        if len(self.rms_history) >= 2:
            energy_delta = rms - self.rms_history[-2]
        
        # Beat/onset detection
        onset_detected = self._detect_onset(rms)
        beat_confidence = min(rms / (np.mean(list(self.rms_history)[-5:]) + 1e-12), 3.0)
        
        # Update tempo if beat detected
        if onset_detected and timestamp - self.last_beat_time > self.min_beat_interval:
            self._estimate_tempo(timestamp)
            self.last_beat_time = timestamp
        
        # Create feature object
        features = AudioFeatures(
            rms=rms,
            bass=bass,
            mid=mid,
            high=high,
            onset_detected=onset_detected,
            beat_confidence=beat_confidence,
            tempo_bpm=self.tempo_bpm,
            spectral_centroid=spectral_centroid,
            spectral_rolloff=spectral_rolloff,
            energy_delta=energy_delta,
            energy_level=self._classify_energy_level(rms)
        )
        
        # Determine if keyframe should be generated
        features.should_generate_keyframe = self._should_generate_keyframe(features)
        
        # Store in history
        self.feature_history.append(features)
        
        return features
    
    def get_smoothed_features(self, window_size: int = 3) -> Optional[AudioFeatures]:
        """Get temporally smoothed features to reduce noise"""
        if len(self.feature_history) < window_size:
            return self.get_features()
        
        # Get recent features
        recent = list(self.feature_history)[-window_size:]
        
        # Smooth continuous values
        smoothed = AudioFeatures(
            rms=np.mean([f.rms for f in recent]),
            bass=np.mean([f.bass for f in recent]),
            mid=np.mean([f.mid for f in recent]),
            high=np.mean([f.high for f in recent]),
            spectral_centroid=np.mean([f.spectral_centroid for f in recent]),
            spectral_rolloff=np.mean([f.spectral_rolloff for f in recent]),
            energy_delta=recent[-1].energy_delta,  # Keep most recent
            
            # Boolean/categorical features from most recent
            onset_detected=recent[-1].onset_detected,
            beat_confidence=recent[-1].beat_confidence,
            tempo_bpm=self.tempo_bpm,
            should_generate_keyframe=recent[-1].should_generate_keyframe,
            energy_level=recent[-1].energy_level
        )
        
        return smoothed
    
    def cleanup(self):
        """Clean up audio resources"""
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'p') and self.p:
            self.p.terminate()

if __name__ == "__main__":
    # Test the enhanced analyzer
    print("Testing Enhanced Audio Analyzer...")
    print("Press Ctrl+C to stop")
    
    analyzer = EnhancedAudioAnalyzer()
    analyzer.stream.start_stream()
    
    try:
        while True:
            features = analyzer.get_features()
            if features:
                print(f"RMS: {features.rms:.3f}, "
                      f"Energy: {features.energy_level}, "
                      f"Beat: {features.onset_detected}, "
                      f"BPM: {features.tempo_bpm:.1f}, "
                      f"Keyframe: {features.should_generate_keyframe}")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        analyzer.cleanup()