from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import haversine as hs
import numpy as np

def create_data_model(depot_coords, stops_coords, num_vehicles=1, vehicle_capacities=None, demands=None, traffic_factor=1.0):
    data = {}
    locations = [depot_coords] + stops_coords
    n = len(locations)
    
    dist_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i != j:
                d_km = hs.haversine(locations[i], locations[j])
                dist_matrix[i][j] = int(d_km * 1000 * traffic_factor)
    
    data['distance_matrix'] = dist_matrix.tolist()
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    
    if demands is None:
        demands = [0] + [1] * len(stops_coords)
    data['demands'] = demands
    
    if vehicle_capacities is None:
        vehicle_capacities = [10] * num_vehicles
    data['vehicle_capacities'] = vehicle_capacities

    return data, locations

def solve_vrp(depot_coords, stops_coords, num_vehicles=1, vehicle_capacities=None, demands=None, traffic_factor=1.0):
    data, locations = create_data_model(depot_coords, stops_coords, num_vehicles, vehicle_capacities, demands, traffic_factor)

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  
        data['vehicle_capacities'],
        True,  
        'Capacity')

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(3)

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {"error": "No solution found. Check capacity constraints or input lengths."}

    routes = []
    total_distance = 0
    total_baseline = sum([int(hs.haversine(depot_coords, stop)*2000) for stop in stops_coords])  

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_list = []
        route_dist = 0
        route_load = 0
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            lat, lon = locations[node_index]
            
            stop_type = "Depot" if node_index == 0 else f"Stop {node_index} (Load: {data['demands'][node_index]})"
            
            route_list.append({
                "node": node_index,
                "label": stop_type,
                "lat": lat,
                "lon": lon
            })
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            if previous_index != index:
                route_dist += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        
        node_index = manager.IndexToNode(index)
        lat, lon = locations[node_index]
        route_list.append({
            "node": node_index,
            "label": "Depot (Return)",
            "lat": lat,
            "lon": lon
        })
        
        if len(route_list) > 2:
            km_dist = round((route_dist / 1000.0) / traffic_factor, 2)
            routes.append({
                "vehicle_id": vehicle_id,
                "stops": route_list,
                "distance_km": km_dist,
                "load": route_load
            })
            total_distance += route_dist
        
    baseline_km = round((total_baseline / 1000.0) / traffic_factor, 2)
    optimized_km = round((total_distance / 1000.0) / traffic_factor, 2)
    saved_km = round(baseline_km - optimized_km, 2)
    eff_pct = round((saved_km / baseline_km) * 100, 2) if baseline_km > 0 else 0
        
    return {
        "status": "Optimal",
        "total_distance_km": optimized_km,
        "baseline_distance_km": baseline_km,
        "saved_distance_km": saved_km,
        "efficiency_improvement_pct": eff_pct,
        "routes": routes
    }
