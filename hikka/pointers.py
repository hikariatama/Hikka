# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import typing


class PointerList(list):
    """Pointer to list saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore  # noqa: F821
        module: str,
        key: str,
        default: typing.Optional[typing.Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        super().__init__(db.get(module, key, default))

    @property
    def data(self) -> list:
        return list(self)

    @data.setter
    def data(self, value: list):
        self.clear()
        self.extend(value)
        self._save()

    def __repr__(self):
        return f"PointerList({list(self)})"

    def __str__(self):
        return f"PointerList({list(self)})"

    def __delitem__(self, __i: typing.Union[typing.SupportsIndex, slice]) -> None:
        a = super().__delitem__(__i)
        self._save()
        return a

    def __setitem__(
        self,
        __i: typing.Union[typing.SupportsIndex, slice],
        __v: typing.Any,
    ) -> None:
        a = super().__setitem__(__i, __v)
        self._save()
        return a

    def __iadd__(self, __x: typing.Iterable) -> "Self":  # type: ignore  # noqa: F821
        a = super().__iadd__(__x)
        self._save()
        return a

    def __imul__(self, __x: int) -> "Self":  # type: ignore  # noqa: F821
        a = super().__imul__(__x)
        self._save()
        return a

    def append(self, value: typing.Any):
        super().append(value)
        self._save()

    def extend(self, value: typing.Iterable):
        super().extend(value)
        self._save()

    def insert(self, index: int, value: typing.Any):
        super().insert(index, value)
        self._save()

    def remove(self, value: typing.Any):
        super().remove(value)
        self._save()

    def pop(self, index: int = -1) -> typing.Any:
        a = super().pop(index)
        self._save()
        return a

    def clear(self) -> None:
        super().clear()
        self._save()

    def _save(self):
        self._db.set(self._module, self._key, list(self))

    def tolist(self):
        return self._db.get(self._module, self._key, self._default)


class PointerDict(dict):
    """Pointer to dict saved in database"""

    def __init__(
        self,
        db: "Database",  # type: ignore  # noqa: F821
        module: str,
        key: str,
        default: typing.Optional[typing.Any] = None,
    ):
        self._db = db
        self._module = module
        self._key = key
        self._default = default
        super().__init__(db.get(module, key, default))

    @property
    def data(self) -> dict:
        return dict(self)

    @data.setter
    def data(self, value: dict):
        self.clear()
        self.update(value)
        self._save()

    def __repr__(self):
        return f"PointerDict({dict(self)})"

    def __bool__(self) -> bool:
        return bool(self._db.get(self._module, self._key, self._default))

    def __setitem__(self, key: str, value: typing.Any):
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

    def setdefault(self, key: str, default: typing.Any = None) -> typing.Any:
        a = super().setdefault(key, default)
        self._save()
        return a

    def pop(self, key: str, default: typing.Any = None) -> typing.Any:
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

    def todict(self):
        return self._db.get(self._module, self._key, self._default)


class BaseSerializingMiddlewareDict:
    def __init__(self, pointer: PointerDict):
        self._pointer = pointer

    def serialize(self, item: typing.Any) -> "JSONSerializable":  # type: ignore  # noqa: F821
        raise NotImplementedError

    def deserialize(self, item: "JSONSerializable") -> typing.Any:  # type: ignore  # noqa: F821
        raise NotImplementedError

    def __getitem__(self, key: typing.Any) -> typing.Any:
        return self.deserialize(self._pointer[key])

    def __setitem__(self, key: typing.Any, value: typing.Any) -> None:
        self._pointer[key] = self.serialize(value)

    def __delitem__(self, key: typing.Any) -> None:
        del self._pointer[key]

    def __iter__(self) -> typing.Iterator[typing.Any]:
        for key, value in self._pointer.items():
            yield (key, self.deserialize(value))

    def __len__(self) -> int:
        return len(self._pointer)

    def __contains__(self, item: typing.Any) -> bool:
        return item in self._pointer

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._pointer})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._pointer})"

    def pop(self, key: typing.Any) -> typing.Any:
        return self.deserialize(self._pointer.pop(key))

    def popitem(self) -> typing.Any:
        return self.deserialize(self._pointer.popitem())

    def get(self, key: typing.Any, default: typing.Any = None) -> typing.Any:
        return self.deserialize(self._pointer[key]) if key in self._pointer else default

    def setdefault(self, key: typing.Any, default: typing.Any = None) -> typing.Any:
        return self.deserialize(self._pointer.setdefault(key, self.serialize(default)))

    def clear(self) -> None:
        self._pointer.clear()

    def todict(self) -> dict:
        return {
            key: self.deserialize(value) for key, value in self._pointer.data.items()
        }

    def keys(self) -> typing.KeysView:
        return self._pointer.keys()

    def values(self) -> typing.Iterable[typing.Any]:
        return (self.deserialize(value) for value in self._pointer.values())


class BaseSerializingMiddlewareList:
    def __init__(self, pointer: PointerList):
        self._pointer = pointer

    def serialize(self, item: typing.Any) -> "JSONSerializable":  # type: ignore  # noqa: F821
        raise NotImplementedError

    def deserialize(self, item: "JSONSerializable") -> typing.Any:  # type: ignore  # noqa: F821
        raise NotImplementedError

    def remove(self, item: typing.Any) -> None:
        self._pointer.remove(self.serialize(item))

    def pop(self, index: int) -> typing.Any:
        return self.deserialize(self._pointer.pop(index))

    def insert(self, index: int, item: typing.Any) -> None:
        self._pointer.insert(index, self.serialize(item))

    def append(self, item: typing.Any) -> None:
        self._pointer.append(self.serialize(item))

    def extend(self, items: typing.Iterable[typing.Any]) -> None:
        self._pointer.extend([self.serialize(item) for item in items])

    def __getitem__(self, key: typing.Any) -> typing.Any:
        return self.deserialize(self._pointer[key])

    def __setitem__(self, key: typing.Any, value: typing.Any) -> None:
        self._pointer[key] = self.serialize(value)

    def __delitem__(self, key: typing.Any) -> None:
        del self._pointer[key]

    def __iter__(self) -> typing.Iterator[typing.Any]:
        return (self.deserialize(item) for item in self._pointer)

    def __len__(self) -> int:
        return len(self._pointer)

    def __contains__(self, item: typing.Any) -> bool:
        return self.serialize(item) in self._pointer

    def __reversed__(self) -> typing.Iterator[typing.Any]:
        return (self.deserialize(item) for item in reversed(self._pointer))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._pointer})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._pointer})"

    def tolist(self) -> list:
        return [self.deserialize(item) for item in self._pointer.data]


class NamedTupleMiddlewareList(BaseSerializingMiddlewareList):
    def __init__(self, pointer: PointerList, item_type: typing.Type[typing.Any]):
        super().__init__(pointer)
        self._item_type = item_type

    def serialize(self, item: typing.Any) -> "JSONSerializable":  # type: ignore  # noqa: F821
        return item._asdict()

    def deserialize(self, item: "JSONSerializable") -> typing.Any:  # type: ignore  # noqa: F821
        return self._item_type(**item)


class NamedTupleMiddlewareDict(BaseSerializingMiddlewareDict):
    def __init__(self, pointer: PointerList, item_type: typing.Type[typing.Any]):
        super().__init__(pointer)
        self._item_type = item_type

    def serialize(self, item: typing.Any) -> "JSONSerializable":  # type: ignore  # noqa: F821
        return item._asdict()

    def deserialize(self, item: "JSONSerializable") -> typing.Any:  # type: ignore  # noqa: F821
        return self._item_type(**item)
