import io
import cv2
import base64
import numpy as np


def bytesio_to_base64(bytes_io: io.BytesIO) -> str:
    """
    Converts an io.BytesIO object to a base64 string.

    Args:
        bytes_io (io.BytesIO): The BytesIO object to convert.

    Returns:
        str: The base64 encoded string representation of the BytesIO object.
    """
    bytes_io.seek(0)
    base64_str = base64.b64encode(bytes_io.read()).decode('utf-8')
    return base64_str


def encode_image_as_buffer(img: np.ndarray, ext=".jpg") -> io.BytesIO | None:
    """
    Encodes an image into a binary buffer.

    Args:
        img (np.ndarray): The image to encode.
        ext (str, optional): The file extension/format to use for encoding. Defaults to ".jpg".

    Returns:
        io.BytesIO | None: A BytesIO object containing the encoded image, or None if encoding fails.
    """
    success, buffer = cv2.imencode(ext, img)
    if success:
        return io.BytesIO(buffer.tobytes())
    return None


def image_to_base64(img: np.ndarray, ext=".jpg") -> str | None:
    """
    Converts an image to a base64 string.

    Args:
        img (np.ndarray): The image to convert.
        ext (str, optional): The file extension/format to use for encoding. Defaults to ".jpg".

    Returns:
        str | None: The base64 encoded string representation of the image, or None if encoding fails.
    """
    bytes_io = encode_image_as_buffer(img, ext)
    if bytes_io:
        return bytesio_to_base64(bytes_io)
    return None
