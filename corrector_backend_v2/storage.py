import zarr
import numpy as np
from numcodecs import Blosc

IMAGES = "images"
LABELS = "labels"


class StorageMapper:

    def __init__(self, store_path: str, image_shape: (int, int, int), label_size: int, chunk_size: int):
        self.store_path = store_path
        self.image_shape = image_shape
        self.label_size = label_size
        self.chunk_size = chunk_size

        self.store = self.create_or_get_zarr_store()

    def create_or_get_zarr_store(self):
        """
        Create or open a Zarr store with two datasets: 'images' and 'labels'.
        Both are initialized with zero length on the first dimension
        (i.e., the batch dimension).
        """
        zarr_store = zarr.open(self.store_path, mode='a')

        compressor = Blosc(cname='zstd', clevel=5, shuffle=Blosc.SHUFFLE)

        if IMAGES not in zarr_store:
            zarr_store.create_dataset(
                name=IMAGES,
                shape=(0,) + self.image_shape,
                chunks=(self.chunk_size,) + self.image_shape,
                dtype=np.uint8,
                compressor=compressor,
            )

        if LABELS not in zarr_store:
            zarr_store.create_dataset(
                name=LABELS,
                shape=(0, self.label_size),
                chunks=(self.chunk_size, self.label_size),
                dtype=np.int8,
                compressor=compressor,
            )

        return zarr_store

    def append_data(self, new_images: np.ndarray, new_labels: np.ndarray):
        """
        Append new data to the 'images' and 'labels' Zarr datasets.
        """
        assert new_images.shape[0] == new_labels.shape[0], (
            f"ERROR. Shapes must match {new_images.shape=} and {new_labels.shape=}."
        )
        assert new_images.shape[1:] == self.image_shape, (
            f"Incompatible image shape. "
            f"Expected {self.image_shape}, got {new_images.shape[1:]}"
        )
        assert new_labels.shape[1:] == (self.label_size,), (
            f"Incompatible label shape. "
            f"Expected {(self.label_size,)}, found {new_labels.shape[1:]}."
        )

        images_ds = self.store[IMAGES]
        labels_ds = self.store[LABELS]

        new_length = images_ds.shape[0] + new_images.shape[0]
        new_shape_images = (new_length,) + images_ds.shape[1:]
        new_shape_labels = (new_length,) + labels_ds.shape[1:]
        images_ds.resize(new_shape_images)
        labels_ds.resize(new_shape_labels)

        images_ds[-new_images.shape[0]:] = new_images
        labels_ds[-new_labels.shape[0]:] = new_labels


def lazy_iterate_dataset(store_path: str, batch_size: int, start_index: int = 0, end_index: int = None):
    """
    A generator that yields (images, labels) in slices (batches) from
    the Zarr store, allowing for lazy loading and memory efficiency.

    :param store_path: Path of store.
    :param batch_size: Size of each chunk.
    :param start_index: Starting index in the dataset (default 0).
    :param end_index: Ending index (exclusive). If None, goes to the end.

    Yields:
        (images_batch, labels_batch) in consecutive slices of length batch_size.
    """

    store = zarr.open(store_path, mode='a')
    images_ds = store[IMAGES]
    labels_ds = store[LABELS]

    total_length = images_ds.shape[0]

    if end_index is None:
        end_index = total_length

    end_index = min(end_index, total_length)
    for i in range(start_index, end_index, batch_size):
        start = i
        stop = min(i + batch_size, end_index)
        batch_images = images_ds[start:stop]
        batch_labels = labels_ds[start:stop]
        yield batch_images, batch_labels
