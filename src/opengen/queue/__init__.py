"""
OpenGen Queue Subsystem.
"""
from opengen.queue.worker import huey, init_queue

__all__ = ["huey", "init_queue"]
