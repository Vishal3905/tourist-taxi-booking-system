console.log("Taxi Website Loaded!");

const counters = document.querySelectorAll(".counter");

counters.forEach(counter => {

    const updateCounter = () => {

        const target = +counter.getAttribute("data-target");
        const current = +counter.innerText;

        const increment = target / 100;

        if(current < target){
            counter.innerText = Math.ceil(current + increment);
            setTimeout(updateCounter, 20);
        }else{
            counter.innerText = target + "+";
        }
    };

    updateCounter();
});


const rating = document.querySelector(".rating-counter");

if(rating){
    let value = 0;

    const ratingInterval = setInterval(() => {

        value += 0.1;

        rating.innerText = value.toFixed(1) + "★";

        if(value >= 4.9){
            rating.innerText = "4.9★";
            clearInterval(ratingInterval);
        }

    },50);
}