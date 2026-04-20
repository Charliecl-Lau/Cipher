# Cipher

A high-stakes, competitive 4-digit logic game where human intuition races against a mathematically perfect Information Theory algorithm. Built with a tactile, vintage "ledger and ink" aesthetic.

---

## The Concept

Cipher is a modern implementation of the classic **Bulls and Cows** game. Each player (and the AI) starts with a random 4-digit secret. Your goal is to decode the secret in the fewest moves possible.

The twist? While you are using logic and memory, the AI is calculating the **Shannon Entropy** of every possible move to systematically dismantle a search space of **5,040 permutations**.

---

## Visual Identity: "Digital Vintage"

The UI is designed to feel like a physical desk.

| Element | Description |
|---|---|
| **The Ledger** | Results are displayed in a two-page open logbook |
| **The Memo Pad** | Active gameplay takes place on a wrinkled piece of memo paper held by masking tape |
| **The Ink** | Every digit and block is rendered in a hand-drawn, watercolor-ink style |

**Feedback Blocks** (non-positional color indicators):

- 🟩 **Green** — Correct digit, correct position
- 🟨 **Yellow** — Correct digit, incorrect position
- 🟥 **Red** — Digit not present in the code

---

## The AI: "The Entropy Agent"

The core solver uses a **Minimax Algorithm** rooted in Information Theory:

1. **Possibility Mapping** — The AI maintains a list of all 5,040 valid permutations.
2. **Entropy Calculation** — For every potential guess, the AI simulates all possible feedback outcomes (combinations of Green/Yellow/Red) and calculates how much each would narrow down the remaining possibilities.
3. **Maximized Gain** — The AI selects the guess that guarantees the largest reduction in the search space, even in the worst-case scenario.

---

## Getting Started

### Prerequisites

- Python 3.8+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Charliecl-Lau/Cipher.git
   cd Cipher
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

   If `streamlit` is not on your PATH (common on Windows), use:
   ```bash
   python -m streamlit run app.py --server.headless true
   ```

   The app will be available at **http://localhost:8501**.

---

## Project Structure

```
Cipher/
├── app.py              # Main Streamlit application and UI logic
├── cipher_engine.py    # Minimax/Entropy AI logic
├── image/              # Custom UI assets (parchment, paint, memo textures)
├── requirements.txt    # Project dependencies
└── README.md           # You are here
```

---

## How to Play

1. **Landing** — Click `START GAME` on the parchment landing page.
2. **Mission Briefing** — A dialog explains the rules and colour feedback system. Click `Start` to begin.
3. **Game** — Enter your guess using the 4-box digit grid. Each box accepts one unique digit; press `Enter` or click `SUBMIT` after filling all four.
4. **Feedback** — Each guess shows colour blocks indicating how close you were. The AI makes its own guess simultaneously behind the scenes.
5. **Result** — Once you crack the code, the ledger opens to reveal the outcome (win or loss), the AI's full solution path, and a step-by-step entropy explanation for every move the AI made. Click `PLAY AGAIN` to start a new round.
