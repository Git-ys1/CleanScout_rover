import numpy as np
import torch


def dfl_torch(position):
    x = torch.tensor(position)
    n, c, h, w = x.shape
    p_num = 4
    mc = c // p_num
    y = x.reshape(n, p_num, mc, h, w)
    y = y.softmax(2)
    acc_matrix = torch.arange(mc, dtype=torch.float32).reshape(
        1, 1, mc, 1, 1
    )
    return (y * acc_matrix).sum(2).numpy()


def dfl_numpy(position):
    n, c, h, w = position.shape
    p_num = 4
    mc = c // p_num
    y = position.reshape(n, p_num, mc, h, w)
    y = y - np.max(y, axis=2, keepdims=True)
    y = np.exp(y)
    y = y / np.sum(y, axis=2, keepdims=True)
    acc_matrix = np.arange(mc, dtype=np.float32).reshape(
        1, 1, mc, 1, 1
    )
    return (y * acc_matrix).sum(axis=2)


np.random.seed(0)
input_data = np.random.randn(1, 64, 80, 80).astype(np.float32)
torch_output = dfl_torch(input_data)
numpy_output = dfl_numpy(input_data)

print("max_abs_error:", np.max(np.abs(torch_output - numpy_output)))
print("mean_abs_error:", np.mean(np.abs(torch_output - numpy_output)))
