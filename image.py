import os
from PIL import Image, ImageOps

def crop_image(in_image_filename, out_image_filename, width, height):
    in_image = Image.open(in_image_filename)
    out_image = ImageOps.fit(
        in_image,
        (width, height),
        Image.ANTIALIAS
    )
    out_image.save(out_image_filename)

