import gc as _gc
import inspect
import logging
import types as _types
import typing

logger = logging.getLogger(__name__)


def proxy0(data):
    def proxy1():
        return data

    return proxy1


_CELLTYPE = type(proxy0(None).__closure__[0])


def replace_all_refs(replace_from: typing.Any, replace_to: typing.Any) -> typing.Any:
    """
    :summary: Uses the :mod:`gc` module to replace all references to obj
              :attr:`replace_from` with :attr:`replace_to` (it tries it's best,
              anyway).
    :param replace_from: The obj you want to replace.
    :param replace_to: The new objject you want in place of the old one.
    :returns: The replace_from
    """
    # https://github.com/cart0113/pyjack/blob/dd1f9b70b71f48335d72f53ee0264cf70dbf4e28/pyjack.py

    _gc.collect()

    hit = False
    for referrer in _gc.get_referrers(replace_from):
        # FRAMES -- PASS THEM UP
        if isinstance(referrer, _types.FrameType):
            continue

        # DICTS
        if isinstance(referrer, dict):
            cls = None

            # THIS CODE HERE IS TO DEAL WITH DICTPROXY TYPES
            if "__dict__" in referrer and "__weakref__" in referrer:
                for cls in _gc.get_referrers(referrer):
                    if inspect.isclass(cls) and cls.__dict__ == referrer:
                        break

            for key, value in referrer.items():
                # REMEMBER TO REPLACE VALUES ...
                if value is replace_from:
                    hit = True
                    value = replace_to
                    referrer[key] = value
                    if cls:  # AGAIN, CLEANUP DICTPROXY PROBLEM
                        setattr(cls, key, replace_to)
                # AND KEYS.
                if key is replace_from:
                    hit = True
                    del referrer[key]
                    referrer[replace_to] = value

        elif isinstance(referrer, list):
            for i, value in enumerate(referrer):
                if value is replace_from:
                    hit = True
                    referrer[i] = replace_to

        elif isinstance(referrer, set):
            referrer.remove(replace_from)
            referrer.add(replace_to)
            hit = True

        elif isinstance(
            referrer,
            (
                tuple,
                frozenset,
            ),
        ):
            new_tuple = []
            for obj in referrer:
                if obj is replace_from:
                    new_tuple.append(replace_to)
                else:
                    new_tuple.append(obj)
            replace_all_refs(referrer, type(referrer)(new_tuple))

        elif isinstance(referrer, _CELLTYPE):

            def _proxy0(data):
                def proxy1():
                    return data

                return proxy1

            proxy = _proxy0(replace_to)
            newcell = proxy.__closure__[0]
            replace_all_refs(referrer, newcell)

        elif isinstance(referrer, _types.FunctionType):
            localsmap = {}
            for key in ["code", "globals", "name", "defaults", "closure"]:
                orgattr = getattr(referrer, f"__{key}__")
                localsmap[key] = replace_to if orgattr is replace_from else orgattr
            localsmap["argdefs"] = localsmap["defaults"]
            del localsmap["defaults"]
            newfn = _types.FunctionType(**localsmap)
            replace_all_refs(referrer, newfn)

        else:
            logger.debug("%s is not supported.", referrer)

    if hit is False:
        raise AttributeError(f"Object '{replace_from}' not found")

    return replace_from
