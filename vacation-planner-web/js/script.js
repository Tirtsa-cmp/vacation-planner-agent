console.log("Hello Vacation Planner!");

const button = document.getElementById("plan-button");
const responseArea = document.getElementById("agent-response");

button.addEventListener("click", function() {

    const tripData = {

        people: document.getElementById("number_of_people").value,

        budget: document.getElementById("budget").value,

        days: document.getElementById("number_of_days").value,

        preference: document.getElementById("preference").value

    };


    localStorage.setItem(
        "tripData",
        JSON.stringify(tripData)
    );


    window.location.href = "planner.html";

});
const navbar = document.querySelector(".navbar");


window.addEventListener("scroll", function(){

    if(window.scrollY > 50){

        navbar.classList.add("scrolled");

    } else {

        navbar.classList.remove("scrolled");

    }

});