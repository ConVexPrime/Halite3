import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging
from hlt.positionals import Position
import math

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game = hlt.Game()
game.ready("old convexbot")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ship_states = {}
dropoffs = 0
buildShips = True
buildDropoffs = False

#Magic Numbers
maxDropoffs = 3
maxShipBuildingTurn = 250
minHaliteNeededForShipBuilding = 1500
percentOfMaxHaliteToTriggerDeposit = .70
minDropoffBuildingTurn = 50
minDropoffBuildingHalite = 6500
minDistancefromShipyard = game.game_map.height / 6
ratioThreshold = 10

def calcDistance(theShip, theDropoff):
    # Distance between two points
    # Example: calcDistance(ship.position.x, ship.position.y, me.shipyard.position.x, me.shipyard.position.y)
    return math.hypot(theDropoff.x - theShip.x, theDropoff.y - theShip.y)

""" <<<Game Loop>>> """

while True:
    game.update_frame()

    me = game.me
    game_map = game.game_map
    command_queue = []
    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
    position_choices = []

    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "collect"

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

      #Find the closest drop off point
      returnPoint = me.shipyard.position
      returnDistance = calcDistance(ship.position, me.shipyard.position)
      for dropoff in me.get_dropoffs():
          # logging.info(f"{dropoff.id} - {dropoff.position} is {calcDistance(ship.position, dropoff.position)} away from {ship}.")
          if returnDistance > calcDistance(ship.position, dropoff.position):
              returnPoint = dropoff.position
              returnDistance =  calcDistance(ship.position, dropoff.position)
              # logging.info(f"Destination is {returnPoint}")

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
      # An important part of this is that it checks position_choices.  
      # If it's found to already be in there (becuase another ship has "claimed" this position choice already), it's not added.  
      # This prevents collisions.
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
          move = game_map.naive_navigate(ship, returnPoint)
          position_choices.append(position_dict[move])

          #Do we need to make a dropoff?
          if (game.turn_number > minDropoffBuildingTurn
              and me.halite_amount > minDropoffBuildingHalite
              and calcDistance(ship.position, me.shipyard.position) > minDistancefromShipyard
              and dropoffs < maxDropoffs
              and not game_map[ship.position].has_structure
              and buildDropoffs == True):
                  command_queue.append(ship.make_dropoff())
                  dropoffs += 1
                  buildDropoffs = False
                  # logging.info(f"Dropoffs:{dropoffs}")
          else:
              command_queue.append(ship.move(move))

          # If the ship is still, then it must have reached the shipyard.  Set it back to collecting.
          if move == Direction.Still:
              ship_states[ship.id] = "collect"
      
      # Ship is set to collect.  Move to the adjacent position with the most halite and collect.
      elif ship_states[ship.id] == "collect":
          directional_choice = max(halite_dict, key=halite_dict.get)
          position_choices.append(position_dict[directional_choice])
          command_queue.append(ship.move(game_map.naive_navigate(ship, position_dict[directional_choice])))

          if ship.halite_amount > constants.MAX_HALITE * percentOfMaxHaliteToTriggerDeposit:
              ship_states[ship.id] = "deposit"

    #Logging Stuff
    #ship to drop off ratio
    logging.info("Ship to dropoff ratio")
    logging.info(len(me.get_ships()) / (len(me.get_dropoffs())+1))
    logging.info(f"Build ships: {buildShips}")
    logging.info(f"Build Dropoffs: {buildDropoffs}")

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Only spawn a ship if you have over 2000 halite 11/17 0405
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if (game.turn_number <= maxShipBuildingTurn 
        and me.halite_amount >= constants.SHIP_COST 
        and me.halite_amount > minHaliteNeededForShipBuilding
        and buildShips == True 
        and not game_map[me.shipyard].is_occupied):
            command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)