from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import config
import logging

logger = logging.getLogger(__name__)

class RouteOptimizer:
    def __init__(self, df_data, dist_matrix, time_matrix):
        """
        df_data: DataFrame with columns ['id', 'demand', 'priority']
        dist_matrix: Matrix of distances (meters)
        time_matrix: Matrix of travel times (seconds)
        """
        self.df = df_data
        self.dist_matrix = dist_matrix
        self.time_matrix = time_matrix
        self.manager = None
        self.routing = None
        self.solution = None
        
    def solve(self):
        # 1. Create the routing index manager.
        # We have N locations (0 is depot) and 1 vehicle.
        num_locations = len(self.df)
        self.manager = pywrapcp.RoutingIndexManager(
            num_locations, 
            config.NUM_VEHICLES, 
            config.DEPOT_INDEX
        )

        # 2. Create Routing Model.
        self.routing = pywrapcp.RoutingModel(self.manager)

        # 3. Create and register Transit Callbacks.
        
        # --- Time Callback ---
        def time_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            # Service time could be added here (e.g., 5 mins per stop)
            return int(self.time_matrix[from_node][to_node])

        transit_callback_index = self.routing.RegisterTransitCallback(time_callback)
        
        # Define cost of each arc. 
        # Cost = (Time * w1) + (Fuel/Dist * w2)
        # Note: OR-Tools ArcCost must be integer.
        
        def cost_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            
            time_val = self.time_matrix[from_node][to_node]
            dist_val = self.dist_matrix[from_node][to_node] # approximate fuel
            
            cost = (time_val * config.WEIGHT_TIME) + (dist_val * config.WEIGHT_FUEL)
            return int(cost)
            
        cost_callback_index = self.routing.RegisterTransitCallback(cost_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)

        # 4. Add Dimensions
        
        # --- Capacity Dimension ---
        def demand_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return int(self.df.iloc[from_node]['demand'])

        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)
        
        # Use capacities from vehicle profiles
        capacities = [p['capacity'] for p in config.VEHICLE_PROFILES]
        
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            capacities,  # vehicle-specific capacities
            True,  # start cumul to zero
            "Capacity"
        )
        
        # --- Time Dimension ---
        self.routing.AddDimension(
            transit_callback_index,
            30 * 60,  # allow waiting time
            24 * 60 * 60,  # maximum time
            False,
            "Time"
        )
        time_dimension = self.routing.GetDimensionOrDie("Time")
        time_dimension.SetGlobalSpanCostCoefficient(100)

        # 5. Vehicle-Specific Costs
        for vehicle_id in range(config.NUM_VEHICLES):
            profile = config.VEHICLE_PROFILES[vehicle_id]
            multiplier = profile['cost_multiplier']

            def vehicle_cost_callback(from_index, to_index, v_id=vehicle_id, m=multiplier):
                from_node = self.manager.IndexToNode(from_index)
                to_node = self.manager.IndexToNode(to_index)
                time_val = self.time_matrix[from_node][to_node]
                dist_val = self.dist_matrix[from_node][to_node]
                
                # Safe handling for infinity to avoid OverflowError
                if time_val == float('inf') or dist_val == float('inf'):
                    return 10**9 # Very high cost
                    
                cost = (time_val * config.WEIGHT_TIME + dist_val * config.WEIGHT_FUEL) * m
                return int(cost)

            v_callback_index = self.routing.RegisterTransitCallback(vehicle_cost_callback)
            self.routing.SetArcCostEvaluatorOfVehicle(v_callback_index, vehicle_id)

        # 6. Priority Penalty
        penalty_base = 100000 
        for i, row in self.df.iterrows():
            if i == 0: continue 
            index = self.manager.NodeToIndex(i)
            p_val = row['priority']
            penalty = int(config.WEIGHT_PRIORITY * p_val * penalty_base)
            self.routing.AddDisjunction([index], penalty)

        # 7. Solve
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
        )
        search_parameters.time_limit.seconds = 45
        
        self.solution = self.routing.SolveWithParameters(search_parameters)
        return self.solution

    def print_solution(self):
        """Prints solution and returns detailed route info."""
        if not self.solution:
            logger.warning("No solution found!")
            return None

        total_distance = 0
        total_time = 0
        routes = []

        print(f"Objective: {self.solution.ObjectiveValue()}")
        
        for vehicle_id in range(config.NUM_VEHICLES):
            profile = config.VEHICLE_PROFILES[vehicle_id]
            index = self.routing.Start(vehicle_id)
            plan_output = f"Route for vehicle {vehicle_id} ({profile['name']}):\n"
            route_dist = 0
            route_time = 0
            route_sequence = []
            
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                route_sequence.append(node_index)
                
                time_var = self.routing.GetDimensionOrDie("Time").CumulVar(index)
                plan_output += f" {node_index} Time({self.solution.Min(time_var)},{self.solution.Max(time_var)}) -> "
                
                previous_index = index
                index = self.solution.Value(self.routing.NextVar(index))
                
                from_node = self.manager.IndexToNode(previous_index)
                to_node = self.manager.IndexToNode(index)
                route_dist += self.dist_matrix[from_node][to_node]
                route_time += self.time_matrix[from_node][to_node]

            node_index = self.manager.IndexToNode(index)
            route_sequence.append(node_index)
            time_var = self.routing.GetDimensionOrDie("Time").CumulVar(index)
            plan_output += f"{node_index} Time({self.solution.Min(time_var)},{self.solution.Max(time_var)})\n"
            plan_output += f"Distance: {route_dist:.1f}m | Time: {route_time:.1f}s | Profile: {profile['name']}\n"
            
            print(plan_output)
            total_distance += route_dist
            total_time += route_time
            
            routes.append({
                "vehicle": vehicle_id,
                "vehicle_name": profile['name'],
                "sequence": route_sequence,
                "distance": route_dist,
                "time": route_time
            })

        print(f"Total Distance: {total_distance:.1f}m | Total Time: {total_time:.1f}s")
        return routes
