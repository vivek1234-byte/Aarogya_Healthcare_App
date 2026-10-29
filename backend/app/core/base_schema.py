from typing import Any, Dict

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    class FieldFallback:
        def __init__(self, default=None, default_factory=None, **kwargs):
            self.default = default
            self.default_factory = default_factory

    Field = FieldFallback

    class BaseModel:
        def __init__(self, **kwargs):
            # Assign values based on class annotations and kwargs
            annotations = getattr(self.__class__, "__annotations__", {})
            for key, val_type in annotations.items():
                default_val = getattr(self.__class__, key, None)
                if isinstance(default_val, FieldFallback):
                    if default_val.default_factory:
                        default_val = default_val.default_factory()
                    else:
                        default_val = default_val.default
                setattr(self, key, kwargs.get(key, default_val))

            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        def dict(self) -> Dict[str, Any]:
            return self.model_dump()

        @classmethod
        def model_validate(cls, obj: Any):
            if isinstance(obj, dict):
                return cls(**obj)
            res = cls()
            for k, v in getattr(obj, "__dict__", {}).items():
                if not k.startswith("_"):
                    setattr(res, k, v)
            return res
