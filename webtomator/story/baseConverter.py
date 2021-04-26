# baseConverter.py
# file deepcode ignore R0123: <Comparison to literal typeA/typeB intentionally done here>

from abc import abstractmethod
from inspect import isclass
from typing import Tuple, TypeVar

import debug.logger as clog

logger = clog.getLogger(__name__)


class BaseConverter:
    """
    Base class for all data converters within this module which convert one
    type to an other type.
    """

    def __init__(self, source, target, allowedTypes: Tuple[TypeVar, TypeVar]):
        """ Base class for every dao converter in this app.
        We do invasive type checking here because of the generic behaviour of this class.

        :param source: Must be a data instance which has to be converted to target.
        :param target: Must be a type type of the target class of the conversion.
        :param allowedTypes: Types of allowed source/target objects. Order does NOT matter here.
        """

        # Type check. Order is important here.

        typeA = allowedTypes[0]
        typeB = allowedTypes[1]

        # 1.
        if source is None or target is None:
            raise ValueError("Violating converter rule: Source or target is of type None.")

        # 2.
        # Take possible generics and typing package into account. Here we try to
        # 'upcast' generic types to the python "origin" type, because generic types do not
        # work on instance checks and class checks.
        typeA_instanceCheck = getattr(typeA, "__origin__", typeA)
        typeB_instanceCheck = getattr(typeB, "__origin__", typeB)
        target_instanceCheck = getattr(target, "__origin__", target)

        if not isinstance(source, (typeA_instanceCheck, typeB_instanceCheck)):
            raise TypeError(
                f"Violating converter rule: Source must be an instance of {typeA_instanceCheck} "
                f"or {typeB_instanceCheck}. Source is: {source}"
            )

        if (type(target_instanceCheck) is not type) and (not isclass(target_instanceCheck)):
            raise TypeError(
                f"Violating converter rule: Target {target} must be a type. Target is {target}")

        if target != typeA and target != typeB:
            raise TypeError(
                f"Violating converter rule: Target type must be {typeA} or {typeB}. "
                f"Target is: {target}"
            )

        self._source = source
        self._target = target

    @abstractmethod
    def getConverted(self):
        """
        Returns an instance (target) with converted data from source.
        No type hints for return type here, just because we don't know the type of
        _target. Therefore type checking is heavily done when initializing the class.
        """
        pass
