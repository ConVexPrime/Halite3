import hlt
from hlt import constants
from hlt.positionals import Direction
import random
from random import randint
import logging
from hlt.positionals import Position
import math

class Grid:
    """
    Class for creating grids around a center to point.
    """
    def __init__(self, center_point, grid_size, game_map, show_depleted_at=500):
        self.center_point = center_point
        self.grid_size = grid_size
        self.game_map = game_map
        self.show_depleted_at = show_depleted_at
        self.grid = self.update_grid()
        self.total_halite = self.total_grid_halite()

    def update_grid(self):
        the_grid = []
        for y in range (-1 * self.grid_size, self.grid_size + 1):
            grid_row = []
            for x in range (-1 * self.grid_size, self.grid_size + 1):
                grid_cell = Position(x, y) + self.center_point
                grid_row.append(grid_cell)
            the_grid.append(grid_row)
        return the_grid

    def total_grid_halite(self):
        h = 0
        for r in self.grid:
            for c in r:
                h += self.game_map[c].halite_amount
        return h

    def depleted(self):
        if self.total_halite < self.show_depleted_at:
            return True
        else:
            return False

    def __repr__(self):
        return repr(self.grid)

class SmartNavigate:
    """
    Smart Navigate.  The name pretty much sums it up.
    """
    def __init__(self, game_map):
        self.game_map = game_map
        self.casters = {}
        self.depositers = {}
        self.collectors = {}
        self.moves = []
        self.direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
        self.can_not_move = {}
        self.commands = []

    def collect(self, ship):
        # For each ship: Stores surrounding moves, halite at each move, and map position of each move.
        # Example: {Ship(id=0, Position(20, 19), cargo=105 halite): [(2270, (0, 0), Position(20, 19)), (294, (0, 1), Position(20, 19)), (225, (0, -1), Position(20, 19)), (208, (-1, 0), Position(20, 19)), (152, (1, 0), Position(20, 19))]}
        position_dict = self.get_position_dict(ship)
        all_moves = []
        for direction in position_dict:
            position = position_dict[direction]
            # Inflate the amount of halite at the current position to prevent the ships being "jumpy"
            if direction == (0, 0):
                # TODO hard coded number.  Ewwww
                if (self.game_map[position].halite_amount) > 50:
                    all_moves.append((self.game_map[position].halite_amount * 1000, direction, position))
                else:
                    all_moves.append((self.game_map[position].halite_amount, direction, position))
            else:
                all_moves.append((self.game_map[position].halite_amount, direction, position))

        self.collectors[ship] = sorted(all_moves, reverse=True)
        logging.info(f"Collectors: {self.collectors}")
        
    def deposit(self, ship, destination):
        # Sets a ship to deposit with a destination, just added to the list for now.  Calculated later.
        self.depositers[ship] = self.get_moves(ship, destination)

    def cast(self, ship, destination):
        # Casts a ship to a collect point, just added to the list for now.  Calculated later.
        self.casters[ship] = self.get_moves(ship, destination)

    def commit(self):
        # Calculate the best move for each list of roles and append them to the command queue
        # 3 different dicts allows the different roles to be prioritized.
        # The best priority (probably) is casters, depositers, collectors.

        logging.info(f"Casters: {self.casters}")
        self.get_best_move(self.casters, "CAST")

        logging.info(f"Depositers: {self.depositers}")
        self.get_best_move(self.depositers, "DEPOSIT")
        
        logging.info(f"Collectors: {self.collectors}")
        self.get_best_move(self.collectors, "COLLECT")

        return self.commands
    
    def valid_move(self, position):
        logging.info(f"moves: {self.moves}")
        logging.info(f"can't move: {self.can_not_move}")
        if str(position) not in self.moves:
            for ship in self.can_not_move:
                if self.can_not_move[ship] in str(position):
                    return False
            return True
        else:
            return False

    def get_position_dict(self, ship):
        # Map cords for N,S,E,W, and ship position
        # [Position(19, 9), Position(19, 11), Position(20, 10), Position(18, 10), Position(19, 10)]
        position_options =  ship.position.get_surrounding_cardinals() + [ship.position]
        # Position options mapped to actual map cord
        # {(0, -1): Position(29, 6), (0, 1): Position(29, 8), (1, 0): Position(30, 7), (-1, 0): Position(28, 7), (0, 0): Position(29, 7)} 
        position_dict = {}
        for n, direction in enumerate(self.direction_order):
            position_dict[direction] = position_options[n]
        return position_dict

    def get_moves(self, ship, destination):
        #Get a list of all possible moves, which contains another list of that moves distance to the target, the move itself, and that moves position
        #[((0, -1), 16, Position(21, 20)), ((0, 1), 18, Position(21, 22)), ((1, 0), 18, Position(22, 21)), ((-1, 0), 18, Position(20, 21)), ((0, 0), 17, Position(21, 21))]
        possible_moves = self.get_position_dict(ship)
        all_moves = []
        for move in possible_moves:
            distance = game_map.calculate_distance(possible_moves[move], destination)
            all_moves.append((distance, move, possible_moves[move]))
        return sorted(all_moves)
    
    def get_best_move(self, move_dict, description):
        for ship in move_dict:
            if ship.id in self.can_not_move:
                #Can't move
                self.commands.append(f'm {ship.id} o')
                self.moves.append(str(ship.position))
                continue
            for i in range(len(move_dict[ship])):
                if self.valid_move(move_dict[ship][i][2]):
                    logging.info(f"VALID MOVE {description} Ship ID: {ship.id} H/M/P: {move_dict[ship][i]}")
                    self.moves.append(str(move_dict[ship][i][2]))
                    direction = Direction.convert(move_dict[ship][i][1])
                    self.commands.append(f'm {ship.id} {direction}')
                    break
                else:
                    logging.info(f"INVALID MOVE {description} Ship ID: {ship.id} H/M/P: {move_dict[ship][i]}")

    def out_of_halite(self, ship):
        #Move: North, South, East, West	Cost: 10% of halite available at turn origin cell is deducted from ship’s current halite.
        if ship.halite_amount >= (int(self.game_map[ship.position].halite_amount * .1)):
            #ship can move
            pass
        else:
            #ship can't move
            self.can_not_move[ship.id] = str(ship.position)
            logging.info(f"{ship.id} has {ship.halite_amount} halite.  {int(self.game_map[ship.position].halite_amount * .1)} is required to move")
    
    def can_spawn(self, shipyardPosition):
        for m in range(len(self.moves)):
            if str(shipyardPosition) in self.moves[m]:
                return False
        return True

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game = hlt.Game()
game.ready("convex-rand")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))
dropoffs = 0
buildShips = True
buildDropoffs = False
returnPoint = game.me.shipyard.position
logging.info(f"Initial return point: {returnPoint}")
ship_returnpoint = {}
ship_states = {}
ship_castpoint = {}

#Magic Numbers
maxDropoffs = randint(0,3)
ratioThreshold = randint(4, 50)
maxShipBuildingTurn = randint((round(constants.MAX_TURNS * .3)), constants.MAX_TURNS)
minHaliteNeededForShipBuilding = randint(constants.SHIP_COST, (constants.SHIP_COST * 3))
percentOfMaxHaliteToTriggerDeposit = round((randint(1,10)/10), 2)
minDropoffBuildingHalite = randint(constants.DROPOFF_COST, (constants.DROPOFF_COST * randint(1, 4)))
minDistancefromShipyard = round(game.game_map.height / randint(3, 20))
grid_size = randint(1, 5)
depletion_limit = randint(500, 3000)

""" <<<Game Loop>>> """
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    the_grid = Grid(returnPoint, grid_size, game_map, depletion_limit)
    navigate = SmartNavigate(game_map)

    #Some checks for ships that just spawned.
    for ship in me.get_ships():

        #If a ship doesn't have a return point it must have just spawned, set it to the current return point.
        if ship.id not in ship_returnpoint:
            ship_returnpoint[ship.id] = returnPoint

        #If a ship doesn't have a state it must have just spawned, cast it.
        if ship.id not in ship_states:
            ship_states[ship.id] = "cast"
            #TODO get cast point from grid?
            x_t = me.shipyard.position.x + randint(-(grid_size), grid_size)
            y_t = ship_returnpoint[ship.id].y + randint(-(grid_size), grid_size)
            ship_castpoint[ship.id] = Position(x_t, y_t)

    for ship in me.get_ships():
        #Get a list of ships that can not move due to being low on halite.
        navigate.out_of_halite(ship)

        #Get the ship to dropoff ratio then use that to determine if we need to build ships or drop offs
        shipToDropoffRatio = len(me.get_ships()) / (len(me.get_dropoffs())+1)
        if shipToDropoffRatio < ratioThreshold:
            #we need to build ships
            buildShips = True
            buildDropoffs = False
        else:
            # we need to build dropoffs
            buildShips = False
            buildDropoffs = True
        
        #Is the ship depositing?
        if ship_states[ship.id] == "deposit":
            #Is the ship at the deposit point?  If so cast it out again.
            if ship.position == ship_returnpoint[ship.id]:
                ship_states[ship.id] = "cast"
                #TODO get cast point from grid?
                x_t = me.shipyard.position.x + randint(-(grid_size), grid_size)
                y_t = ship_returnpoint[ship.id].y + randint(-(grid_size), grid_size)
                ship_castpoint[ship.id] = Position(x_t, y_t)
            else:
                #If not at the deposit point, continue towards it.
                navigate.deposit(ship, ship_returnpoint[ship.id])

        #Is the ship casting?
        if ship_states[ship.id] == "cast":
            #Is the ship at the cast point?  If so, set it to collect.
            if ship.position == ship_castpoint[ship.id]:
                ship_states[ship.id] = "collect"
            else:
                #If not at the cast point, continue towards it.
                navigate.cast(ship, ship_castpoint[ship.id])

        #Is the ship collecting?
        if ship_states[ship.id] == "collect":
            #Is the ship full, if so set to deposit.
            if ship.halite_amount > constants.MAX_HALITE * percentOfMaxHaliteToTriggerDeposit:
                # Do we need to make a dropoff?
                grid_check = Grid(ship.position, grid_size, game_map)
                if (me.halite_amount > minDropoffBuildingHalite
                    and game_map.calculate_distance(ship.position, me.shipyard.position) > minDistancefromShipyard
                    and dropoffs < maxDropoffs
                    and not game_map[ship.position].has_structure
                    and buildDropoffs == True
                    and the_grid.depleted() == True
                    and grid_check.total_halite > 3000):
                        command_queue.append(ship.make_dropoff())
                        dropoffs += 1
                        buildDropoffs = False
                        returnPoint = ship.position
                else:
                    ship_states[ship.id] = "deposit"
                    navigate.deposit(ship, ship_returnpoint[ship.id])
            else:
                #TODO send them all home at the end of the game
                if (constants.MAX_TURNS - game.turn_number) < 25:
                    ship_states[ship.id] = "deposit"
                    navigate.deposit(ship, ship_returnpoint[ship.id])
                else:
                    #If not, continue collecting.
                    navigate.collect(ship)
    
    #commit moves from the smart nav class now, so we can the spawn point.
    to_submit = navigate.commit()

    #Do we need to spawn a ship?
    if (game.turn_number <= maxShipBuildingTurn 
        and me.halite_amount >= constants.SHIP_COST 
        and me.halite_amount > minHaliteNeededForShipBuilding
        and buildShips == True
        and not game_map[me.shipyard].is_occupied
        and navigate.can_spawn(str(me.shipyard.position))):
            command_queue.append(me.shipyard.spawn())
    
    # If the game is over
    if game.turn_number == constants.MAX_TURNS:
        # Get the results
        results = {}
        for player in game.players:
            results[player] = game.players[player].halite_amount
        # Determine if the bot won
        if max(results, key=results.get) == me.id:
            # if the bot did win, record the parameters it used.
            parameters = [len(game.players), game_map.width, maxDropoffs, maxShipBuildingTurn, minHaliteNeededForShipBuilding, percentOfMaxHaliteToTriggerDeposit, minDropoffBuildingHalite, minDistancefromShipyard, ratioThreshold, grid_size, depletion_limit]
            with open("random_bot_wins.txt", "a") as f:
                f.write(str(parameters) + "\n")
    
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue + to_submit)