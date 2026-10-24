const form = document.querySelector("#questionForm");
const message = document.querySelector("#message");
const chat = document.querySelector("#chat");
const send = document.querySelector("#send");
const errorBox = document.querySelector("#error");

const nameInput = document.querySelector("#name");
const levelInput = document.querySelector("#level");
const topicInput = document.querySelector("#topic");
const difficultyInput = document.querySelector("#difficulty");

let savedSettings = null;
try {
    savedSettings = JSON.parse(localStorage.getItem("boardTutorSettings") || "null");
} catch {
    savedSettings = null;
}

let mode = savedSettings?.mode || "Learn";
let attempts = 0;
let sentCount = 0;
let labelsCount = 0;

if (savedSettings) {
    nameInput.value = savedSettings.name || "Student";
    levelInput.value = savedSettings.level || "Class 8";
    topicInput.value = savedSettings.topic || "Linear equations";
    difficultyInput.value = savedSettings.difficulty || "Beginner";
}

function saveSettings() {
    const settings = {
        name: nameInput.value.trim() || "Student",
        level: levelInput.value,
        topic: topicInput.value.trim(),
        difficulty: difficultyInput.value,
        mode
    };
    localStorage.setItem("boardTutorSettings", JSON.stringify(settings));
}

function selectMode(selectedMode) {
    mode = selectedMode;
    document.querySelectorAll(".mode").forEach(button => {
        button.classList.toggle("active", button.dataset.mode === mode);
    });
    document.querySelector("#modeTitle").textContent = `${mode} mode`;
    message.placeholder = mode === "Quiz"
        ? "Start a quiz or submit your answers..."
        : mode === "Practice"
        ? "Ask for practice questions or submit your answer..."
        : "Ask a question or enter your answer...";
    saveSettings();
}

document.querySelectorAll(".mode").forEach(button => {
    button.addEventListener("click", () => selectMode(button.dataset.mode));
});

function addBubble(text, who, extraClass = "") {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${who} ${extraClass}`.trim();
    bubble.textContent = text;
    chat.appendChild(bubble);
    chat.scrollTop = chat.scrollHeight;
    return bubble;
}

selectMode(mode);

[nameInput, levelInput, topicInput, difficultyInput].forEach(input => {
    input.addEventListener("change", saveSettings);
});

form.addEventListener("submit", async event => {
    event.preventDefault();

    const text = message.value.trim();
    const name = nameInput.value.trim() || "Student";
    const level = levelInput.value;
    const topic = topicInput.value.trim();
    const difficulty = difficultyInput.value;

    if (!text || !topic) {
        errorBox.hidden = false;
        errorBox.textContent = "Please enter both a topic and a question.";
        return;
    }

    saveSettings();
    errorBox.hidden = true;
    addBubble(text, "user");
    message.value = "";

    sentCount++;
    document.querySelector("#questionsCount").textContent = sentCount;
    const loading = addBubble("BoardTutor is thinking…", "bot", "loading");
    send.disabled = true;

    try {
        const response = await fetch("/api/tutor", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, level, topic, difficulty, mode, message: text})
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error(`Server returned an unreadable response (HTTP ${response.status}).`);
        }

        loading.remove();
        if (!response.ok) {
            throw new Error(data.detail || `Tutor request failed (HTTP ${response.status}).`);
        }

        addBubble(data.answer || "No answer was returned.", "bot");

        const firstLine = (data.answer || "").trim().split(/\r?\n/)[0].toUpperCase();
        if (["CORRECT", "INCORRECT", "PARTLY CORRECT"].some(label => firstLine.startsWith(label))) {
            labelsCount++;
            document.querySelector("#correctCount").textContent = labelsCount;
        }

        attempts++;
        document.querySelector("#attempts").textContent = attempts;
    } catch (error) {
        loading.remove();
        errorBox.hidden = false;
        errorBox.textContent = `${error.message} Check the VS Code terminal for details.`;
    } finally {
        send.disabled = false;
        message.focus();
    }
});

document.querySelector("#clear").addEventListener("click", () => {
    chat.replaceChildren();
    attempts = 0;
    sentCount = 0;
    labelsCount = 0;
    document.querySelector("#attempts").textContent = "0";
    document.querySelector("#questionsCount").textContent = "0";
    document.querySelector("#correctCount").textContent = "—";
    errorBox.hidden = true;
    addBubble("Session cleared. Choose a topic and start learning again!", "bot");
});
