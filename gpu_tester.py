
import pyopencl as cl
import numpy as np

def test_gpu():
    """
    Tests the GPU by performing a simple computation using PyOpenCL.
    """
    # Create a context and command queue
    try:
        platforms = cl.get_platforms()
        if not platforms:
            print("No OpenCL platforms found. Check OpenCL installation.")
            return

        devices = platforms[0].get_devices(device_type=cl.device_type.GPU)
        if not devices:
            print("No GPU devices found.")
            return

        context = cl.Context(devices)
        queue = cl.CommandQueue(context)

    except cl.Error as e:
        print(f"Error setting up PyOpenCL context: {e}")
        print("Please ensure OpenCL drivers are installed for your GPU.")
        return

    # Create some data
    a = np.random.rand(50000).astype(np.float32)
    b = np.random.rand(50000).astype(np.float32)

    # Create memory buffers on the device
    mf = cl.mem_flags
    a_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
    b_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b)
    dest_buf = cl.Buffer(context, mf.WRITE_ONLY, b.nbytes)

    # Create a program from the kernel source
    program = cl.Program(context, """
    __kernel void multiply(__global const float *a,
    __global const float *b, __global float *c)
    {
      int gid = get_global_id(0);
      c[gid] = a[gid] * b[gid];
    }
    """).build()

    # Execute the kernel
    program.multiply(queue, a.shape, None, a_buf, b_buf, dest_buf)

    # Create a buffer to store the result
    c = np.empty_like(a)
    cl.enqueue_copy(queue, c, dest_buf)

    # Check the result
    if np.allclose(c, a * b):
        print("GPU test successful!")
    else:
        print("GPU test failed!")

if __name__ == '__main__':
    test_gpu()
