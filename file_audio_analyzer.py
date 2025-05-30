#!/usr/bin/env python3
"""
File-based audio analyzer for processing MP3/WAV files
Provides real-time-like analysis of pre-recorded audio files
"""

import numpy as np
import librosa
import soundfile as sf
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional, List
from enhanced_audio_analyzer import AudioFeatures

class FileAudioAnalyzer:
    """Analyzes audio files and provides real-time-like streaming of features"""
    
    def __init__(self, audio_file: str, target_fps: int = 30, chunk_duration: float = 0.033):
        """
        Initialize file audio analyzer
        
        Args:
            audio_file: Path to MP3/WAV file
            target_fps: Target analysis rate (frames per second)
            chunk_duration: Duration of each analysis chunk in seconds
        """
        self.audio_file = audio_file
        self.target_fps = target_fps
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(chunk_duration * 44100)  # Assuming 44.1kHz
        
        # Load audio file
        print(f"Loading audio file: {audio_file}")
        self.audio_data, self.sample_rate = librosa.load(audio_file, sr=44100)
        self.duration = len(self.audio_data) / self.sample_rate
        print(f"Loaded: {self.duration:.1f}s @ {self.sample_rate}Hz")
        
        # Analysis state
        self.current_position = 0
        self.is_playing = False
        self.start_time = None
        
        # Feature history for temporal analysis
        self.feature_history = deque(maxlen=10)
        self.rms_history = deque(maxlen=30)
        
        # Beat detection
        self.last_beat_time = 0
        self.beat_threshold = 1.3
        
        # Keyframe timing
        self.last_keyframe_time = 0
        self.keyframe_interval = 2.0  # seconds between keyframes
        
        # Pre-compute some features for efficiency
        self._precompute_features()
    
    def _precompute_features(self):
        """Pre-compute some expensive features"""
        print("Pre-computing audio features...")
        
        # Compute tempo
        tempo, _ = librosa.beat.beat_track(y=self.audio_data, sr=self.sample_rate)
        self.estimated_tempo = float(tempo)
        
        # Compute spectral features for the entire track
        hop_length = 512
        self.spectral_centroids = librosa.feature.spectral_centroid(
            y=self.audio_data, sr=self.sample_rate, hop_length=hop_length
        )[0]
        self.spectral_rolloffs = librosa.feature.spectral_rolloff(
            y=self.audio_data, sr=self.sample_rate, hop_length=hop_length
        )[0]
        
        print(f"Estimated tempo: {self.estimated_tempo:.1f} BPM")
        print("Pre-computation complete")
    
    def start_playback(self):
        """Start 'playback' - begins streaming audio features"""
        self.is_playing = True
        self.start_time = time.time()
        self.current_position = 0
        print(f"Starting audio analysis playback ({self.duration:.1f}s)")
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        print("Audio playback stopped")
    
    def get_current_time(self) -> float:
        """Get current playback time in seconds"""
        if not self.is_playing or self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def is_finished(self) -> bool:
        """Check if we've reached the end of the audio file"""
        return self.get_current_time() >= self.duration
    
    def get_smoothed_features(self) -> Optional[AudioFeatures]:
        """Get current audio features based on playback position"""
        if not self.is_playing:
            return None
            
        current_time = self.get_current_time()
        
        # Check if we've reached the end
        if current_time >= self.duration:
            return None
        
        # Calculate sample position
        sample_pos = int(current_time * self.sample_rate)
        
        # Extract current chunk
        start_sample = max(0, sample_pos)
        end_sample = min(len(self.audio_data), start_sample + self.chunk_samples)
        
        if start_sample >= len(self.audio_data):
            return None
            
        chunk = self.audio_data[start_sample:end_sample]
        
        if len(chunk) == 0:
            return None
        
        # Compute features for this chunk
        features = self._analyze_chunk(chunk, current_time)
        
        # Add to history
        self.feature_history.append(features)
        
        return features
    
    def _analyze_chunk(self, chunk: np.ndarray, current_time: float) -> AudioFeatures:
        """Analyze a chunk of audio and return features"""
        
        # Basic amplitude analysis
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        self.rms_history.append(rms)
        
        # Frequency analysis
        fft = np.abs(np.fft.rfft(chunk))
        freqs = np.fft.rfftfreq(len(chunk), 1/self.sample_rate)
        
        # Frequency bands
        bass_mask = freqs < 250
        mid_mask = (freqs >= 250) & (freqs < 4000)
        high_mask = freqs >= 4000
        
        bass = float(np.mean(fft[bass_mask])) if np.any(bass_mask) else 0.0
        mid = float(np.mean(fft[mid_mask])) if np.any(mid_mask) else 0.0
        high = float(np.mean(fft[high_mask])) if np.any(high_mask) else 0.0
        
        # Beat detection (simple energy-based)
        onset_detected = False
        beat_confidence = 0.0
        
        if len(self.rms_history) > 5:
            recent_avg = np.mean(list(self.rms_history)[-5:])
            overall_avg = np.mean(list(self.rms_history))
            
            if recent_avg > overall_avg * self.beat_threshold:
                if current_time - self.last_beat_time > 0.1:  # Minimum beat interval
                    onset_detected = True
                    beat_confidence = min(1.0, (recent_avg / overall_avg - 1.0))
                    self.last_beat_time = current_time
        
        # Spectral features (use pre-computed when possible)
        frame_idx = int(current_time * self.sample_rate / 512)  # hop_length = 512
        
        if frame_idx < len(self.spectral_centroids):
            spectral_centroid = float(self.spectral_centroids[frame_idx])
            spectral_rolloff = float(self.spectral_rolloffs[frame_idx])
        else:
            # Fallback computation
            spectral_centroid = float(np.sum(freqs * fft) / np.sum(fft)) if np.sum(fft) > 0 else 0.0
            spectral_rolloff = float(freqs[np.where(np.cumsum(fft) >= 0.85 * np.sum(fft))[0][0]]) if len(fft) > 0 else 0.0
        
        # Energy level classification
        energy_level = "low"
        if rms > 0.1:
            energy_level = "high"
        elif rms > 0.05:
            energy_level = "medium"
        
        # Energy delta (change from previous)
        energy_delta = 0.0
        if len(self.rms_history) > 1:
            energy_delta = rms - list(self.rms_history)[-2]
        
        # Keyframe timing
        should_generate_keyframe = False
        if (current_time - self.last_keyframe_time > self.keyframe_interval or 
            onset_detected or 
            abs(energy_delta) > 0.05):
            should_generate_keyframe = True
            self.last_keyframe_time = current_time
        
        return AudioFeatures(
            rms=rms,
            bass=bass,
            mid=mid,
            high=high,
            onset_detected=onset_detected,
            beat_confidence=beat_confidence,
            tempo_bpm=self.estimated_tempo,
            spectral_centroid=spectral_centroid,
            spectral_rolloff=spectral_rolloff,
            energy_delta=energy_delta,
            should_generate_keyframe=should_generate_keyframe,
            energy_level=energy_level
        )
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_playback()
        print("File audio analyzer cleaned up")

def test_file_analyzer(audio_file: str):
    """Test the file audio analyzer"""
    analyzer = FileAudioAnalyzer(audio_file)
    analyzer.start_playback()
    
    try:
        while not analyzer.is_finished():
            features = analyzer.get_smoothed_features()
            if features:
                print(f"Time: {analyzer.get_current_time():.2f}s | "
                      f"RMS: {features.rms:.3f} | "
                      f"Energy: {features.energy_level} | "
                      f"Beat: {features.onset_detected} | "
                      f"BPM: {features.tempo_bpm:.1f}")
            time.sleep(0.1)  # 10 FPS analysis
    finally:
        analyzer.cleanup()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python file_audio_analyzer.py <audio_file>")
        sys.exit(1)
    
    test_file_analyzer(sys.argv[1])