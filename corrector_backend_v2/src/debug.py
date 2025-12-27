import cv2
import numpy as np

from .image_manipulation import resize_to_fit, resize_to_vertical_fit


def show(img, name="debug_img"):
    """
    Displays an image in a window for debugging purposes.

    Args:
        img (np.ndarray): The image to be displayed.
        name (str): The name of the display window. Defaults to "debug_img".
    """
    cv2.namedWindow(name)
    cv2.moveWindow(name, 40, 30)
    cv2.imshow(name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def debug_show_image(debug_img: np.ndarray, points: np.ndarray | None = None, pad=30, name="debug_img"):
    """
    Draws numbers on specified points in an image for debugging purposes.

    Args:
        debug_img (np.ndarray): The image on which points will be drawn.
        points (np.ndarray): Points to be marked, in the format [[X1, Y1], [X2, Y2], ...].
        pad (int): Padding to add around the image. Defaults to 30.
        name (str): The name of the display window. Defaults to "debug_img".
    """
    debug_img = cv2.copyMakeBorder(debug_img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    if points is not None:
        debug_img = debug_img.copy()

        if len(debug_img.shape) == 2:
            debug_img = cv2.cvtColor(debug_img, cv2.COLOR_GRAY2BGR)

        # Draw points and numbers
        for i, (x, y) in enumerate(points):
            x = int(x) + pad
            y = int(y) + pad

            cv2.circle(debug_img, (x, y), radius=3, color=(0, 255, 0), thickness=-1)
            cv2.putText(debug_img, str(i + 1), (x, y), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.9, color=(0, 0, 255), thickness=1, lineType=cv2.LINE_AA)

    debug_img = resize_to_fit(debug_img)
    show(debug_img, name=name)


def debug_show_images(*arg, concatenate=False, resize=True, axis=1):
    """
    Displays multiple images side by side or separately for debugging purposes.

    Args:
        *arg: Variable number of images to display.
        concatenate (bool): Whether to concatenate the images into one display. Defaults to False.
        resize (bool): Whether to resize the images to fit the screen. Defaults to True.
        axis (int): The axis along which images will be concatenated if `concatenate` is True. Defaults to 1.
    """
    if concatenate:
        images = [resize_to_vertical_fit(img, screen_height=1000) if resize else img for img in arg]
        concatenated = np.concatenate(images, axis=axis)
        show(resize_to_fit(concatenated))
    else:
        for img in arg:
            show(resize_to_fit(img) if resize else img)
