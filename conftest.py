"""Top-level pytest collection controls for legacy demo scripts."""

# These files are runnable demo/test scripts for the agent prototype rather than
# maintained pytest modules. Keep them out of the default pytest collection so
# `pytest` reflects the supported automated suite under `tests/`.
collect_ignore = [
    "test_phase1.py",
    "test_phase2.py",
    "test_phase2_integration.py",
    "test_phase3_ui.py",
    "test_verizon_css.py",
]
