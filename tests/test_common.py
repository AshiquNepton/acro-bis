import json
from django.test import SimpleTestCase, Client
from django.urls import reverse


class AuthenticationSecurityTests(SimpleTestCase):
    """
    Tests enforcing authentication and tenant isolation policies
    specified in docs/SECURITY.md and docs/ARCHITECTURE.md.
    """
    databases = {'default'}

    def setUp(self):
        self.client = Client()

    def test_login_page_is_public(self):
        """Root login view at /common/ must be accessible unauthenticated."""
        response = self.client.get('/common/')
        self.assertEqual(response.status_code, 200)

    def test_root_redirects_to_login(self):
        """Root / must redirect to /common/."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/common/')

    def test_unauthenticated_page_access_redirects_to_login(self):
        """Standard browser requests to protected views redirect to login."""
        protected_urls = [
            '/inventory/dashboard/',
            '/financial/dashboard/',
            '/restaurant/dashboard/',
            '/laundry/dashboard/',
            '/reports/stock-report/',
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"Expected 302 redirect for {url}")
            self.assertIn('/common/', response.url)

    def test_unauthenticated_ajax_returns_401_json(self):
        """AJAX requests to protected views return 401 JSON per docs/SECURITY.md §2."""
        response = self.client.get(
            '/inventory/dashboard/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Session expired', data['error'])

    def test_unauthenticated_fetch_json_accept_header_returns_401(self):
        """Fetch requests with application/json Accept header return 401 JSON."""
        response = self.client.get(
            '/reports/stock-report/',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Session expired', data['error'])
