"""disable.py -- lifecycle script for the example-5 package.

Runs when the package is disabled. Manager appends .disabled to the folder
name when disabling, which causes ComfyUI to skip the package on load.

This is an EXAMPLE implementation. Replace the body of disable() with your
actual cleanup logic.

Manager will call this script with: python disable.py
"""


def disable():
    """
    Called by ComfyUI-Manager when the package is disabled.

    Typical tasks:
    - Save state that should persist across disable/enable cycles
    - Release resources

    This example is a no-op placeholder. Add your cleanup logic here.
    """
    pass


if __name__ == "__main__":
    disable()
