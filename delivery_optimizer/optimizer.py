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
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [config.VEHICLE_CAPACITY] * config.NUM_VEHICLES,  # vehicle maximum capacities
            True,  # start cumul to zero
            "Capacity"
        )
        
        # --- Time Dimension ---
        # We reuse the time callback from step 3
        self.routing.AddDimension(
            transit_callback_index,
            30 * 60,  # allow waiting time (30 mins slack)
            24 * 60 * 60,  # maximum time per vehicle (24 hours)
            False,  # Don't force start cumul to zero
            "Time"
        )
        time_dimension = self.routing.GetDimensionOrDie("Time")
        
        # Add Time Window Constraints (Mocking some windows)
        # For this MVP, we'll assign a loose window to all, 
        # but tighter for high priority just to show logic, or keep it open.
        # User asked for "TimeWindow constraints for at least 2 stops"
        
        for i, row in self.df.iterrows():
            if i == 0: continue # Skip depot constraints for now
            
            # Mocking windows: 
            # Stops with even index: Morning (08:00 - 12:00) 
            # Stops with odd index: Afternoon (12:00 - 18:00)
            # Time in seconds since start (0).
            
            if i % 2 == 0: 
                # e.g., Must be visited between 30 mins and 4 hours
                start = 1800 
                end = 14400 
            else:
                # e.g., Must be visited between 1 hour and 6 hours
                start = 3600
                end = 21600
                
            index = self.manager.NodeToIndex(i)
            time_dimension.CumulVar(index).SetRange(start, end)

        # 5. Priority Penalty (Cost component 3)
        # We allow dropping nodes if infeasible (or too expensive), 
        # but apply penalty = Base * Priority * Weight
        
        # Base penalty for dropping any node (should be > max path cost to discourage dropping unless necessary)
        # If Capacity is 15 and we generate demand 1-4 for 10 stops, total demand ~25. 
        # So drops ARE inevitable with 1 vehicle.
        
        penalty_base = 100000 
        
        for i, row in self.df.iterrows():
            if i == 0: continue 
            index = self.manager.NodeToIndex(i)
            # The prompt requested: (PriorityPenalty * w3)
            # We interpret this as: Cost includes penalty for unvisited nodes.
            # Penalty = w3 * PriorityFactor * Base
            
            p_val = row['priority'] # 1, 2, 3
            penalty = int(config.WEIGHT_PRIORITY * p_val * penalty_base)
            self.routing.AddDisjunction([index], penalty)

        # 6. Solve
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = 10 # 10s timeout
        
        self.solution = self.routing.SolveWithParameters(search_parameters)
        return self.solution

    def print_solution(self):
        """Prints solution on console."""
        if not self.solution:
            logger.warning("No solution found!")
            return None

        total_distance = 0
        total_time = 0
        routes = []

        print(f"Objective: {self.solution.ObjectiveValue()}")
        
        # Dropped nodes
        dropped_nodes = []
        for node in range(self.routing.Size()):
            if self.routing.IsStart(node) or self.routing.IsEnd(node):
                continue
            if self.solution.Value(self.routing.NextVar(node)) == node:
                dropped_nodes.append(node)
        
        if dropped_nodes:
            print(f"Dropped nodes: {dropped_nodes}")

        for vehicle_id in range(config.NUM_VEHICLES):
            index = self.routing.Start(vehicle_id)
            plan_output = f"Route for vehicle {vehicle_id}:\n"
            route_dist = 0
            route_time = 0
            route_sequence = []
            
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                route_sequence.append(node_index)
                
                # Get time var
                time_var = self.routing.GetDimensionOrDie("Time").CumulVar(index)
                plan_output += f" {node_index} Time({self.solution.Min(time_var)},{self.solution.Max(time_var)}) -> "
                
                previous_index = index
                index = self.solution.Value(self.routing.NextVar(index))
                
                # Metrics
                # Note: matrix is [node][node], but index is routing index. 
                # Need conversion for lookups if not using callback logic internally.
                # However, callbacks already used dist/time matrices.
                from_node = self.manager.IndexToNode(previous_index)
                to_node = self.manager.IndexToNode(index)
                
                route_dist += self.dist_matrix[from_node][to_node]
                route_time += self.time_matrix[from_node][to_node]

            node_index = self.manager.IndexToNode(index)
            route_sequence.append(node_index)
            
            time_var = self.routing.GetDimensionOrDie("Time").CumulVar(index)
            plan_output += f"{node_index} Time({self.solution.Min(time_var)},{self.solution.Max(time_var)})\n"
            
            plan_output += f"Distance of the route: {route_dist}m\n"
            plan_output += f"Time of the route: {route_time}s\n"
            
            print(plan_output)
            
            total_distance += route_dist
            total_time += route_time
            
            routes.append({
                "vehicle": vehicle_id,
                "sequence": route_sequence,
                "distance": route_dist,
                "time": route_time
            })

        print(f"Total Distance of all routes: {total_distance}m")
        print(f"Total Time of all routes: {total_time}s")
        return routes
