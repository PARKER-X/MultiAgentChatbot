let history = [];

function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  // Add user message
  addMessage("user", message);
  input.value = "";

  // Add placeholder assistant message
  const loadingDiv = addMessage("assistant", "Bot is processing...");

  // Use setTimeout to let the DOM update first
  setTimeout(async () => {
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message, history })
      });

      const data = await response.json();
      history = data.history;

      updateMessage(loadingDiv, `Bot: ${data.response}`);
    } catch (err) {
      updateMessage(loadingDiv, "Bot: Sorry, something went wrong.");
      console.error(err);
    }
  }, 10); // Minimal delay to give browser time to update
}

function addMessage(role, text) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = role;
  div.textContent = `${role === "user" ? "You" : "Bot"}: ${text}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div; // So we can update this message later
}

function updateMessage(div, newText) {
  div.textContent = newText;
}
