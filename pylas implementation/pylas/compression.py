""" The functions related to the LAZ format (compressed LAS)
"""
import enum
import os
from typing import Tuple


class LazBackend(enum.Enum):
    """Supported backends for reading and writing LAS/LAZ"""

    # type_hint = Union[LazBackend, Iterable[LazBackend]]

    LazrsParallel = 0
    Lazrs = 1
    Laszip = 2  # laszip executable, used through a Popen

    def is_available(self) -> bool:
        """Returns true if the backend is available"""
        if self == LazBackend.Lazrs or self == LazBackend.LazrsParallel:
            try:
                import lazrs
            except ModuleNotFoundError:
                return False
            else:
                return True
        elif self == LazBackend.Laszip:
            try:
                find_laszip_executable()
            except FileNotFoundError:
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def detect_available() -> Tuple["LazBackend"]:
        """Returns a tuple containing the available backends in the current
        python environment
        """
        available_backends = []

        if LazBackend.LazrsParallel.is_available():
            available_backends.append(LazBackend.LazrsParallel)
            available_backends.append(LazBackend.Lazrs)

        if LazBackend.Laszip.is_available():
            available_backends.append(LazBackend.Laszip)

        return tuple(available_backends)


def is_point_format_compressed(point_format_id: int) -> bool:
    compression_bit_7 = (point_format_id & 0x80) >> 7
    compression_bit_6 = (point_format_id & 0x40) >> 6
    if not compression_bit_6 and compression_bit_7:
        return True
    return False


def compressed_id_to_uncompressed(point_format_id: int) -> int:
    return point_format_id & 0x3F


def uncompressed_id_to_compressed(point_format_id: int) -> int:
    return (2 ** 7) | point_format_id


def find_laszip_executable() -> str:
    laszip_names = ("laszip", "laszip.exe", "laszip-cli", "laszip-cli.exe")

    for binary in laszip_names:
        in_path = (
            os.path.isfile(os.path.join(x, binary))
            for x in os.environ["PATH"].split(os.pathsep)
        )
        if any(in_path):
            return binary
    raise FileNotFoundError("Could not find laszip executable")
