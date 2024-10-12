from threading import Lock


# Inherits from `type`, making it a metaclass.
class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}
    _lock: Lock = Lock()

    # The `__call__` method is invoked when you try to create an instance of a class (`cls()`)
    # (Here we are overriding that method.)
    def __call__(cls, *args, **kwargs):
        # Double-checked locking to ensure thread safety
        if cls not in cls._instances:
            with cls._lock:
                # After acquiring the lock, checks again to prevent race conditions
                # where multiple threads might have passed the first check simultaneously.
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
