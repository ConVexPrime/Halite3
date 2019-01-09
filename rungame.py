import os
import secrets

map_sizes = [32, 40, 48, 56, 64]

while True:
  map_choice = secrets.choice(map_sizes)
  commands = [f'halite.exe --replay-directory replays/ -vvv --width {map_choice} --height {map_choice} "python ConvexBot-Random.py" "python ConvexBot-Random.py" "python ConvexBot5.py" "python ConvexBot-Random.py"',
              f'halite.exe --replay-directory replays/ -vvv --width {map_choice} --height {map_choice} "python ConvexBot5.py" "python ConvexBot-Random.py"']

  command = secrets.choice(commands)
  os.system(command)
