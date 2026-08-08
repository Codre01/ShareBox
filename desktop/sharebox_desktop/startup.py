"""Re-export the platform launch-at-startup helper for the desktop shell."""

from sharebox.app.startup import set_launch_at_startup, supports_launch_at_startup

__all__ = ["set_launch_at_startup", "supports_launch_at_startup"]
