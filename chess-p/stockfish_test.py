import subprocess
import time
import os

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Stockfish path
stockfish_path = r"c:\Users\spsuh\Desktop\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
print(f"Stockfish path: {stockfish_path}")

# Check if file exists
if os.path.isfile(stockfish_path):
    print("Stockfish executable found!")
else:
    print("Stockfish executable not found!")

class Stockfish:
    def __init__(self, path):
        self.process = subprocess.Popen(
            path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def send_command(self, command):
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()

    def get_best_move(self, fen, depth=10):
        self.send_command(f"position fen {fen}")
        self.send_command(f"go depth {depth}")
        
        while True:
            output = self.process.stdout.readline().strip()
            if output.startswith("bestmove"):
                return output.split()[1]

# Create Stockfish instance
try:
    engine = Stockfish(stockfish_path)
    print("Stockfish engine initialized successfully.")
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    exit(1)

# Test with a simple position (starting position)
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

print("Analyzing starting position...")
try:
    best_move = engine.get_best_move(fen)
    print(f"Best move: {best_move}")
except Exception as e:
    print(f"Error getting best move: {e}")

# Close the Stockfish process
engine.process.terminate()
print("Stockfish process terminated.")