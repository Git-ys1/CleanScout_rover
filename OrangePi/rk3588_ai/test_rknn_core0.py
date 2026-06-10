import os
import sys
import time

import numpy as np
from rknnlite.api import RKNNLite


model_path = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "models/lxmyzzs/yolo11n.rknn"
)

if not os.path.exists(model_path):
    print("model does not exist:", model_path)
    sys.exit(1)

rknn = RKNNLite()

print("[1] load_rknn:", model_path)
ret = rknn.load_rknn(model_path)
print("load_rknn ret =", ret)
if ret != 0:
    sys.exit(1)

print("[2] init_runtime: NPU_CORE_0")
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0)
print("init_runtime ret =", ret)
if ret != 0:
    rknn.release()
    sys.exit(1)

print("[3] inference")
image = np.zeros((1, 640, 640, 3), dtype=np.uint8)

start = time.time()
outputs = rknn.inference(inputs=[image], data_format=["nhwc"])
elapsed_ms = (time.time() - start) * 1000

if outputs is None:
    print("inference failed: RKNNLite returned None")
    rknn.release()
    sys.exit(1)

print("inference OK")
print("time_ms =", elapsed_ms)
print("outputs num =", len(outputs))
for index, output in enumerate(outputs):
    print(
        "output",
        index,
        "shape =",
        output.shape,
        "dtype =",
        output.dtype,
    )

rknn.release()
print("[DONE]")
