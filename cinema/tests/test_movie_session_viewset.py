from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from cinema.models import Movie, Genre, Actor, CinemaHall, MovieSession
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta


MOVIESESSION_URL = reverse("cinema:moviesession-list")


def detail_url(session_id):
    return reverse("cinema:moviesession-detail", args=[session_id])


class MovieSessionViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@cinema.com", password="testpass"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@cinema.com", password="adminpass"
        )
        self.genre = Genre.objects.create(name="Action")
        self.actor = Actor.objects.create(first_name="John", last_name="Doe")
        self.movie = Movie.objects.create(
            title="Test Movie", description="Desc", duration=120
        )
        self.movie.genres.add(self.genre)
        self.movie.actors.add(self.actor)
        self.hall = CinemaHall.objects.create(name="Hall 1", rows=5, seats_in_row=5)
        self.session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.hall,
            show_time=datetime.now() + timedelta(days=1),
        )

    def test_list_sessions_requires_auth(self):
        res = self.client.get(MOVIESESSION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        res = self.client.get(MOVIESESSION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_filter_sessions_by_date(self):
        self.client.force_authenticate(user=self.user)
        date_str = self.session.show_time.strftime("%Y-%m-%d")
        res = self.client.get(MOVIESESSION_URL, {"date": date_str})
        self.assertEqual(len(res.data), 1)

    def test_filter_sessions_by_movie(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(MOVIESESSION_URL, {"movie": self.movie.id})
        self.assertEqual(len(res.data), 1)

    def test_retrieve_session_detail_requires_auth(self):
        url = detail_url(self.session.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.session.id)

    def test_create_session_admin_only(self):
        payload = {
            "movie": self.movie.id,
            "cinema_hall": self.hall.id,
            "show_time": (datetime.now() + timedelta(days=2)).isoformat(),
        }
        self.client.force_authenticate(user=self.user)
        res = self.client.post(MOVIESESSION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        res = self.client.post(MOVIESESSION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
