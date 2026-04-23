"""enable.py -- lifecycle script for the example-5 package.

Runs when the package is re-enabled after being disabled. Manager appends
.disabled to the folder name when disabling, and removes it when re-enabling.

This is an EXAMPLE implementation. Replace the body of enable() with your
actual restore logic.

Manager will call this script with: python enable.py
"""


def enable():
    """
    Called by ComfyUI-Manager when the package is re-enabled.

    Typical tasks:
    - Restore state saved during disable
    - Re-register resources

    This example is a no-op placeholder. Add your restore logic here.
    """
    pass


if __name__ == "__main__":
    enable()
