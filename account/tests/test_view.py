from account.factories import UserFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from config.testing.base import BaseAPITest


class UserprofleTest(BaseAPITest):
    def setUp(self):
        self.test_user = UserFactory()
        super().setUp()

    def test_get_userprofile(self):
        url = reverse("account_userprofile")

        res: Response = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.test_user)
        res: Response = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_update_userprofile(self):
        url = reverse("account_userprofile")

        new_data = {
            "first_name": "new name",
            "last_name": "new last name",
        }

        res: Response = self.client.patch(url, new_data, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.test_user)
        res: Response = self.client.patch(url, new_data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_registration_is_marked_as_completed(self):
        url = reverse("account_userprofile")
        complete_data = {
            "first_name": "new name",
            "last_name": "new last name",
            "mobile": "+233559899966",
            "extension": "12345",
        }
        self.client.force_authenticate(user=self.test_user)
        res: Response = self.client.patch(url, complete_data, format="json")
        self.assertTrue(res.data.get("is_registration_completed"))

        incomplete_data = {
            "first_name": "new name",
            "last_name": "",
            "mobile": "+233559899966",
            "extension": "12345",
        }
        res: Response = self.client.patch(url, incomplete_data, format="json")
        self.assertFalse(res.data.get("is_registration_completed"))

    def test_update_profile_picture(self):
        self.client.force_authenticate(user=self.test_user)
        url = reverse("account_userprofile")

        new_data = {"profile_picture": self.generate_base64_photo_file()}

        res: Response = self.client.patch(url, new_data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data.get("profile_picture"))

    def test_delete_account(self):
        self.client.force_authenticate(user=self.test_user)
        url = reverse("account_userprofile")

        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
