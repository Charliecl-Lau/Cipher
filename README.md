# Cipher

**A high-stakes, competitive 4-digit logic game**  
*Where human intuition races against a mathematically perfect Information Theory algorithm.*

Built with a tactile, vintage "ledger and ink" aesthetic.

---

## 📜 The Concept

Cipher is a modern implementation of the classic **Bulls and Cows** game (also known as Mastermind with digits).

- Each player (and the AI) starts with a secret 4-digit code using **unique digits** (0–9).
- Your goal: decode the secret in the **fewest moves possible**.
- The twist? While you rely on logic and memory, the AI uses **Shannon Entropy** and a Minimax algorithm to systematically dismantle the 5,040 possible permutations.

---

## 🎨 Visual Identity: "Digital Vintage"

The entire UI is designed to feel like a real wooden desk from the 1940s:

- **The Ledger** — Results appear in a two-page open logbook.
- **The Memo Pad** — Gameplay happens on a wrinkled sheet of memo paper held down by masking tape.
- **The Ink** — Every digit and feedback block is rendered in hand-drawn, watercolor-ink style.
- **Feedback Blocks**:
  - 🟩 **Green** — Correct digit, correct position  
  - 🟨 **Yellow** — Correct digit, wrong position  
  - 🟥 **Red** — Digit not in the code

---

## 🧠 The AI: "The Entropy Agent"

The AI doesn’t just guess — it **thinks like a mathematician**.

- Maintains a live list of all 5,040 valid permutations.
- For every possible guess, it simulates **every possible feedback outcome**.
- Calculates the **Shannon Entropy** of each outcome to determine how much the search space shrinks.
- Always chooses the move that **guarantees the largest reduction** in possibilities — even in the worst-case scenario.

This makes the AI an unbeatable benchmark and a fascinating teacher of Information Theory.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Streamlit

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Charliecl-Lau/Cipher.git
cd Cipher

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the game
streamlit run app.py

📝 How to Play

Click START GAME — a new secret code is generated.
Enter a 4-digit guess with unique digits.
Press Enter or click Submit.
Study the feedback blocks and refine your next guess.
When you solve it, the Entropy Agent reveals its entire solution path with full mathematical explanations.
