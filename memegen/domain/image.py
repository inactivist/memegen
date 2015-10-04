import os
import logging

from PIL import Image as ImageFile, ImageFont, ImageDraw


log = logging.getLogger(__name__)

# TODO: move to a fonts store
FONT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    'data', 'fonts', 'Impact.ttf'
))


class Image:
    """JPEG generated by applying text to a template."""

    def __init__(self, template, text, root=None):
        self.template = template
        self.text = text
        self.root = root

    @property
    def path(self):
        if self.root:
            return os.path.join(self.root, self.template.key,
                                self.text.path + '.jpg')
        else:
            return None

    def generate(self):
        directory = os.path.dirname(self.path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        make_meme(self.text.top, self.text.bottom,
                  self.template.path, self.path)


# based on: https://github.com/danieldiekmeier/memegenerator
def make_meme(top, bottom, background, path, match_font_size=False):
    """Add text to an image and save it."""
    img = ImageFile.open(background)

    # Resize to a maximum height and width
    img.thumbnail((500, 500))
    image_size = img.size

    # Draw image
    draw = ImageDraw.Draw(img)

    max_font_size = int(image_size[1] / 5)
    min_font_size_single_line = int(image_size[1] / 12)
    max_text_len = image_size[0] - 20
    top_font_size, top = _optimize_font_size(top, max_font_size,
                                             min_font_size_single_line,
                                             max_text_len)
    bottom_font_size, bottom = _optimize_font_size(bottom, max_font_size,
                                                   min_font_size_single_line,
                                                   max_text_len)

    if match_font_size is True:
        top_font_size = min(top_font_size, bottom_font_size)
        bottom_font_size = top_font_size

    top_font = ImageFont.truetype(FONT, top_font_size)
    bottom_font = ImageFont.truetype(FONT, bottom_font_size)

    top_text_size = draw.multiline_textsize(top, top_font)
    bottom_text_size = draw.multiline_textsize(bottom, bottom_font)

    # Find top centered position for top text
    top_text_position_x = (image_size[0] / 2) - (top_text_size[0] / 2)
    top_text_position_y = 0
    top_text_position = (top_text_position_x, top_text_position_y)

    # Find bottom centered position for bottom text
    bottom_text_size_x = (image_size[0] / 2) - (bottom_text_size[0] / 2)
    bottom_text_size_y = image_size[1] - bottom_text_size[1] * (7 / 6)
    bottom_text_position = (bottom_text_size_x, bottom_text_size_y)

    _draw_outlined_text(draw, top_text_position,
                        top, top_font, top_font_size)
    _draw_outlined_text(draw, bottom_text_position,
                        bottom, bottom_font, bottom_font_size)

    log.info("generating: %s", path)
    return img.save(path)


def _draw_outlined_text(draw_image, text_position, text, font, font_size):
    """Draw white text with black outline on an image."""

    # Draw black text outlines
    outline_range = max(1, font_size // 25)
    for x in range(-outline_range, outline_range + 1):
        for y in range(-outline_range, outline_range + 1):
            pos = (text_position[0] + x, text_position[1] + y)
            draw_image.multiline_text(pos, text, (0, 0, 0),
                                      font=font, align='center')

    # Draw inner white text
    draw_image.multiline_text(text_position, text, (255, 255, 255),
                              font=font, align='center')


def _optimize_font_size(text, max_font_size, min_font_size,
                        max_text_len):
    """Calculate the optimal font size to fit text in a given size."""
    # Check size when using smallest single line font size
    font = ImageFont.truetype(FONT, min_font_size)
    text_size = font.getsize(text)

    # calculate font size for text, split if necessary
    if text_size[0] > max_text_len:
        phrases = _split(text)
    else:
        phrases = [text]
    font_size = max_font_size // len(phrases)
    for phrase in phrases:
        font_size = min(_maximize_font_size(phrase, max_text_len),
                        font_size)

    # rebuild text with new lines
    text = '\n'.join(phrases)

    return font_size, text


def _maximize_font_size(text, max_size):
    """Find the biggest font size that will fit."""
    font_size = max_size
    font = ImageFont.truetype(FONT, font_size)
    text_size = font.getsize(text)
    while text_size[0] > max_size and font_size > 1:
        font_size = font_size - 1
        font = ImageFont.truetype(FONT, font_size)
        text_size = font.getsize(text)
    return font_size


def _split(text):
    """Split a line of text into two similarly sized pieces.

    >>> _split("Hello, world!")
    ('Hello,', 'world!')

    >>> _split("This is a phrase that can be split.")
    ('This is a phrase', 'that can be split.')

    >>> _split("This_is_a_phrase_that_can_not_be_split.")
    ('This_is_a_phrase_that_can_not_be_split.',)
    """
    result = (text,)
    if len(text) >= 3 and ' ' in text[1:-1]:  # can split this string
        space_indices = [i for i in range(len(text)) if text[i] == ' ']
        space_proximities = [abs(i - len(text) // 2) for i in space_indices]
        for i, j in zip(space_proximities, space_indices):
            if i == min(space_proximities):
                result = (text[:j], text[j + 1:])
                break
    return result
