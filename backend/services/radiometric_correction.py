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
