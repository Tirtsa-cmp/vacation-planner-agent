const sendButton = document.getElementById("send-button");

const input = document.getElementById("user-answer");

const chatBox = document.getElementById("chat-box");


sendButton.addEventListener("click", function(){


    const answer = input.value;


    if(answer === "") return;


    chatBox.innerHTML +=
    `
    <div class="message user">
        ${answer}
    </div>
    `;


    input.value = "";


});