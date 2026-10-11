"""Canonical rendered-content identities, independent of file encoding."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from build_public_dashboard import image_checks


class ImageChecksTest(unittest.TestCase):
    def test_encoding_transparency_and_resizing(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b, c = [Path(folder) / name for name in ('a.png', 'b.png', 'c.png')]
            white = Image.new('RGB', (256, 256), 'white')
            white.save(a, compress_level=0)
            white.save(b, compress_level=9)
            self.assertNotEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(image_checks(a), image_checks(b))
            Image.new('RGBA', (256, 256), (10, 20, 30, 0)).save(c)
            self.assertEqual(image_checks(a), image_checks(c))
            # One almost-white pixel survives source hashing but rounds away at small sizes.
            white.putpixel((0, 0), (254, 254, 254))
            white.save(b)
            self.assertNotEqual(image_checks(a)['source_sha256'], image_checks(b)['source_sha256'])
            self.assertEqual(image_checks(a)['size_sha256'], image_checks(b)['size_sha256'])
            Image.new('RGB', (128, 128)).save(c)
            with self.assertRaises(ValueError):
                image_checks(c)


if __name__ == '__main__':
    unittest.main()
