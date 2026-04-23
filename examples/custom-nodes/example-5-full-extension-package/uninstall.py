"""uninstall.py -- lifecycle script for the example-5 package.

Runs before the package is removed. This is an EXAMPLE implementation.
For production packages, add cleanup logic that is safe to run as a
pre-removal step.

Manager will call this script with: python uninstall.py

WARNING: uninstall.py is NOT guaranteed to run. Users may delete the
directory manually, or Manager may remove the directory without invoking
the script. Do not put critical cleanup logic here as the only path.
"""


def uninstall():
    """
    Called by ComfyUI-Manager before the package directory is removed.

    Typical tasks:
    - Remove downloaded assets or cache files created by the package
    - Uninstall package-specific pip packages (use with caution)

    This example is a no-op placeholder. Add your cleanup logic here.
    """
    pass


if __name__ == "__main__":
    uninstall()
