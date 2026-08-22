import pytest

from model.route_optimizer import nearest_neighbor_baseline, solve_vrp


def test_baseline_returns_round_trip_distance():
    depot = (40.7128, -74.0060)
    stops = [(40.7138, -74.0050), (40.7150, -74.0030)]
    assert nearest_neighbor_baseline(depot, stops) > 0


def test_every_stop_is_visited_once():
    depot = (40.7128, -74.0060)
    stops = [(40.7138, -74.0050), (40.7150, -74.0030), (40.7160, -74.0040)]
    result = solve_vrp(depot, stops, num_vehicles=1, vehicle_capacities=[3], demands=[0, 1, 1, 1])
    visited = [s["node"] for route in result["routes"] for s in route["stops"] if s["node"] != 0]
    assert sorted(visited) == [1, 2, 3]


def test_capacity_validation():
    depot = (40.7128, -74.0060)
    stops = [(40.7138, -74.0050), (40.7150, -74.0030)]
    with pytest.raises(ValueError, match="capacity"):
        solve_vrp(depot, stops, num_vehicles=1, vehicle_capacities=[1], demands=[0, 1, 1])


def test_invalid_demand_length():
    depot = (40.7128, -74.0060)
    stops = [(40.7138, -74.0050)]
    with pytest.raises(ValueError, match="demands"):
        solve_vrp(depot, stops, demands=[0, 1, 1])
