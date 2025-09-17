
let aladin; // Aladin Lite instance
let cursorInMOC = false; // Flag to check if the cursor is in a MOC region
let gameStarted = false; // Flag to track if the game has started
let score = 0; // Player's score
let timeLeft = 30; // Game duration in seconds
let timerInterval; // Timer interval
const popup = document.getElementById('popup'); // Popup element for displaying messages
const aladinContainer = document.getElementById('aladin-lite-div'); // Container for the Aladin Lite viewer
const successSound = document.getElementById('success-sound'); // Sound for successful action
const errorSound = document.getElementById('error-sound'); // Sound for unsuccessful action
const startGameButton = document.getElementById('start-game'); // Start game button
const scoreDisplay = document.getElementById('score'); // Score display element
const timerDisplay = document.getElementById('timer'); // Timer display element
const gameStatusDisplay = document.getElementById('game-status'); // Game status display element
const countdownDisplay = document.getElementById('countdown'); // Countdown display element
const timeElement = document.getElementById('time'); // Time display element

successSound.volume = 1; // Set maximum volume for success sound
errorSound.volume = 1; // Set maximum volume for error sound

// Function to start the game
function startGame() {
    if (gameStarted) return;
    gameStarted = true;
    score = 0;
    timeLeft = 30;
    scoreDisplay.textContent = `Score: ${score}`;
    timerDisplay.style.color = 'white';
    timeElement.textContent = `${timeLeft}`;
    countdownDisplay.style.display = 'none'; // Hide countdown at the start
    gameStatusDisplay.textContent = "Game in progress...";
    startGameButton.disabled = true;

    // Start the timer
    timerInterval = setInterval(() => {
        timeLeft--;
        timeElement.textContent = timeLeft; // Update the element with the remaining time

        if (timeLeft <= 5) {
            timerDisplay.style.color = ''; // Change color of the timer
            countdownDisplay.textContent = timeLeft;
            countdownDisplay.style.display = 'block'; // Show the countdown in large font
        } else {
            timerDisplay.style.color = 'white';
            countdownDisplay.style.display = 'none'; // Hide the countdown
        }

        if (timeLeft <= 0) {
            endGame();
        }
    }, 1000);
}

// Function to end the game
function endGame(message = `Time's up! Final score: ${score}`) {
    clearInterval(timerInterval);
    gameStarted = false;
    startGameButton.disabled = false;
    gameStatusDisplay.textContent = message;
    countdownDisplay.style.display = 'none'; // Hide the countdown
}

let mocList = [];

// Load MOC data from mocDataList.json
fetch('moc/mocDataList.json')
.then(response => response.json())
.then(mocDataList => {

    A.init.then(() => {
        aladin = A.aladin('#aladin-lite-div', { target: 'Sgr', fov: 180 });

        // Create MOC at the same position in the sky
        mocList = mocDataList.map(moc_with_text => {
            const mocData = processMOCWithText(moc_with_text);
            const moc = A.MOCFromJSON(mocData, { opacity: 0.45, color: 'magenta', lineWidth: 1, fill: true, perimeter: true });
            aladin.addMOC(moc);
            return { moc, text: moc_with_text.text, isTarget: moc_with_text.isTarget };
        });

        // Handle mouse movement events
        aladin.on('mouseMove', function (pos) {
            if (!pos || !gameStarted) return;

            let found = false;
            mocList.forEach(item => {
                const isInMOC = item.moc.contains(pos.ra, pos.dec);

                if (isInMOC) {
                    found = true;
                    if (item.isTarget && !cursorInMOC) {
                        score += 10; // Only for the winning MOC
                        scoreDisplay.textContent = `Score: ${score}`;
                        popup.textContent = item.text;
                        popup.style.display = 'block'; // Show the popup
                        if (successSound) {
                            successSound.currentTime = 0;
                            successSound.play().catch(error => console.log("Error playing success sound: ", error));
                        }
                        endGame("Congratulations! You found the Large Magellanic Cloud!");
                    } else if (!item.isTarget && !cursorInMOC) {
                        popup.textContent = item.text; // Error message for non-winning MOC
                        popup.style.display = 'block';
                        if (errorSound) {
                            errorSound.currentTime = 0;
                            errorSound.play().catch(error => console.log("Error playing error sound: ", error));
                        }
                    }
                    cursorInMOC = true;
                }
            });

            if (!found && cursorInMOC) {
                cursorInMOC = false;
                popup.style.display = 'none'; // Hide the popup
            }
        });

        // Update the position of the popup based on mouse movement
        aladinContainer.addEventListener('mousemove', function (event) {
            if (cursorInMOC) {
                const rect = aladinContainer.getBoundingClientRect();
                popup.style.left = `${event.clientX - rect.left + 10}px`;
                popup.style.top = `${event.clientY - rect.top + 10}px`;
            }
        });
    });

    startGameButton.addEventListener('click', startGame);
});

// Function to process MOC with text
function processMOCWithText(mocWithText) {
    const mocData = {};
    for (const key in mocWithText) {
        if (key !== 'text' && key !== 'isTarget') {
            mocData[key] = mocWithText[key];
        }
    }
    return mocData;
}
