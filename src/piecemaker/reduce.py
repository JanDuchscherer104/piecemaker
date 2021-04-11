import os
import json
import shutil
from glob import iglob

from PIL import Image

from piecemaker.tools import scale_down_imgfile, potrace
from piecemaker.sprite import generate_sprite_layout, generate_sprite_svg
from piecemaker.cut_proof import generate_cut_proof_html
from piecemaker.sprite_vector_proof import generate_sprite_vector_proof_html


def reduce_size(scale, minimum_scale, output_dir):
    factor = scale / minimum_scale
    minimum_scaled_dir = os.path.join(output_dir, f"scale-{minimum_scale}")
    scaled_dir = os.path.join(output_dir, f"scale-{scale}")

    shutil.copytree(minimum_scaled_dir, scaled_dir)
    os.rename(
        os.path.join(scaled_dir, f"lines-{minimum_scale}.png"),
        os.path.join(scaled_dir, f"lines-{scale}.png"),
    )
    os.rename(
        os.path.join(scaled_dir, f"original-{minimum_scale}.jpg"),
        os.path.join(scaled_dir, f"original-{scale}.jpg"),
    )

    for filename in [
        "masks.json",
        "cut_proof.html",
        "sprite.svg",
        "sprite_vector_proof.html",
        "sprite_with_padding.jpg",
        "sprite_layout.json",
    ]:
        os.unlink(os.path.join(scaled_dir, filename))
    shutil.rmtree(os.path.join(scaled_dir, "vector"))

    for ext in [".jpg", ".png", ".bmp"]:
        for imgfile in iglob(f"{scaled_dir}/**/*{ext}", recursive=True):
            scale_down_imgfile(imgfile, factor)

    with open(os.path.join(scaled_dir, "pieces.json"), "r") as pieces_json:
        piece_bboxes = json.load(pieces_json)
    with open(
        os.path.join(scaled_dir, "piece_id_to_mask.json"), "r"
    ) as piece_id_to_mask_json:
        piece_id_to_mask = json.load(piece_id_to_mask_json)
    for (i, bbox) in piece_bboxes.items():
        im = Image.open(os.path.join(scaled_dir, "mask", f"{piece_id_to_mask[i]}.bmp"))
        (width, height) = im.size
        im.close()
        bbox[0] = round(bbox[0] * factor)
        bbox[1] = round(bbox[1] * factor)
        bbox[2] = bbox[0] + width
        bbox[3] = bbox[1] + height
    with open(os.path.join(scaled_dir, "pieces.json"), "w") as pieces_json:
        json.dump(piece_bboxes, pieces_json)

    os.mkdir(os.path.join(scaled_dir, "vector"))
    for piece in iglob(os.path.join(scaled_dir, "mask", "*.bmp")):
        potrace(piece, os.path.join(scaled_dir, "vector"))

    sprite_layout = generate_sprite_layout(
        raster_dir=os.path.join(scaled_dir, "raster_with_padding"),
        output_dir=scaled_dir,
    )
    jpg_sprite_file_name = os.path.join(scaled_dir, "sprite_with_padding.jpg")

    generate_sprite_svg(
        sprite_layout=sprite_layout,
        jpg_sprite_file_name=jpg_sprite_file_name,
        scaled_image=os.path.join(scaled_dir, f"original-{scale}.jpg"),
        output_dir=scaled_dir,
        scale=scale,
        pieces_json_file=os.path.join(scaled_dir, "pieces.json"),
        vector_dir=os.path.join(scaled_dir, "vector"),
    )

    generate_sprite_vector_proof_html(
        pieces_json_file=os.path.join(scaled_dir, "pieces.json"),
        sprite_svg_file=os.path.join(scaled_dir, "sprite.svg"),
        output_dir=scaled_dir,
        sprite_layout=sprite_layout,
        scale=scale,
    )

    generate_cut_proof_html(
        pieces_json_file=os.path.join(scaled_dir, "pieces.json"),
        output_dir=scaled_dir,
        scale=scale,
    )