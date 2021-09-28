import numpy as np
import cv2
from eiseg.util.remotesensing import sample_norm


def check_sitk():
    try:
        import SimpleITK as sitk

        return True
    except ImportError:
        return False


if check_sitk:
    import SimpleITK as sitk


def dcm_reader(path):
    print(path)
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames([path])
    image = reader.Execute()
    print("image", image, type(image))
    img = sitk.GetArrayFromImage(image)
    print(img.shape, type(img))
    return img


# def open_nii(niiimg_path):
#     if IPT_SITK == True:
#         sitk_image = sitk.ReadImage(niiimg_path)
#         return _nii2arr(sitk_image)
#     else:
#         raise ImportError("can't import SimpleITK!")


#
# def _nii2arr(sitk_image):
#     if IPT_SITK == True:
#         img = sitk.GetArrayFromImage(sitk_image).transpose((1, 2, 0))
#         return img
#     else:
#         raise ImportError("can't import SimpleITK!")
#
#
# def slice_img(img, index):
#     if index == 0:
#         return sample_norm(
#             cv2.merge(
#                 [
#                     np.uint16(img[:, :, index]),
#                     np.uint16(img[:, :, index]),
#                     np.uint16(img[:, :, index + 1]),
#                 ]
#             )
#         )
#     elif index == img.shape[2] - 1:
#         return sample_norm(
#             cv2.merge(
#                 [
#                     np.uint16(img[:, :, index - 1]),
#                     np.uint16(img[:, :, index]),
#                     np.uint16(img[:, :, index]),
#                 ]
#             )
#         )
#     else:
#         return sample_norm(
#             cv2.merge(
#                 [
#                     np.uint16(img[:, :, index - 1]),
#                     np.uint16(img[:, :, index]),
#                     np.uint16(img[:, :, index + 1]),
#                 ]
#             )
#         )
