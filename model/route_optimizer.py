"""
model/route_optimizer.py
------------------------
Uses Google OR-Tools to solve the Vehicle Routing Problem (VRP).
Given a depot and a list of requested deliveries, it finds the optimal
route minimizing total distance.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import haversine as hs
import numpy as np


def create_data_model(depot_coords, stops_coords, num_vehicles=1):
    """
    Creates the payload for the OR-Tools solver.
    """
    data = {}
    # Combine depot (index 0) with stops
    locations = [depot_coords] + stops_coords
    
    # Compute Haversine distance matrix (in meters)
    n = len(locations)
    dist_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i != j:
                # haversine expects (lat, lon)
                d_km = hs.haversine(locations[i], locations[j])
                dist_matrix[i][j] = int(d_km * 1000)
    
    data['distance_matrix'] = dist_matrix.tolist()
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    return data, locations


def solve_vrp(depot_coords, stops_coords, num_vehicles=1):
    """
    Solves the VRP and returns the ordered route(s).
    """
    data, locations = create_data_model(depot_coords, stops_coords, num_vehicles)

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(2)

    # Solve
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {"error": "No solution found."}

    # Extract routes
    routes = []
    total_distance = 0
    
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_list = []
        route_dist = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            # Add metadata for the UI Map
            lat, lon = locations[node_index]
            stop_type = "Depot" if node_index == 0 else f"Stop {node_index}"
            
            route_list.append({
                "node": node_index,
                "label": stop_type,
                "lat": lat,
                "lon": lon
            })
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_dist += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        
        # Add return to depot
        node_index = manager.IndexToNode(index)
        lat, lon = locations[node_index]
        route_list.append({
            "node": node_index,
            "label": "Depot (Return)",
            "lat": lat,
            "lon": lon
        })
        
        routes.append({
            "vehicle_id": vehicle_id,
            "stops": route_list,
            "distance_km": round((route_dist / 1000.0), 2)
        })
        total_distance += route_dist
        
    return {
        "status": "Optimal",
        "total_distance_km": round(total_distance / 1000.0, 2),
        "routes": routes
    }
