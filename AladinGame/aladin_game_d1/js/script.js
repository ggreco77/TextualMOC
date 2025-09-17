
let aladin;
let cursorInMOC = false; // Track if the cursor is inside the MOC region
let soundsEnabled = false; // Variable to control if sounds are enabled
let moc; // This will hold the MOC data without text
let mocText = ''; // This will hold the MOC text

const popup = document.getElementById('popup');
const aladinContainer = document.getElementById('aladin-lite-div');
const enterSound = document.getElementById('enter-sound');
const exitSound = document.getElementById('exit-sound');
const soundToggle = document.getElementById('sound-toggle');

// Function to process a MOC object containing text and other data
function processMOCWithText(mocWithText) {
    const mocData = {};
    // Extract text and data separately from the MOC object
    for (const key in mocWithText) {
        if (key === 'text') {
            mocText = mocWithText[key]; // Store the text separately
        } else {
            mocData[key] = mocWithText[key]; // Store the other data in mocData
        }
    }
    return mocData;
}

// Function to toggle sound effects on or off
function toggleSounds() {
    soundsEnabled = !soundsEnabled;
    soundToggle.textContent = soundsEnabled ? "Disable Sounds" : "Enable Sounds"; // Update button text
}

// Add event listener to toggle sound on button click
soundToggle.addEventListener('click', toggleSounds);

// Initialize the Aladin Lite viewer
A.init.then(() => {
    aladin = A.aladin('#aladin-lite-div', { target: 'LMC', fov: 35 }); // Create the Aladin instance

    // Load MOC data from an external JSON file
    fetch('moc/mocData.json')
    .then(response => response.json())
    .then(moc_with_text => {
        // Process the MOC to separate area data and text
        const mocData = processMOCWithText(moc_with_text);

        // Create the MOC object for Aladin with specified appearance settings
        moc = A.MOCFromJSON(mocData, { opacity: 0.45, color: 'magenta', lineWidth: 1, fill: true, perimeter: true});
        aladin.addMOC(moc);

        // Handle mouse movement events to detect when the cursor enters or leaves the MOC region
        aladin.on('mouseMove', function (pos) {
            if (!pos) return; // If no position data is available, exit the function

            // Check if the cursor is within the MOC region
            let isInMOC = moc.contains(pos.ra, pos.dec);

            if (isInMOC && !cursorInMOC) {
                // When entering the MOC region
                console.log('Cursor entered the MOC region');
                cursorInMOC = true; // Update state
                popup.style.display = 'block'; // Show the popup
                popup.textContent = mocText; // Update the popup with the MOC text

                // Play entry sound if sounds are enabled
                if (soundsEnabled) {
                    enterSound.play().catch(error => console.log("Error playing entry sound: ", error));
                }
            } else if (!isInMOC && cursorInMOC) {
                // When leaving the MOC region
                console.log('Cursor left the MOC region');
                cursorInMOC = false; // Update state
                popup.style.display = 'none'; // Hide the popup

                // Play exit sound if sounds are enabled
                if (soundsEnabled) {
                    exitSound.play().catch(error => console.log("Error playing exit sound: ", error));
                }
            }
        });
    });
});
