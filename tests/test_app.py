"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


# Store the original activities data
ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture
def client():
    """Provide a TestClient and reset activities state before each test"""
    # Reset activities to original state
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that /activities returns a dict of activities"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that response contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data

    def test_participants_list_is_list(self, client):
        """Test that participants is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_data in data.values():
            assert isinstance(activity_data["participants"], list)

    def test_activity_has_initial_participants(self, client):
        """Test that activities have their initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have michael and daniel
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "signed up" in data["message"].lower()

    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        email = "test@mergington.edu"
        activity = "Art Studio"
        
        # Signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can signup for same activity"""
        activity = "Science Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Add first student
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        assert response1.status_code == 200
        
        # Add second student
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        assert response2.status_code == 200
        
        # Verify both are in activity
        response = client.get("/activities")
        data = response.json()
        assert email1 in data[activity]["participants"]
        assert email2 in data[activity]["participants"]

    def test_signup_response_message_format(self, client):
        """Test that signup returns proper message"""
        email = "newstudent@mergington.edu"
        activity = "Debate Team"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]


class TestUnregisterEndpoint:
    """Tests for POST /unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregister"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "unregistered" in data["message"].lower()

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from activity"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]

    def test_unregister_nonexistent_student_returns_400(self, client):
        """Test that unregistering non-existent student returns 400"""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_response_message_format(self, client):
        """Test that unregister returns proper message"""
        email = "emma@mergington.edu"
        activity = "Programming Class"
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_unregister_then_signup_again(self, client):
        """Test that a student can signup after unregistering"""
        email = "jordan@mergington.edu"
        activity = "Tennis Club"
        
        # Unregister
        response1 = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Signup again
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify they're registered
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests covering real-world scenarios"""

    def test_full_signup_flow(self, client):
        """Test complete signup flow: view activities -> signup -> see update"""
        # 1. Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        initial_count = len(data["Theater Club"]["participants"])
        
        # 2. Signup
        email = "newactor@mergington.edu"
        response = client.post(f"/activities/Theater%20Club/signup?email={email}")
        assert response.status_code == 200
        
        # 3. Verify update
        response = client.get("/activities")
        data = response.json()
        assert len(data["Theater Club"]["participants"]) == initial_count + 1
        assert email in data["Theater Club"]["participants"]

    def test_signup_unregister_signup_cycle(self, client):
        """Test cycle: signup -> unregister -> signup again"""
        email = "cycling@mergington.edu"
        activity = "Basketball Team"
        
        # Signup
        r1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert r1.status_code == 200
        
        # Unregister
        r2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert r2.status_code == 200
        
        # Signup again
        r3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert r3.status_code == 200
        
        # Verify final state
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
