"""Local stub package for tests that patch ``snowflake.connector``.

This repo does not require the real Snowflake connector for metadata-runtime
unit tests. The stub exists so patch targets can be resolved when the optional
dependency is not installed.
"""

