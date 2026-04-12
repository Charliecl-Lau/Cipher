UI Design & Interaction Guide: "Cipher"

This document provides a comprehensive set of UI instructions to give a frontend developer, ensuring the app perfectly matches the visual style and functional flow of your PRD.
UI Design & Interaction Guide: "Cipher-4"
1. Design Philosophy: "Digital Vintage"

The interface must blend the tactile feeling of analog logic puzzles (ledgers, typewriter print, chalkboards) with digital efficiency. It should feel like a secret tool used by mathematical spymasters.
Color Palette (Crucial)

    Base (Parchment): #F3E5AB (Used for ALL page backgrounds).

    Text (Ink): #2A1B0A (Deep, dark brown; use a handwritten or typewriter font).

    Grid Lines (Subtle): #E5D3A3 (Faint ledger or graph paper grid overlay).

    Feedback - Correct (Green): #10B981 (Emerald/Green; use a solid, slightly textured square block, not an icon).

    Feedback - Wrong Position (Yellow): #FBBF24 (Amber/Yellow; solid, textured block).

    Feedback - Not Present (Red): #EF4444 (Deep/Red; solid, textured block).

2. Functional Screens & Interaction Flow
A. Landing Page (The Entry)

    Viewport: Standard web page. The entire background is #F3E5AB.

    Elements: One large, centered, rectangular button.

    Style: Dark border, typewriter font text.

    Text: START GAME

    Interaction: Clicking "START GAME" fades the button out and immediately loads the "Session UI."

B. Session UI (The Race)

    Background: Seamless parchment texture (#F3E5AB) with subtle graph paper lines.

    Header: YOUR PROCESS (Handwritten style font, top center).

The Guess History Container (Scrollable Area)

    Position: Below the header, centered.

    Logic: This area displays a vertical list of the last 5 guesses.

    Row Structure: Each guess entry uses this specific format:

        [Underlined Guess: 0-1-2-3] <Gap> [Block 1] [Block 2] [Block 3] [Block 4]

    Scrolling: When guess #6 is entered, the top guess (#1) scrolls out of view. A subtle, styled vertical scroll bar must appear on the right side of this specific container.

The Guess Input (Prompts)

    Position: Fixed at the bottom of the Session UI (below the scrollable history).

    Input Prompt Text: Prompt your next 4-digit guess here: (Ink color, small font).

    Input Method (The Underlines): Below the prompt text, display exactly four distinct underscores (_ _ _ _).

        Interaction: When the user types a digit (0-9), the first underline is replaced by that digit (e.g., 3 _ _ _). Non-digits and repeating digits are ignored. When all four are filled (e.g., 3 7 1 9), the system auto-submits.

        Reset: After auto-submitting, the input resets to _ _ _ _.

C. The Reveal & AI Analysis (Endgame)

    Trigger: Activated immediately upon the user getting 4 Green blocks.

    Transition: The Session UI fades out, and the "Cipher-4 Ledger" opens.

Left Page: "AI AGENT SOLUTION PATH"

    Visual: Looks like a page from a physical ledger book (aged paper, #F3E5AB, horizontal ruled lines).

    Content: A vertical timeline of the AI’s actual guesses and feedback.

        1-2-3-4 [Block 1-4]

        5-6-7-8 [Block 1-4]
        ... and so on.

Right Page: "STEP-BY-STEP EXPLANATION"

    Visual: A companion parchment page, often including faint mathematical sketches (decision trees, set diagrams).

    Content: The AI Agent's detailed breakdown of its logic for each move shown on the left page.

    Example Callout: Guess 3 (1590): This guess... reduced the total possible combinations from 648 to just 87. (Ink text).

    Key Metrics: Highlight values like "Entropy Gain" or "Possibilities Left" using slightly bolder or italicized ink text.