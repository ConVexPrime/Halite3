import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging
from hlt.positionals import Position
import math
from random import randint

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

    def best_halite_node(self):
        #TODO the best option for a ship to be casted to
        pass
    
    def claim_node(self):
        #TODO a ship has declared this as it's destination
        pass

    def taken_node(self):
        #TODO there is currently a ship at node
        pass

    def __repr__(self):
        return repr(self.grid)

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game = hlt.Game()
game.ready("convexrando")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))
ship_states = {}
dropoffs = 0
buildShips = True
buildDropoffs = False
returnPoint = game.me.shipyard.position
ship_returnpoint = {}

#Magic Numbers
maxDropoffs = randint(0,3)
maxShipBuildingTurn = randint((round(constants.MAX_TURNS * .3)), constants.MAX_TURNS)
minHaliteNeededForShipBuilding = randint(constants.SHIP_COST, (constants.SHIP_COST * 3))
percentOfMaxHaliteToTriggerDeposit = round((randint(1,10)/10), 2)
minDropoffBuildingHalite = randint(constants.DROPOFF_COST, (constants.DROPOFF_COST * randint(1, 4)))
minDistancefromShipyard = round(game.game_map.height / randint(3, 20)) #Fix this, it sucks
ratioThreshold = randint(4, 25)
grid_size = randint(1, 5)
depletion_limit = randint(500, 3000)

""" <<<Game Loop>>> """
while True:
    game.update_frame()

    me = game.me
    game_map = game.game_map
    command_queue = []
    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
    position_choices = []
    the_grid = Grid(returnPoint, grid_size, game_map, depletion_limit)

    #If a ship doesn't have a state it must have just spawned, set it to collect
    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "collect"

    #If a ship doesn't have a return point it must have just spawned, set it to the current return point.
    for ship in me.get_ships():
        if ship.id not in ship_returnpoint:
            ship_returnpoint[ship.id] = returnPoint

    for ship in me.get_ships():
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

        # Spits out map cords for N,S,E,W, and ship position
        # Example: [Position(19, 9), Position(19, 11), Position(20, 10), Position(18, 10), Position(19, 10)]
        position_options =  ship.position.get_surrounding_cardinals() + [ship.position]

        # Stores the movement options mapped to actual map cord
        # Example:{(0, -1): Position(29, 6), (0, 1): Position(29, 8), (1, 0): Position(30, 7), (-1, 0): Position(28, 7), (0, 0): Position(29, 7)} 
        position_dict = {}
        for n, direction in enumerate(direction_order):
            position_dict[direction] = position_options[n]

        # Stores amount of halite from the surrounding movement options
        # Example: {(0, -1): 206, (0, 1): 90, (1, 0): 173, (-1, 0): 144, (0, 0): 222}
        # An important part of this is that it checks position_choices.  If it's found to already be in 
        # there (becuase another ship has "claimed" this position choice already), it's not added.  This prevents collisions.
        halite_dict = {}
        for direction in position_dict:
            position = position_dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_dict[direction] not in position_choices:
                if direction == Direction.Still:
                    halite_dict[direction] = halite_amount * 3
                else:
                    halite_dict[direction] = halite_amount

        # Ship is enroute to deposit.  naive navigate to the shipyard.    
        if ship_states[ship.id] == "deposit":
            move = game_map.naive_navigate(ship, ship_returnpoint[ship.id])

            position_choices.append(position_dict[move])

            #Do we need to make a dropoff?
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
                command_queue.append(ship.move(move))

            # If the ship is still, then it must have reached the shipyard.  Set it back to collecting.
            # TODO There is a better way to do this.
            if move == Direction.Still:
                ship_states[ship.id] = "collect"

        # Ship is set to collect.  Move to the adjacent position with the most halite and collect.
        elif ship_states[ship.id] == "collect":
            directional_choice = max(halite_dict, key=halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            command_queue.append(ship.move(game_map.naive_navigate(ship, position_dict[directional_choice])))

            if ship.halite_amount > constants.MAX_HALITE * percentOfMaxHaliteToTriggerDeposit:
                ship_states[ship.id] = "deposit"

    #Do we need to spawn a ship?
    if (game.turn_number <= maxShipBuildingTurn 
        and me.halite_amount >= constants.SHIP_COST 
        and me.halite_amount > minHaliteNeededForShipBuilding
        and buildShips == True 
        and not game_map[me.shipyard].is_occupied): 
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
            parameters = [maxDropoffs, maxShipBuildingTurn, minHaliteNeededForShipBuilding, percentOfMaxHaliteToTriggerDeposit, minDropoffBuildingHalite, minDistancefromShipyard, ratioThreshold, grid_size, depletion_limit]
            with open("random_bot_wins.txt", "a") as f:
                f.write(str(parameters) + "\n")
    logging.info(command_queue)
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)