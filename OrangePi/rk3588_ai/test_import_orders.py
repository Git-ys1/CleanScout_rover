import subprocess
import sys
import textwrap


TESTS = {
    "torch_only": """
        import torch
        print("torch OK", torch.__version__)
    """,
    "torch_cv2_rknn": """
        import torch
        print("torch OK", torch.__version__)
        import cv2
        print("cv2 OK", cv2.__version__)
        from rknnlite.api import RKNNLite
        print("rknnlite OK")
    """,
    "cv2_torch_rknn": """
        import cv2
        print("cv2 OK", cv2.__version__)
        import torch
        print("torch OK", torch.__version__)
        from rknnlite.api import RKNNLite
        print("rknnlite OK")
    """,
    "rknn_cv2_torch": """
        from rknnlite.api import RKNNLite
        print("rknnlite OK")
        import cv2
        print("cv2 OK", cv2.__version__)
        import torch
        print("torch OK", torch.__version__)
    """,
    "numpy_cv2_rknn_torch": """
        import numpy
        print("numpy OK", numpy.__version__)
        import cv2
        print("cv2 OK", cv2.__version__)
        from rknnlite.api import RKNNLite
        print("rknnlite OK")
        import torch
        print("torch OK", torch.__version__)
    """,
}


for name, code in TESTS.items():
    print("\n==========", name, "==========")
    process = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        text=True,
        capture_output=True,
    )
    print("returncode:", process.returncode)
    print("stdout:\n", process.stdout)
    print("stderr:\n", process.stderr)
