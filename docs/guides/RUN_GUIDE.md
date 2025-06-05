# How to Run Synthesia

## Quick Start (macOS)

```bash
# 1. Run the setup script
./setup.sh

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Run the basic visualizer
python audio_visual_prototype.py
```

## What to Expect

When you run `audio_visual_prototype.py`:
1. A window will open showing the visualizer
2. It will use your default microphone input
3. You'll see:
   - Center circle: Reacts to overall volume (RMS)
   - Background color: Changes with bass frequencies
   - Left bars: Red (bass), Green (mid), Blue (high) frequencies
4. Press 'q' to quit

## Troubleshooting

### "No module named 'pyaudio'"
```bash
# macOS: Install portaudio first
brew install portaudio

# Then reinstall pyaudio
pip install --force-reinstall pyaudio
```

### "Cannot find input device"
- Check System Preferences → Security & Privacy → Microphone
- Make sure Terminal/Python has microphone access

### "Module 'cv2' not found"
```bash
pip install opencv-python
```

## Testing with Music

1. Play music on your computer
2. macOS: Install BlackHole (virtual audio device) to route system audio
3. Or simply play music near your microphone

## Next Steps

Once basic visualizer works:

1. **Try the advanced version** (procedural visuals only for now):
   ```bash
   python audio_visual_sd.py
   ```

2. **Enable Stable Diffusion** (requires GPU):
   - Uncomment the diffusers imports in `audio_visual_sd.py`
   - Set `use_sd=True` when creating AudioVisualEngine

3. **Use with ComfyUI**:
   - Copy `comfyui_integration.py` to `ComfyUI/custom_nodes/synthesia/`
   - Restart ComfyUI
   - Look for "Audio" category in node menu