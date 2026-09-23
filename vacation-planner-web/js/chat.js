let sessionId = sessionStorage.getItem("vacation_session_id");
if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("vacation_session_id", sessionId);
}
const sendButton = document.getElementById("send-button");
console.log("CHAT.JS LOADED");
const input = document.getElementById("user-answer");

const chatBox = document.getElementById("chat-box");



sendButton.addEventListener("click", async function(){
console.log("BUTTON CLICKED");


const answer = input.value;
console.log("MESSAGE:", answer);

if(answer.trim() === "") return;

console.log("SENDING MESSAGE TO SERVER...");
    // afficher message utilisateur
addMessage(answer, "user");


input.value = "";


    // message temporaire IA
addMessage("✨ AI is thinking...", "ai thinking");



try {

console.log("FETCHING RESPONSE FROM SERVER...");
    const response = await fetch(
        "http://localhost:5000/chat",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    message: answer,

                    session_id: sessionId

                })

            }
        );



    const data = await response.json();



        // supprimer le message thinking
    //const thinking = document.querySelector(".thinking");

    //if(thinking){
     //       thinking.remove();
       // }



        // afficher réponse Claude
    addMessage(data.response, "ai");


    }

catch(error){

    console.error(error);

addMessage(
            "❌ Something went wrong.",
            "ai"
        );

    }


});



function addMessage(text, type){
    // Convert markdown-style links [text](url) into clickable buttons
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g;
    let formattedText = text.replace(linkRegex, (match, label, url) => {
        return `<a href="${url}" target="_blank" class="booking-link">${label}</a>`;
    });

    // Convert remaining markdown bold **text** into <strong>
    formattedText = formattedText.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Convert line breaks into <br>
    formattedText = formattedText.replace(/\n/g, "<br>");

    chatBox.innerHTML += `
    <div class="message ${type}">
        ${formattedText}
    </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;
}