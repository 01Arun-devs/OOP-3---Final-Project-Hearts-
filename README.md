# OOP-3---Final-Project-Hearts-

# ♥ Hearts Card Game

A fully playable Hearts card game built in Python using Object-Oriented Programming principles.  
Play as 1 human player against 3 AI opponents — with animations, real card images, and persistent stats.

---

## 👥 Team Members

| Name | Role |
|------|------|
| Jeel Suthar | OOP Structure — Card, Deck, Player base classes |
| Rudra Chauhan | Game Rules — Rule enforcement, scoring |
| Sujay Tailor | AI Logic — Basic AI & Smart AI |
| Arun Kumar | Integration — Game flow, controller, logging |
| Darsh Patel | GUI — Interface, animations, visuals |

---

## 📖 Overview

Hearts is a classic 4-player trick-taking card game.  
The goal is to finish with the **lowest score** by avoiding penalty cards:

- ♥ Hearts = 1 point each  
- ♠ Queen of Spades = 5 points  

The game ends when a player reaches the score limit (50 or 100), and the player with the lowest score wins.

This version includes a graphical interface, animations, and intelligent AI players.

---

## ✨ Features

- Standard 52-card deck with real card images  
- 1 human player vs 3 AI opponents  
- Shuffle & deal animations  
- Card play animations (fly & flip)  
- Trick winner animations  
- Two AI types:
  - Basic defensive AI  
  - Smart AI (Shoot the Moon strategy)  
- Full rule enforcement:
  - Must follow suit  
  - Hearts breaking rule  
- Shoot the Moon support  
- Score limit options (50 or 100)  
- Player name input  
- Rotating dealer system  
- Pause / Resume gameplay  
- Live scoreboard & move log  
- Persistent statistics (JSON)  
- Full game logging (text file)

---

## 🛠 Technologies Used

- **Language:** Python 3.8+  
- **GUI:** tkinter  
- **Images:** Pillow (PIL)  
- **Data Storage:** JSON + text files  

### OOP Concepts Used

- Encapsulation  
- Inheritance  
- Polymorphism  
- Composition  
- Abstraction  

---

## 🚀 Getting Started

### Prerequisites

Make sure Python 3.8+ is installed.

Install required library:
```bash
pip install Pillow

▶️ Run the Game
Clone or download the project
Ensure all files are in the same folder:
main.py
gui.py
logic.py
player.py
deck.py
card.py
Open terminal in that folder
Run:
python main.py

👉 The cards/ folder will be created automatically on first run.

📁 Project Structure
hearts_final/
│
├── main.py        # Entry point
├── card.py        # Card class
├── deck.py        # Deck logic
├── player.py      # Player + AI classes
├── logic.py       # Game controller
├── gui.py         # Interface & animations
│
├── cards/         # Auto-generated images
├── game_log.txt   # Game logs
└── scores.json    # Player stats
🎮 How the Game Works
Enter your name and choose score limit
Cards are shuffled and dealt (13 each)
Player with 2♣ starts first
Players must follow suit if possible
Highest card of lead suit wins the trick
Hearts cannot be played until broken
After 13 tricks:
Hearts = 1 point
Queen of Spades = 5 points
Shoot the Moon:
Collect all penalty cards → you get 0
Others get +18
Game continues until score limit reached
Lowest score wins
🤖 AI Players
Player	Strategy
AI 1	Defensive — avoids points
AI 2	Smart AI — attempts Shoot the Moon
AI 3	Defensive — similar to AI 1
⌨️ Keyboard Shortcuts
Key	Action
Enter	Play first valid card
Space	Pause / Resume
Esc	Quit game
📊 Statistics & Logging
Stored in scores.json
Total games played
Wins & losses
Best (lowest) score
Stored in game_log.txt
Game start time
Cards dealt
Each move
Trick winners
Final scores
🔮 Future Enhancements
Card passing (official Hearts rule)
Sound effects
More AI difficulty levels
Online multiplayer
Custom themes
🎓 Course

COSC2200 — Object Oriented Programming 3
Durham College — Group 2


