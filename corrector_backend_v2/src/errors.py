
class WrongNumberDetectedInImageException(Exception):
    """
    Raised when an incorrect number of elements is detected in the image.
    """
    pass


class UnableToFindFourAlignTrianglesException(Exception):
    """
    Raised when the number of detected triangles is not equal to 4.

    Attributes:
        image (np.ndarray): The image where the error occurred.
        amount (int): The number of detected triangles.
    """
    def __init__(self, image, amount):
        self.image = image
        self.amount = amount
        super().__init__(f"Found '{amount}', not the 4 triangles expected.")


class FoundAlignTrianglesAreNotFilledException(Exception):
    """
    Raised when the detected aligned triangles are not filled above the required threshold.

    Attributes:
        image (np.ndarray): The image where the error occurred.
        mean_val (float): The mean pixel value of the triangle.
        min_threshold (float): The minimum pixel value threshold.
    """
    def __init__(self, image, mean_val, min_threshold):
        self.image = image
        self.mean_val = mean_val
        self.min_threshold = min_threshold
        super().__init__(f"FoundAlignTrianglesAreNotFilledException: mean_val: '{mean_val}', min_threshold: '{min_threshold}'.")
