import base64
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient


class BaseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def generate_base64_photo_file(self):
        image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_file = SimpleUploadedFile("test.png", buffer.getvalue())

        # Convert the image file to a Base64-encoded string
        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

        return image_b64
