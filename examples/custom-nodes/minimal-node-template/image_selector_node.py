"""Official walkthrough example adapted into a repo-local reference file.

Primary source: https://docs.comfy.org/custom-nodes/walkthrough
"""

import torch
from server import PromptServer


class ImageSelector:
    CATEGORY = "example"
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "choose_image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["brightest", "reddest", "greenest", "bluest"],),
            }
        }

    def choose_image(self, images, mode):
        batch_size = images.shape[0]
        brightness = [torch.mean(image.flatten()).item() for image in images]
        if mode == "brightest":
            scores = brightness
        else:
            channel = 0 if mode == "reddest" else (1 if mode == "greenest" else 2)
            absolute = [torch.mean(image[:, :, channel].flatten()).item() for image in images]
            scores = [absolute[i] / (brightness[i] + 1e-8) for i in range(batch_size)]

        best = scores.index(max(scores))
        result = images[best].unsqueeze(0)
        PromptServer.instance.send_sync(
            "example.imageselector.textmessage",
            {"message": f"Picked image {best + 1}"},
        )
        return (result,)


NODE_CLASS_MAPPINGS = {
    "Image Selector": ImageSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Image Selector": "Image Selector",
}

WEB_DIRECTORY = "./web/js"
