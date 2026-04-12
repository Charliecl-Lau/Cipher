Cipher

A high-stakes, competitive 4-digit logic game where human intuition races against a mathematically perfect Information Theory algorithm. Built with a tactile, vintage "ledger and ink" aesthetic.
📜 The Concept

Cipher is a modern implementation of the classic "Bulls and Cows" game. Each player (and the AI) starts with a random 4-digit secret. Your goal is to decode the secret in the fewest moves possible.

The twist? While you are using logic and memory, the AI is calculating the Shannon Entropy of every possible move to systematically dismantle the search space of 5,040 permutations.
🎨 Visual Identity: "Digital Vintage"

The UI is designed to feel like a physical desk.

    The Ledger: Results are displayed in a two-page open logbook.

    The Memo Pad: Active gameplay takes place on a wrinkled piece of memo paper held by masking tape.

    The Ink: Every digit and block is rendered in a hand-drawn, watercolor-ink style.

    Feedback Blocks: Non-positional color indicators:

        🟩 Green: Correct digit, correct position.

        🟨 Yellow: Correct digit, incorrect position.

        🟥 Red: Digit not present in the code.

🧠 The AI: "The Entropy Agent"

The core solver uses a Minimax Algorithm rooted in Information Theory:

    Possibility Mapping: The AI maintains a list of all 5,040 valid permutations.

    Entropy Calculation: For every potential guess, the AI simulates all possible feedback outcomes (combinations of Green/Yellow/Red) and calculates how much each would narrow down the remaining possibilities.

    Maximized Gain: The AI selects the guess that guarantees the largest reduction in the "search space," even in the worst-case scenario.

🚀 Getting Started
Prerequisites

    Python 3.8+

    Streamlit

Installation

    Clone the repository:
    Bash

    git clone https://github.com/[YOUR_USERNAME]/Cipher.git
    cd Cipher

    Install dependencies:
    Bash

    pip install -r requirements.txt

    Run the application:
    Bash

    streamlit run app.py

🛠 Project Structure
Plaintext

Cipher/
├── app.py              # Main Streamlit application and UI logic
├── solver.py           # The Minimax/Entropy AI logic
├── image/              # Custom UI assets (parchment, paint, memo textures)
├── requirements.txt    # Project dependencies
└── README.md           # You are here

📝 Instructions

    Start: Click "START GAME" to generate a secret code.

    Guess: Type 4 unique digits.

    Submit: Press Enter or click Submit.

    Compare: Once you solve the code, the AI Agent will reveal its solution path and explain the mathematical logic behind every move it made.
