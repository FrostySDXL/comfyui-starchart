# Example 6: V1 STRING Reference

**Status:** Pattern example
**Level:** Beginner -- focused V1 reference example

## What This Example Is

This directory contains a deliberately small V1 custom node that uses one
`STRING` input and two `STRING` outputs.

It proves four things only:

- the copy-safe V1 `@classmethod def INPUT_TYPES(cls)` shape
- module-level `NODE_CLASS_MAPPINGS` registration
- tuple returns for multiple outputs
- `STRING` values arriving in Python as normal `str` objects

## Files

- `string_echo_reference.py` -- minimal V1 node with explicit `STRING` usage

## What This Example Does Not Cover

- frontend JavaScript
- tensor datatypes such as `IMAGE` or `LATENT`
- packaging for ComfyUI-Manager
- runtime messaging or advanced hidden inputs

Use this example when you want the smallest repo-local V1 reference before you
move to the official walkthrough example in `minimal-node-template/`.
