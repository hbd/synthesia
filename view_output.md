# 🎬 Viewing Your Generated Audio-Visual Output

## 📁 **Generated Files Location**
- **Frames**: `output_frames/frame_XXXXXX.png` 
- **Videos**: `*.mp4` files when using `--save-video`

## 🖥️ **Viewing Options**

### **1. Download Files Locally**
The easiest way to view results:

```bash
# Zip all frames for download
cd /home/Ubuntu/prj/synthesia
zip -r audio_visual_output.zip output_frames/ *.mp4

# Or copy individual files you want to see
# Right-click files in file browser to download
```

### **2. Web-based Viewing** 
```bash
# Start simple web server to view in browser
cd output_frames
python3 -m http.server 8000

# Then visit: http://localhost:8000 in browser
# (if you have port forwarding set up)
```

### **3. Create GIF Animation**
```bash
# Install imagemagick
sudo apt install imagemagick

# Create animated GIF from frames
convert -delay 10 output_frames/frame_*.png output.gif
```

### **4. Command Line Preview**
```bash
# View file info
file output_frames/frame_000000.png
identify output_frames/frame_000000.png

# Convert to ASCII art (fun!)
jp2a --colors output_frames/frame_000000.png
```

### **5. X11 Display** (if GUI access available)
```bash
# View with image viewer
display output_frames/frame_000000.png
eog output_frames/frame_000000.png
```

## 🎥 **Current Output Status**
- ✅ Generated audio-reactive frames from YouTube video
- ✅ Each frame responds to music tempo (123 BPM detected)  
- ✅ Energy levels change colors and patterns
- ✅ Beat detection triggers visual changes

## 🚀 **Next Steps**
1. **Download frames** to see visual results
2. **Generate full video** with SD enabled for AI visuals
3. **Try different audio** (your own music files)
4. **Adjust parameters** (resolution, frame rate, style)

The system is working! You just need to get the files to view them locally.