console.log("Hello Vaccation Planner !");

const button = document.getElementById("plan-button");
button.addEventListener("click", function() {
    alert("Let's plan your vacation!");

    const numberOfPeople = document.getElementById("number_of_people").value;
    const budget = document.getElementById("budget").value; 
    const numberOfDays = document.getElementById("number_of_days").value;
    const preference = document.getElementById("preference").value;

     console.log({
        people,
        days,
        preferences,
        budget
    });

});

const navbar = document.querySelector(".navbar");


window.addEventListener("scroll", function(){

    if(window.scrollY > 50){

        navbar.classList.add("scrolled");

    } else {

        navbar.classList.remove("scrolled");

    }

});