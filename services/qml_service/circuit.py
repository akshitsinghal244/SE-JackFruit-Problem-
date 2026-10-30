"""Variational Quantum Classifier (VQC) built with PennyLane, trained through PyTorch.

Circuit for n qubits (simulated on PennyLane's default.qubit):

    |0> -RY(x0)-+                          +- <Z0> --+
    |0> -RY(x1)-|  StronglyEntangling      |- <Z1> --|--> 3 numbers in [-1, 1]
    |0> -RY(x2)-|  layers: trainable       |- <Z2> --+
    |0> -RY(x3)-+  rotations + CNOT ring   +
       encoding        "the model"           read-out

Class read-out (a design choice -> record it in the SADS):
    logits_c = scale_c * <Z_c> + bias_c      for c = Low, Medium, High (qubits 0, 1, 2)
    probabilities = softmax(logits)
<Z> is in [-1, 1], so without a trainable scale the softmax could never be confident
(the best it could do is e^1 vs e^-1 ~ 0.78 vs 0.11). scale and bias are 6 classical
parameters; all the feature mixing happens in the quantum layers.
"""
from __future__ import annotations

import pennylane as qml
import torch
from torch import nn


def make_qlayer(n_qubits: int, n_layers: int) -> qml.qnn.TorchLayer:
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev, interface="torch", diff_method="backprop")
    def circuit(inputs, weights):            # the first argument MUST be named `inputs`
        qml.AngleEmbedding(inputs, wires=range(n_qubits), rotation="Y")
        qml.StronglyEntanglingLayers(weights, wires=range(n_qubits))
        return [qml.expval(qml.PauliZ(w)) for w in range(3)]

    shapes = {"weights": qml.StronglyEntanglingLayers.shape(n_layers=n_layers, n_wires=n_qubits)}
    return qml.qnn.TorchLayer(circuit, shapes)


class HybridVQC(nn.Module):
    def __init__(self, n_qubits: int = 4, n_layers: int = 3):
        super().__init__()
        self.n_qubits, self.n_layers = n_qubits, n_layers
        self.qlayer = make_qlayer(n_qubits, n_layers)
        self.scale = nn.Parameter(torch.full((3,), 2.0))
        self.bias = nn.Parameter(torch.zeros(3))

    def forward(self, angles: torch.Tensor) -> torch.Tensor:
        z = self.qlayer(angles).to(torch.float32)   # [B, 3] expectation values
        return self.scale * z + self.bias           # logits
