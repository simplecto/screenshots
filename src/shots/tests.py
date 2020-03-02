from django.test import TestCase
import json
from django.urls import reverse
from shots.models import ScreenShot
from django.http import HttpResponse, JsonResponse


class TestScreenShotAPI(TestCase):

    def setUp(self) -> None:
        self.api_url = reverse('api-screenshot')

    def do_post(self, data) -> JsonResponse:
        return self.client.post(
                    self.api_url,
                    data=json.dumps(data),
                    content_type='application/json'
        )

    def test_url_missing(self):
        data = {}
        response = self.do_post(data)
        self.assertEqual(response.status_code, 400)

    def test_url_domain_does_not_exist(self):
        data = {'url': 'sdf234dfg345fdg-doesnotexist.com'}
        response = self.do_post(data)
        self.assertEqual(response.status_code, 400)

    def test_url_malformatted(self):
        data = {'url': 'htp:google.com'}
        response = self.do_post(data)
        self.assertEqual(response.status_code, 400)

    def test_url_ok(self):
        data = {'url': 'http://google.com'}
        response = self.do_post(data)
        self.assertEqual(response.status_code, 201)

    def test_callback_url_domain_does_not_exist(self):
        data = {
            'url': 'https://www.simplecto.com',
            'callback_url': 'sdf234dfg345fdg-doesnotexist.com'
        }
        response = self.do_post(data)
        self.assertEqual(response.status_code, 400)

    def test_callback_url_malformatted(self):
        data = {
            'url': 'https://www.simplecto.com',
            'callback_url': 'htp:sdf234dfg345fdg-doesnotexist.com'
        }
        response = self.do_post(data)
        self.assertEqual(response.status_code, 400)
