import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging

game = hlt.Game()

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("sentdexbot")

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

ship_states = {}

while True:
    game.update_frame()

    me = game.me
    game_map = game.game_map

    command_queue = []

    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

    position_choices = []

    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "collecting"

    for ship in me.get_ships():

        # Spits out map cords for N,S,E,W, and ship position
        # Example: [Position(19, 9), Position(19, 11), Position(20, 10), Position(18, 10), Position(19, 10)]
        position_options =  ship.position.get_surrounding_cardinals() + [ship.position]

        # Stores the movement options mapped to actual map cord
        # Example:{(0, -1): Position(29, 6), (0, 1): Position(29, 8), (1, 0): Position(30, 7), (-1, 0): Position(28, 7), (0, 0): Position(29, 7)} 
        position_dict = {}

        for n, direction in enumerate(direction_order):
            position_dict[direction] = position_options[n]

        # Use directional offset to calculate map position from current position and cardinal direction?  Yeah, probably a good idea.
        # logging.info(position_dict)
        # logging.info(ship.position.directional_offset(Direction.North))

        # Stores amount of halite from the surrounding movement options {(0,1): 500}
        halite_dict = {}
       
        for direction in position_dict:
            position = position_dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_dict[direction] not in position_choices:
                if direction == Direction.Still:
                    halite_dict[direction] = halite_amount * 3
                else:
                    halite_dict[direction] = halite_amount
        logging.info(halite_dict)

        #Here is where shit gets sketchy.  Set roles?    
        if ship_states[ship.id] == "depositing":
            move = game_map.naive_navigate(ship, me.shipyard.position)
            position_choices.append(position_dict[move])
            command_queue.append(ship.move(move))

            if move == Direction.Still:
                ship_states[ship.id] = "collecting"
        
        elif ship_states[ship.id] == "collecting":
            directional_choice = max(halite_dict, key=halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            command_queue.append(ship.move(game_map.naive_navigate(ship, position_dict[directional_choice])))

            if ship.halite_amount > constants.MAX_HALITE * .95:
                ship_states[ship.id] = "depositing"



    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

