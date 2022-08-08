import asyncio
from typing import Any, Iterable, Optional, SupportsIndex, Union
from typing_extensions import Self


class PointerInt(int):
    """Pointer to integer saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        self.value = db.get(module, key, default)

    def set(self, value: Any):
        self._db.set(self._module, self._key, value)
        self.value = value


class PointerList(list):
    """Pointer to list saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        self.set(db.get(module, key, default))

    def __delitem__(self, __i: Union[SupportsIndex, slice]) -> None:
        a = super().__delitem__(__i)
        self._save()
        return a

    def __setitem__(self, __i: Union[SupportsIndex, slice], __v: Any) -> None:
        a = super().__setitem__(__i, __v)
        self._save()
        return a

    def __iadd__(self, __x: Iterable) -> Self:
        a = super().__iadd__(__x)
        self._save()
        return a

    def __imul__(self, __x: int) -> Self:
        a = super().__imul__(__x)
        self._save()
        return a

    def __str__(self):
        return f"PointerList({list(self)})"

    def append(self, value: Any):
        super().append(value)
        self._save()

    def extend(self, value: Iterable):
        super().extend(value)
        self._save()

    def insert(self, index: int, value: Any):
        super().insert(index, value)
        self._save()

    def remove(self, value: Any):
        super().remove(value)
        self._save()

    def pop(self, index: int = -1) -> Any:
        a = super().pop(index)
        self._save()
        return a

    def clear(self) -> None:
        super().clear()
        self._save()

    def _save(self):
        self._db.set(self._module, self._key, list(self))

    def set(self, value: Any):
        if not isinstance(value, list):
            raise TypeError(
                f"Attempted to assign value {value}, which is not a list to pointer"
            )

        self.clear()
        self.extend(value)
        self._save()


class PointerTuple(tuple):
    """Pointer to tuple saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        self.set(db.get(module, key, default))

    def set(self, value: Any):
        if not isinstance(value, tuple):
            raise TypeError(
                f"Attempted to assign value {value}, which is not a tuple to pointer"
            )

        self.clear()
        self.extend(value)
        self._save()


class PointerDict(dict):
    """Pointer to dict saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        self.set(db.get(module, key, default))

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, value)
        self._save()

    def __delitem__(self, key: str):
        super().__delitem__(key)
        self._save()

    def __str__(self):
        return f"PointerDict({dict(self)})"

    def update(self, __m: dict) -> None:
        super().update(__m)
        self._save()

    def setdefault(self, key: str, default: Any) -> Any:
        if key not in self:
            self[key] = default
            self._save()
        return self[key]

    def pop(self, key: str, default: Any = None) -> Any:
        a = super().pop(key, default)
        self._save()
        return a

    def popitem(self) -> tuple:
        a = super().popitem()
        self._save()
        return a

    def clear(self) -> None:
        super().clear()
        self._save()

    def _save(self):
        self._db.set(self._module, self._key, dict(self))

    def set(self, value: Any):
        if not isinstance(value, dict):
            raise TypeError(
                f"Attempted to assign value {value}, which is not a dict to pointer"
            )

        self.clear()
        self.update(value)
        self._save()


class PointerStr(str):
    """Pointer to string saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        self.value = db.get(module, key, default)

    def set(self, value: Any):
        self.replace(self.center(0), value)
        self._db.set(self._module, self._key, value)


class PointerBool(PointerInt):
    def __init__(
        self,
        db: "Database",  # type: ignore
        module: str,
        key: str,
        default: Optional[Any] = None,
    ):
        super().__init__(db, module, key, default)
