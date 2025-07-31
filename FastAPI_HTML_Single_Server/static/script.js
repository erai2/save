async function askQuestion() {
  const q = document.getElementById("questionInput").value;
  const res = await fetch("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: q }),
  });
  const data = await res.json();
  document.getElementById("answerBox").textContent = data.answer;
}