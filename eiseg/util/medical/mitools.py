def check_sitk():
    try:
        import SimpleITK as sitk
        return True
    except ImportError:
        return False


import numpy as np
import cv2
from eiseg.util.remotesensing import sample_norm

IPT_SITK = check_sitk()
if IPT_SITK:
    import SimpleITK as sitk


def open_nii(niiimg_path):
    if IPT_SITK == True:
        sitk_image = sitk.ReadImage(niiimg_path)
        return _nii2arr(sitk_image)
    else:
        raise ImportError('can\'t import SimpleITK!')


def _nii2arr(sitk_image):
    if IPT_SITK == True:
        img = sitk.GetArrayFromImage(sitk_image).transpose((1, 2, 0))
        return img
    else:
        raise ImportError('can\'t import SimpleITK!')


def slice_img(img, index):
    return sample_norm(cv2.merge([np.uint16(img[:, :, index])] * 3))