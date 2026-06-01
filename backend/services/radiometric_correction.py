from backend.utils import min_max_scale
from itertools import pairwise

import numpy as np
import numpy.typing as npt


def get_radiometric_corrector() -> RadiometricCorrector:
    return RadiometricCorrector()


MAX_R = 3.0
MID_R = 0.13
SAT = 1.2
GAMMA = 1.8
G_OFF = 0.01
G_OFF_POW = G_OFF**GAMMA
G_OFF_RANGE = (1 + G_OFF) ** GAMMA - G_OFF_POW


def clip(arr: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    clipped = np.maximum(arr, 0)
    clipped = np.minimum(clipped, 1)

    return clipped


class RadiometricCorrector:

    # this function is based on the default "true color" evalscript from Copernicus browser
    def true_color(self, input_arr: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:

        rgb = np.copy(input_arr)

        rgb /= MAX_R

        rgb = clip(rgb)

        rgb = (
            rgb
            * (rgb * (MID_R / MAX_R) - 1.0)
            / (rgb * (2.0 * MID_R / MAX_R - 1.0) - MID_R / MAX_R)
        )

        rgb = ((rgb + G_OFF) ** GAMMA - G_OFF_POW) / G_OFF_RANGE

        avg_s = (rgb[0] + rgb[1] + rgb[2]) / 3.0 * (1.0 - SAT)

        rgb = clip(avg_s + rgb * SAT)

        rgb = np.where(
            rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**0.41666666666 - 0.055
        )

        return rgb

    def density_slice(
        self, image: npt.NDArray[np.float64], breaks: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:

        step_size = 1.0 / (breaks.size + 1)

        breaks = np.array([0, *breaks, 1])
        for i, (start, end) in enumerate(pairwise(breaks)):
            slice_bv = np.float64(i * step_size)

            image = np.where((start <= image) & (image < end), slice_bv, image)

        return image

    def linear_stretch(
        self,
        image: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        # Assume the image is of shape (3, height, width)
        image[0] = self._linear_stetch_one_band(image[0])
        image[1] = self._linear_stetch_one_band(image[1])
        image[2] = self._linear_stetch_one_band(image[2])

        return image

    def _linear_stetch_one_band(
        self, image: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        # Assume the image is of shape (height, width)

        return min_max_scale(image, np.float64(0), np.float64(1))


def histogram_equalize(arr: npt.NDArray[np.float64], bins: int = 1000):
    counts, edges = np.histogram(arr, bins=bins)

    cumulative_distribution = counts.cumsum() / counts.sum()  # normalized to [0, 1]

    # Average each pair of adjacent edges to get the centers
    bin_centers = (edges[:-1] + edges[1:]) / 2

    # bin_centers=X and cumulutative_distribution=Y create a piecewise linear function that is the cumulative histogram
    # but only has as much precision as the number of bins. We can interpolate the new values of arr from this histogram
    return np.interp(arr, bin_centers, cumulative_distribution)
