from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    participant_lists = {
        activity_name: deepcopy(activity["participants"])
        for activity_name, activity in activities.items()
    }

    with TestClient(app) as test_client:
        yield test_client

    for activity_name, participants in participant_lists.items():
        activities[activity_name]["participants"] = participants


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.json()["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Soccer Club"
    }
    assert email in activities["Soccer Club"]["participants"]


def test_duplicate_signup_returns_bad_request(client):
    email = "new.student@mergington.edu"
    activities["Soccer Club"]["participants"].append(email)

    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities["Soccer Club"]["participants"].count(email) == 1


def test_signup_for_unknown_activity_returns_not_found(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    email = "new.student@mergington.edu"
    activities["Soccer Club"]["participants"].append(email)

    response = client.delete(f"/activities/Soccer Club/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Soccer Club"
    }
    assert email not in activities["Soccer Club"]["participants"]


def test_unregister_unknown_participant_returns_not_found(client):
    response = client.delete(
        "/activities/Soccer Club/participants/missing.student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}


def test_unregister_from_unknown_activity_returns_not_found(client):
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
