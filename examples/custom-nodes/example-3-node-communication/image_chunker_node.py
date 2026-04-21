"""V1 node demonstrating batch processing and multi-output patterns.

Splits a batch of images into individual frames, processes each,
and outputs: processed batch, batch mask, and a summary string.
"""

import torch
from server import PromptServer


class ImageChunkerNode:
    CATEGORY = "example/chunker"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("processed_images", "batch_mask", "summary")
    FUNCTION = "chunk_and_process"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "operation": (["passthrough", "grayscale", "edge_detect"],),
            },
            "optional": {
                "threshold": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                }),
            }
        }

    def chunk_and_process(self, images, operation="passthrough", threshold=0.5):
        batch_size = images.shape[0]
        processed_frames = []
        max_intensity_per_pixel = None

        for i in range(batch_size):
            single_frame = images[i].unsqueeze(0)

            # Apply operation
            if operation == "passthrough":
                processed = single_frame
            elif operation == "grayscale":
                # Luminance weights: ITU-R BT.709
                r, g, b = single_frame[:, :, :, 0], single_frame[:, :, :, 1], single_frame[:, :, :, 2]
                gray = 0.2126 * r + 0.7152 * g + 0.0722 * b
                processed = gray.unsqueeze(-1).expand_as(single_frame)
            elif operation == "edge_detect":
                # Simple Sobel-like gradient magnitude
                dx = single_frame[:, :, 1:, :] - single_frame[:, :, :-1, :]
                dy = single_frame[:, 1:, :, :] - single_frame[:, :-1, :, :]
                grad_mag = torch.sqrt(dx[:, :, :-1, :] ** 2 + dy[:, :-1, :, :] ** 2 + 1e-8)
                processed = grad_mag

            processed_frames.append(processed.squeeze(0))

            # Track max intensity across batch for mask
            frame_abs = torch.abs(processed)
            if max_intensity_per_pixel is None:
                max_intensity_per_pixel = frame_abs
            else:
                max_intensity_per_pixel = torch.maximum(max_intensity_per_pixel, frame_abs)

            # Emit progress event
            PromptServer.instance.send_sync(
                "example.chunker.progress",
                {
                    "index": i + 1,
                    "total": batch_size,
                    "operation": operation,
                },
            )

        # Stack all processed frames back into a batch
        processed_batch = torch.stack(processed_frames, dim=0)

        # Normalize max intensity to [0, 1] for mask
        batch_mask = max_intensity_per_pixel
        if batch_mask.max() > 1e-8:
            batch_mask = batch_mask / batch_mask.max()
        batch_mask = (batch_mask > threshold).float()

        # Summary string for logging
        summary = f"{operation}: {batch_size} frames, threshold={threshold:.2f}"

        return (processed_batch, batch_mask, summary)


NODE_CLASS_MAPPINGS = {
    "Image Chunker": ImageChunkerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Image Chunker": "Image Chunker / Processor",
}
