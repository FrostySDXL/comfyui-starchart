from typing import TypedDict


class torch:
    class Tensor:
        pass


ImageInput = torch.Tensor
"""
An image in format [B, H, W, C]
"""


class AudioInput(TypedDict):
    """
    TypedDict representing audio input.
    """

    waveform: torch.Tensor
    """
    Tensor in format [B, C, T].
    """

    sample_rate: int
