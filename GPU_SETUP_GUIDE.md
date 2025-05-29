# GPU Setup Guide for RTX A6000 x2

This guide optimizes Synthesia for high-performance GPU setups, specifically dual RTX A6000 systems.

## Hardware Capabilities

**RTX A6000 Specifications:**
- 48GB VRAM per GPU (96GB total)
- 10,752 CUDA cores per GPU
- PCIe 4.0 support
- NVLink support (if connected)

**Expected Performance Improvements:**
- **SDXL-Turbo**: 50-100ms per image (vs 1-3s on consumer GPUs)
- **Multiple models**: Run SD + FLUX + Mochi simultaneously
- **Higher resolution**: 1024x1024 or 1536x1536 real-time generation
- **Multiple streams**: Generate different styles in parallel

## Software Setup

### 1. CUDA and PyTorch Installation

```bash
# For RTX A6000, install CUDA 12.1+ and PyTorch with CUDA support
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify GPU detection
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}'); print([torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])"
```

### 2. Optimized Dependencies

```bash
# High-performance inference
pip install xformers flash-attn
pip install bitsandbytes  # For memory optimization
pip install triton  # For custom kernels

# Optional: TensorRT for maximum speed
pip install nvidia-tensorrt
```

### 3. System Configuration

```bash
# Set GPU memory fraction (optional - A6000 has plenty)
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Enable optimizations
export TORCH_CUDA_ARCH_LIST="8.6"  # RTX A6000 architecture
export CUDA_LAUNCH_BLOCKING=0  # Async CUDA calls
```

## Performance Optimizations

### 1. Multi-GPU Configuration

**Option A: Model Parallelism**
```python
# Load different models on different GPUs
sd_generator_gpu0 = StableDiffusionGenerator(device="cuda:0")  # SDXL-Turbo
flux_generator_gpu1 = FluxGenerator(device="cuda:1")          # FLUX
```

**Option B: Pipeline Parallelism**
```python
# One GPU generates, other processes
generator_gpu = "cuda:0"     # Generation
interpolation_gpu = "cuda:1" # Post-processing
```

### 2. Memory Optimization

```python
# A6000 config - maximize quality and speed
generator_config = {
    "torch_dtype": torch.float16,  # or bfloat16
    "enable_cpu_offload": False,   # Keep everything on GPU
    "enable_attention_slicing": False,  # Disable for A6000
    "enable_vae_slicing": False,   # Disable for A6000
    "enable_sequential_cpu_offload": False
}
```

### 3. Compilation Optimizations

```python
# Compile models for maximum speed
if hasattr(torch, 'compile'):
    pipe.unet = torch.compile(pipe.unet, mode="max-autotune")
    pipe.vae.decode = torch.compile(pipe.vae.decode, mode="max-autotune")
```

## Recommended Settings for RTX A6000

### 1. High-Performance Mode

```bash
# Ultra-fast generation
python audio_visual_sd_system.py \
    --sd-model turbo \
    --fps 60 \
    --width 1024 \
    --height 1024 \
    --cache-size 8
```

### 2. Multi-Model Mode (Future)

```bash
# Run multiple models simultaneously
python audio_visual_sd_system.py \
    --models sdxl-turbo,flux-schnell \
    --multi-gpu \
    --fps 30 \
    --resolution 1536x1536
```

### 3. Production Streaming Mode

```bash
# For live performances/streaming
python audio_visual_sd_system.py \
    --fps 60 \
    --resolution 1920x1080 \
    --record output.mp4 \
    --stream rtmp://your.stream.url
```

## Expected Performance Benchmarks

### Single RTX A6000
- **SDXL-Turbo**: 50-80ms at 512x512, 100-150ms at 1024x1024
- **FLUX-Schnell**: 200-400ms at 1024x1024
- **Frame interpolation**: 60+ fps at 1080p

### Dual RTX A6000
- **Parallel generation**: 2x throughput
- **Mixed models**: SDXL + FLUX simultaneously
- **Higher resolution**: 1536x1536+ real-time
- **Recording**: 4K60 output while generating

## GPU Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Detailed monitoring
pip install gpustat
gpustat -i 1
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size or resolution
   - Enable gradient checkpointing
   - Use CPU offload for VAE

2. **Slow Performance**
   - Check CUDA version compatibility
   - Verify xformers installation
   - Enable torch.compile

3. **Multi-GPU Issues**
   - Set CUDA_VISIBLE_DEVICES
   - Check NVLink connectivity
   - Balance memory usage

### Performance Monitoring Code

```python
# Add to your system for GPU monitoring
import torch

def monitor_gpu():
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        memory = torch.cuda.memory_stats(i)
        print(f"GPU {i}: {props.name}")
        print(f"  Memory: {memory['allocated_bytes.all.current']/1e9:.1f}GB / {props.total_memory/1e9:.1f}GB")
        print(f"  Utilization: {torch.cuda.utilization(i)}%")
```

## Next Steps on RTX A6000

1. **Test basic system**: Verify 60+ fps operation
2. **Enable advanced models**: FLUX, Mochi, custom models
3. **Implement multi-GPU**: Parallel generation pipelines
4. **Add recording**: High-resolution video output
5. **Optimize prompts**: Complex, detailed prompts with fast generation
6. **Real-time streaming**: Live performance integration

The RTX A6000 setup will transform this from a demo into a professional-grade audio-visual generation system!