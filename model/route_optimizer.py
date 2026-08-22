from typing import Optional, Sequence, Tuple

import haversine as hs
import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

Coordinate = Tuple[float, float]


def _validate_inputs(stops_coords, num_vehicles, vehicle_capacities, demands, traffic_factor):
    if not stops_coords:
        raise ValueError("At least one delivery stop is required.")
    if num_vehicles < 1:
        raise ValueError("num_vehicles must be at least 1.")
    if traffic_factor <= 0:
        raise ValueError("traffic_factor must be greater than 0.")
    if demands is not None:
        if len(demands) != len(stops_coords) + 1:
            raise ValueError("demands must contain one depot value plus one value per stop.")
        if any(d < 0 for d in demands):
            raise ValueError("demands cannot contain negative values.")
    if vehicle_capacities is not None:
        if len(vehicle_capacities) != num_vehicles:
            raise ValueError("vehicle_capacities must contain one value per vehicle.")
        if any(c <= 0 for c in vehicle_capacities):
            raise ValueError("vehicle capacities must be positive.")


def create_data_model(depot_coords, stops_coords, num_vehicles=1, vehicle_capacities=None, demands=None, traffic_factor=1.0):
    _validate_inputs(stops_coords, num_vehicles, vehicle_capacities, demands, traffic_factor)
    locations = [depot_coords] + list(stops_coords)
    n = len(locations)
    dist_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i != j:
                d_km = hs.haversine(locations[i], locations[j])
                dist_matrix[i][j] = max(1, int(d_km * 1000 * traffic_factor))

    demands = [0] + [1] * len(stops_coords) if demands is None else list(demands)
    vehicle_capacities = [10] * num_vehicles if vehicle_capacities is None else list(vehicle_capacities)
    if sum(demands) > sum(vehicle_capacities):
        raise ValueError("Total delivery demand exceeds total fleet capacity.")

    return {
        "distance_matrix": dist_matrix.tolist(),
        "num_vehicles": num_vehicles,
        "depot": 0,
        "demands": demands,
        "vehicle_capacities": vehicle_capacities,
    }, locations


def nearest_neighbor_baseline(depot_coords, stops_coords):
    """Return a deterministic nearest-neighbor depot->stops->depot baseline in km."""
    remaining = list(stops_coords)
    current = depot_coords
    total_km = 0.0
    while remaining:
        next_stop = min(remaining, key=lambda stop: hs.haversine(current, stop))
        total_km += hs.haversine(current, next_stop)
        current = next_stop
        remaining.remove(next_stop)
    total_km += hs.haversine(current, depot_coords)
    return round(total_km, 2)


def solve_vrp(depot_coords, stops_coords, num_vehicles=1, vehicle_capacities=None, demands=None, traffic_factor=1.0):
    data, locations = create_data_model(depot_coords, stops_coords, num_vehicles, vehicle_capacities, demands, traffic_factor)
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), data["num_vehicles"], data["depot"])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return data["distance_matrix"][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        return data["demands"][manager.IndexToNode(from_index)]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_callback_index, 0, data["vehicle_capacities"], True, "Capacity")

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.FromSeconds(3)
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        raise ValueError("No feasible route found. Check demands and vehicle capacities.")

    routes = []
    total_distance_m = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_list = []
        route_distance_m = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            lat, lon = locations[node_index]
            label = "Depot" if node_index == 0 else f"Stop {node_index} (Load: {data['demands'][node_index]})"
            route_list.append({"node": node_index, "label": label, "lat": lat, "lon": lon})
            next_index = solution.Value(routing.NextVar(index))
            route_distance_m += routing.GetArcCostForVehicle(index, next_index, vehicle_id)
            index = next_index
        lat, lon = locations[0]
        route_list.append({"node": 0, "label": "Depot (Return)", "lat": lat, "lon": lon})
        if len(route_list) > 2:
            distance_km = round(route_distance_m / 1000.0 / traffic_factor, 2)
            routes.append({"vehicle_id": vehicle_id, "stops": route_list, "distance_km": distance_km, "load": route_load})
            total_distance_m += route_distance_m

    optimized_km = round(total_distance_m / 1000.0 / traffic_factor, 2)
    baseline_km = nearest_neighbor_baseline(depot_coords, stops_coords)
    saved_km = round(baseline_km - optimized_km, 2)
    improvement_pct = round(saved_km / baseline_km * 100, 2) if baseline_km else 0.0
    return {
        "status": "Feasible solution found",
        "total_distance_km": optimized_km,
        "baseline_distance_km": baseline_km,
        "saved_distance_km": saved_km,
        "efficiency_improvement_pct": improvement_pct,
        "routes": routes,
    }
