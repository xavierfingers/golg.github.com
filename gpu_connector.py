import pyopencl as cl
import numpy as np

print("[INFO] Initializing PyOpenCL...")

# --- 1. List Platforms and Devices ---
print("\n--- OpenCL Platforms and Devices ---")
platforms = cl.get_platforms()
if not platforms:
    print("No OpenCL platforms found. Please ensure OpenCL drivers are installed.")
    exit()

for platform_idx, platform in enumerate(platforms):
    print(f"Platform {platform_idx}: {platform.name}")
    devices = platform.get_devices()
    if not devices:
        print(f"  No devices found for Platform {platform.name}")
    for device_idx, device in enumerate(devices):
        print(f"  Device {device_idx}: {device.name} (Type: {cl.device_type.to_string(device.type)}) ")
        print(f"    Max Clock Freq: {device.max_clock_frequency} MHz")
        print(f"    Global Mem Size: {device.global_mem_size / (1024**3):.2f} GB")
        print(f"    Max Work Group Size: {device.max_work_group_size}")

# --- 2. Select a GPU Device ---
# Try to find the first GPU device
gpu_device = None
for platform in platforms:
    devices = platform.get_devices(device_type=cl.device_type.GPU)
    if devices:
        gpu_device = devices[0]
        print(f"\n[INFO] Selected GPU device: {gpu_device.name} from Platform: {platform.name}")
        break

if gpu_device is None:
    print("\n[ERROR] No GPU device found. Falling back to CPU if available.")
    # If no GPU, try to find a CPU device
    for platform in platforms:
        devices = platform.get_devices(device_type=cl.device_type.CPU)
        if devices:
            gpu_device = devices[0] # Renaming for consistency, but it's a CPU
            print(f"[INFO] Selected CPU device: {gpu_device.name} from Platform: {platform.name}")
            break

if gpu_device is None:
    print("\n[ERROR] No suitable OpenCL device (GPU or CPU) found. Exiting.")
    exit()

# --- 3. Create Context and Command Queue ---
context = cl.Context([gpu_device])
queue = cl.CommandQueue(context)
print("[INFO] OpenCL Context and Command Queue created.")

# --- 4. Define a Simple Kernel (Vector Addition) ---
kernel_code = """
__kernel void vec_add(__global const float *a, 
                      __global const float *b, 
                      __global float *c)
{
    int gid = get_global_id(0);
    c[gid] = a[gid] + b[gid];
}
"""

program = cl.Program(context, kernel_code).build()
print("[INFO] OpenCL Kernel compiled.")

# --- 5. Prepare Host Data ---
ARRAY_SIZE = 1000000 # A million elements
a_host = np.random.rand(ARRAY_SIZE).astype(np.float32)
b_host = np.random.rand(ARRAY_SIZE).astype(np.float32)
c_host = np.empty_like(a_host) # To store results from GPU

print(f"[INFO] Host data (arrays a, b) created with {ARRAY_SIZE} elements.")

# --- 6. Create Device Buffers ---
# cl.mem_flags.READ_ONLY: Data will only be read by the kernel
# cl.mem_flags.WRITE_ONLY: Data will only be written by the kernel
# cl.mem_flags.COPY_HOST_PTR: Initialize device buffer with host data

a_dev = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=a_host)
b_dev = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=b_host)
c_dev = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, c_host.nbytes)

print("[INFO] Device buffers created.")

# --- 7. Execute Kernel ---
# global_size: Total number of work-items to execute the kernel
# local_size: Number of work-items in a work-group (optional, can be None)

# Enqueue the kernel for execution
# The 'vec_add' function from the kernel_code will be called
# for each global_id from 0 to ARRAY_SIZE-1

print("[INFO] Executing kernel on device...")
program.vec_add(queue, a_host.shape, None, a_dev, b_dev, c_dev)

# --- 8. Transfer Results Back to Host ---
cl.enqueue_copy(queue, c_host, c_dev).wait()
print("[INFO] Results transferred back to host.")

# --- 9. Verify Results ---
# Compare GPU result with CPU result
c_cpu = a_host + b_host

if np.allclose(c_host, c_cpu):
    print("\n[SUCCESS] GPU computation matches CPU computation!")
    print(f"First 5 GPU results: {c_host[:5]}")
    print(f"First 5 CPU results: {c_cpu[:5]}")
else:
    print("\n[FAILURE] GPU computation does NOT match CPU computation.")
    print(f"First 5 GPU results: {c_host[:5]}")
    print(f"First 5 CPU results: {c_cpu[:5]}")

print("\n[INFO] PyOpenCL script finished.")
