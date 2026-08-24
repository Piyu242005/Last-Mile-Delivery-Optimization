from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "eta_model_loaded" in response.json()


def test_invalid_route_request_is_rejected():
    response = client.post(
        "/optimize-route",
        json={
            "depot": {"lat": 200, "lon": 0},
            "stops": [{"lat": 40.7, "lon": -74.0}],
        },
    )
    assert response.status_code == 422


def test_invalid_capacity_configuration_is_rejected():
    response = client.post(
        "/optimize-route",
        json={
            "depot": {"lat": 40.75, "lon": -73.99},
            "stops": [{"lat": 40.74, "lon": -73.98}],
            "num_vehicles": 2,
            "vehicle_capacities": [10],
        },
    )
    assert response.status_code == 422


def test_prediction_validation():
    response = client.post(
        "/predict",
        json={
            "trip_distance": -1,
            "haversine_km": 2,
            "hour_of_day": 10,
            "day_of_week": 2,
            "is_weekend": 0,
            "speed_mph": 20,
        },
    )
    assert response.status_code == 422
