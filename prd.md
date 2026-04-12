PRD: Project "Cipher"

Version: 1.0

Theme: Vintage Logic / Information Theory

Base Color: #F3E5AB (Parchment)
1. Product Vision

A high-stakes, competitive 4-digit logic game where a user races against a mathematically perfect AI. The game emphasizes the beauty of Information Theory and provides a tactile, "analog" digital experience.
2. Core Game Rules

    The Secret: A unique 4-digit sequence (0-9), no repeats.

    The Feedback: Each guess generates 4 color-coded blocks:

        Green: Correct digit, correct position.

        Yellow: Correct digit, wrong position.

        Red: Digit not present in the secret.

    The Constraint: Feedback is non-positional (the order of color blocks does not match the order of the digits).

3. Technical Features & Requirements
A. The AI Engine (The Opponent)

    Algorithm: Must implement a Minimax or Maximum Entropy solver.

    Efficiency: The AI must aim for the theoretical minimum moves (typically solving within 4–6 guesses).

    Integrity: The AI operates in a "shadow" state. It only receives the same color feedback the user does; it never "sees" the secret number directly.

B. User Interface (UI) & Experience (UX)

    Aesthetic: "Analog Notebook." Textured parchment background (#F3E5AB).

    Landing Page: Simple, centered "START GAME" button in a typewriter font.

    Input Method: Four horizontal underlines (_ _ _ _). User types digits to fill them.

    Session History: * A vertical list of previous guesses.

        Each row: [Digits] | [4 Color Blocks].

        Viewport: Always show the current input and the last 5 guesses. Older guesses move into a scrollable area.

C. The "Reveal" & AI Agent

    Trigger: The game ends immediately when the user finds the secret.

    Side-by-Side Comparison: Show the user's path vs. the AI’s path.

    Agent Analysis: A dedicated section where the AI explains its "thought process" for every move:

        Show "Search Space Reduction" (e.g., 5,040 possibilities → 120).

        Explain the logic behind the "Best Guess" (Entropy gain).

4. Functional Flow

    Start: System generates a secret. User enters "Race Mode."

    Gameplay: User submits guesses. System records both User and AI attempts (AI progress is hidden).

    Endgame: User hits 4 Green blocks.

    Analysis: The screen transitions to the dual-view "Solution Path" with the AI Agent explanation module.

5. Tech Stack Recommendation

    Frontend/Backend: Streamlit (for rapid Python prototyping) or React + Tailwind CSS (for a polished web feel).

    Logic: Python (for the heavy lifting of permutations and entropy calculations).

6. Final Design Directives

    Colors: Use #F3E5AB for background; #10B981 (Green), #FBBF24 (Yellow), #EF4444 (Red) for feedback blocks.

    Animation: Use a subtle fade-in for the AI’s logic path to make the reveal feel like a "unveiling" of a mystery.