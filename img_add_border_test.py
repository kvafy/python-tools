import img_add_border
import unittest
from unittest.mock import MagicMock


WHITE = '#ffffff'


class TestImgAddBorder(unittest.TestCase):

    # Final image with border should be 4x4 mm, from that 1 mm border
    # on all sides. Ie. half of width/height is border and the other
    # half is the original image. Therefore the image should be resized
    # from 10x10 px to 20x20 px.
    def test_add_border__artificial_square(self):
        ratio = (1, 1)
        (img_w_mm, img_h_mm) = (4, 4)
        border_mm = 1

        (img_w_px, img_h_px) = (10, 10)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        # Cropping is not needed.
        self.assert_no_such_command(commands, 'convert', [['-extent']])
        # Added border 5 px on all sides.
        self.assert_command(commands, 'convert', [['-border', '5x5']])

    # Let's create an artificial example that should result in no crop.
    # Target image: 1200x1800 px, 100x150 mm, 10 mm border
    #  => 10 mm out of 100 mm is 10% => 10% of 1200 px = 120 px (border)
    #  => Image without border is (1200 - 2*120)x(1800 - 2*120)px =
    #     = 960x1560 px.
    #       This should be the original image size to achieve no crop.
    def test_add_border__10x15cm_portrait__no_crop(self):
        ratio = (2, 3)
        (img_w_mm, img_h_mm) = (100, 150)
        border_mm = 10

        (img_w_px, img_h_px) = (960, 1560)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        # Cropping is not needed.
        self.assert_no_such_command(commands, 'convert', [['-extent']])
        # Added border 120 px on all sides.
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    def test_add_border__10x15cm_landscape__no_crop(self):
        ratio = (3, 2)
        (img_w_mm, img_h_mm) = (150, 100)
        border_mm = 10

        (img_w_px, img_h_px) = (1560, 960)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        # Cropping is not needed.
        self.assert_no_such_command(commands, 'convert', [['-extent']])
        # Added border 5 px on all sides.
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    # First, let's create an artificial example that should result in no crop.
    # Target image: 1200x1800 px, 100x150 mm, 10 mm border
    #  => 10 mm out of 100 mm is 10% => 10% of 1200 px = 120 px (border)
    #  => Image without border is (1200 - 2*120)x(1800 - 2*120)px =
    #     = 960x1560 px.
    #       This should be the original image size to achieve no crop.
    # Second, let's inlate a dimension by 100 px, which should be cropped.
    def test_add_border__10x15cm_portrait__crop_width(self):
        ratio = (2, 3)
        (img_w_mm, img_h_mm) = (100, 150)
        border_mm = 10

        (img_w_px, img_h_px) = (960 + 100, 1560)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        self.assert_command(commands, 'convert', [['-extent', '960x1560']])
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    def test_add_border__10x15cm_portrait__crop_height(self):
        ratio = (2, 3)
        (img_w_mm, img_h_mm) = (100, 150)
        border_mm = 10

        (img_w_px, img_h_px) = (960, 1560 + 100)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        self.assert_command(commands, 'convert', [['-extent', '960x1560']])
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    def test_add_border__10x15cm_landscape__crop_width(self):
        ratio = (3, 2)
        (img_w_mm, img_h_mm) = (150, 100)
        border_mm = 10

        (img_w_px, img_h_px) = (1560 + 100, 960)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        self.assert_command(commands, 'convert', [['-extent', '1560x960']])
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    def test_add_border__10x15cm_landscape__crop_height(self):
        ratio = (3, 2)
        (img_w_mm, img_h_mm) = (150, 100)
        border_mm = 10

        (img_w_px, img_h_px) = (1560, 960 + 100)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        self.assert_command(commands, 'convert', [['-extent', '1560x960']])
        self.assert_command(commands, 'convert', [['-border', '120x120']])

    # Let's assume image that almost perfectly fits the target ratio but extra
    # pixels need to be cropped because the pixel dimensions of the image
    # are not multiples of the ratio.
    def test_add_border__pixels_over_ratio_are_cropped(self):
        ratio = (2, 3)
        (img_w_mm, img_h_mm) = (100, 150)
        border_mm = 0  # No border needed in this test

        (img_w_px, img_h_px) = (100 + 1, 150 + 2)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE)

        self.assert_command(commands, 'convert', [['-extent', '100x150']])

    # Target DPI = 300, meaning that an image 4x6 inches needs to be
    # (4*300)x(6*300) px = 1200x1800 px after DPI conversion.
    def test_add_border__convert_dpi(self):
        ratio = (2, 3)
        img_w_mm = img_add_border.convert_to_mm(4, 'inch')
        img_h_mm = img_add_border.convert_to_mm(6, 'inch')
        border_mm = 0  # No border needed in this test

        (img_w_px, img_h_px) = (5000, 5000)
        self.fake_image_size((img_w_px, img_h_px))

        commands = img_add_border.add_border(
            'in.jpg', ratio, (img_w_mm, img_h_mm), border_mm, WHITE, dpi=300)

        self.assert_command(
            commands, 'convert', [['-density', '300'], ['-resize', '1200x1800']])


    # Helper methods.

    def fake_image_size(self, size_px):
        def fake_run_shell(args):
            if args[0] == 'identify':
                return (0, '%dx%d' % size_px, '')  # exit code, stdout, stderr
        img_add_border.run_shell = MagicMock(side_effect=fake_run_shell)

    def assert_no_such_command(self, commands, prog, subargs):
        odd_cmd = self.get_command_with_argument(commands, prog, subargs)
        if odd_cmd:
            self.fail('unexpected command %s' % (str(odd_cmd),))

    def assert_command(self, commands, prog, subargs):
        if not self.get_command_with_argument(commands, prog, subargs):
            self.fail('Command not executed: "%s with %s" in %s' % (
                prog, str(subargs), str(commands)))

    def get_command_with_argument(self, commands, prog, subargs):
        def is_sublist_of(needle, haystack):
            for i in range(len(haystack) - len(needle)):
                for j in range(len(needle)):
                    if haystack[i + j] != needle[j]:
                        break
                else:
                    return True
            return False

        for cmd in commands:
            if cmd[0] == prog:
                if all([is_sublist_of(a, cmd) for a in subargs]):
                    return cmd
        return None


if __name__ == '__main__':
    unittest.main()
