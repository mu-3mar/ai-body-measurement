"""Command-line entry point for the backend."""

from __future__ import annotations

import uvicorn

from ai_body_measurement.config import HOST, PORT


def main() -> None:
    uvicorn.run("ai_body_measurement.api:app", host=HOST, port=PORT)


if __name__ == "__main__":
    main()
