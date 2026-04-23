"""install.py -- lifecycle script for the example-5 package.

Runs after the package is first cloned into custom_nodes/. This example is
intentionally zero-dependency, so install() is a documented no-op.

Manager will call this script with: python install.py
"""


def install():
    """
    Called by ComfyUI-Manager after the package is first cloned.

    Typical tasks for a real package:
    - Install Python dependencies from requirements.txt
    - Download external assets or model files
    - Run one-time setup

    This example does none of those things because the demo nodes use only the
    Python standard library.
    """
    return None


if __name__ == "__main__":
    install()
