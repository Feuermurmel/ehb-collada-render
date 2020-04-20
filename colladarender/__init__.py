import argparse
import math
import pathlib
import random
import sys

from PIL import Image, ImageDraw
import collada
import numpy
import matplotlib.cm


def log(message):
    print(message, file=sys.stderr, flush=True)


class UserError(Exception):
    def __init__(self, message, *args):
        super().__init__(message.format(*args))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-o',
        '--output',
        type=pathlib.Path,
        default=None)

    parser.add_argument(
        'input',
        type=pathlib.Path)

    return parser.parse_args()


def iter_triangles_from_collada_file(path):
    mesh = collada.Collada(str(path))

    for i in mesh.geometries:
        for j in i.primitives:
            for k in j.triangleset():
                yield k.vertices


def apply_homogeneous_transform(t, triangle):
    return numpy.concatenate((triangle, numpy.ones((len(triangle), 1))), 1) @ t.T


def color_to_8_bit(c):
    return tuple(int(i * 256) for i in c)


def render(output_image_file, input_dae_files):
    def iter_triangles():
        for path in input_dae_files:
            for i in iter_triangles_from_collada_file(path):
                yield sum(i[:, 1]), i

    random.seed(0)

    triangles = sorted(iter_triangles(), key=lambda x: x[0])
    color_map = matplotlib.cm.get_cmap('plasma')
    scale = 8

    min_height = triangles[0][0]
    max_height = triangles[-1][0]

    x_coordinates = [j for i in triangles for j in i[1][:, 0]]
    y_coordinates = [j for i in triangles for j in i[1][:, 2]]

    min_x = min(x_coordinates)
    max_x = max(x_coordinates)

    min_y = min(y_coordinates)
    max_y = max(y_coordinates)

    # Transform from the coordinate system used  by the model to the
    # coordinate system of the image.
    transform = \
        numpy.array([[scale, 0, 0], [0, scale, 0]]) \
        @ numpy.array([[1, 0, 0, -min_x], [0, 0, 1, -min_y], [0, 0, 0, 1]])

    image_width = math.ceil((max_x - min_x) * scale)
    image_height = math.ceil((max_y - min_y) * scale)

    with Image.new('RGBA', (image_width, image_height)) as image:
        draw = ImageDraw.Draw(image)

        for height, vertices in triangles:
            scaled_height = \
                (height - min_height) / (max_height - min_height)

            # Happens if all vertices triangles have the same height.
            if not math.isfinite(scaled_height):
                scaled_height = 0

            fill_color = color_map(scaled_height)
            line_color = color_map(scaled_height + 0.15)

            points = [
                tuple(vertex)
                for vertex in apply_homogeneous_transform(transform, vertices)]

            draw.polygon(points, fill=color_to_8_bit(fill_color))
            draw.line([*points, points[0]], fill=color_to_8_bit(line_color))

        temp_out_file = \
            output_image_file.with_name(output_image_file.name + '~')

        output_image_file.parent.mkdir(exist_ok=True)

        image.rotate(180).save(str(temp_out_file), 'PNG')
        temp_out_file.rename(output_image_file)


def main(output, input):
    if input.is_dir():
        input_paths = [
            file_path
            for file_path in input.iterdir()
            if not file_path.name.startswith('.')]
    else:
        input_paths = [input]

    if output is None:
        output = pathlib.Path('renderings') / (input.stem + '.png')

    log(f'Rendering {output} ...')
    render(output, input_paths)


def entry_point():
    try:
        main(**vars(parse_args()))
    except KeyboardInterrupt:
        log('Operation interrupted.')
        sys.exit(1)
    except UserError as e:
        log(f'error: {e}')
        sys.exit(2)
