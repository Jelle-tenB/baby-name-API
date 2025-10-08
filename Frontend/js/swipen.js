//TODO: add credit
// Jelle; waar moet de credit erbij?

//TODO: give warning if you're not logged in
/* LikeCarousel (c) 2019 Simone P.M. github.com/simonepm - Licensed MIT */

// get the apicaller for api connection
const apicaller = new ApiCaller()
// get the names to swipe true
async function getNames() {
    //check if there is similarNames in the storage which should happen in likes.html
    if(localStorage.getItem('similarNames')){
        const names = JSON.parse(localStorage.getItem('similarNames'))
        localStorage.removeItem('similarNames')
        return names
    }
    //check if there are filter settings otherwise redirect user to filter.html
    else if (localStorage.getItem('parameters') == null) {
        alert('You need to set your settings first!');
         window.location.assign('../html/filter.html')
    }
    //call api to get names according to the filter
    else {
        try {
            const names = await apicaller.getSwipeList()
            return names
        } catch (error) {
            //TODO:
            console.error(error)
        }
    }
}

const names = await getNames()
//remove the loading sign when we have the names
document.getElementById('loadwarning').remove()

//carousel handles the cards handle, onTap, onpan are default functions try not to edit it too much
class Carousel { 

    constructor(element) {

        if (!element) {
            console.log('element not provided');
            this.board = document.createElement('div');
        } else {
            this.board = element;
        }
        this.lastNumber = 0;

        this.index = [];
        this.likeIDs = []
        this.DisLikeIDs = []

        this.array = names
        //set the counter
        this.updateCounter()

        // add first two cards programmatically
        if (this.array.length > 1) {
            this.push();
            this.push();
        } else {
            this.pushMessage();
        }
        // handle gestures
        this.handle();

    }

    handle() {

        // list all cards
        this.cards = this.board.querySelectorAll('.card');

        // get top card
        this.topCard = this.cards[this.cards.length - 1];

        // get next card
        this.nextCard = this.cards[this.cards.length - 2];

        // if at least one card is present
        if (this.cards.length > 0) {

            // set default top card position and scale
            this.topCard.style.transform =
                'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)';

            // destroy previous Hammer instance, if present
            if (this.hammer) this.hammer.destroy();

            // listen for tap and pan gestures on top card
            this.hammer = new Hammer(this.topCard);
            this.hammer.add(new Hammer.Tap());
            this.hammer.add(new Hammer.Pan({
                position: Hammer.position_ALL,
                threshold: 0
            }));

            // pass events data to custom callbacks
            this.hammer.on('tap', (e) => {
                this.onTap(e)
            });
            this.hammer.on('pan', (e) => {
                this.onPan(e)
            });

        }

    }

    onTap(e) {

        // get finger position on top card
        let propX = (e.center.x - e.target.getBoundingClientRect().left) / e.target.clientWidth;

        // get rotation degrees around Y axis (+/- 15) based on finger position
        let rotateY = 15 * (propX < 0.05 ? -1 : 1);

        // enable transform transition
        this.topCard.style.transition = 'transform 100ms ease-out';

        // apply rotation around Y axis
        this.topCard.style.transform =
            'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(' + rotateY + 'deg) scale(1)';

        // wait for transition end
        setTimeout(() => {
            // reset transform properties
            this.topCard.style.transform =
                'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)';
        }, 100);

    }

    onPan(e) {
        if (!this.isPanning) {

            this.isPanning = true;

            // remove transition properties
            this.topCard.style.transition = null;
            if (this.nextCard) this.nextCard.style.transition = null;

            // get top card coordinates in pixels
            let style = window.getComputedStyle(this.topCard);
            let mx = style.transform.match(/^matrix\((.+)\)$/);
            this.startPosX = mx ? parseFloat(mx[1].split(', ')[4]) : 0;
            this.startPosY = mx ? parseFloat(mx[1].split(', ')[5]) : 0;

            // get top card bounds
            let bounds = this.topCard.getBoundingClientRect();
            // get finger position on top card, top (1) or bottom (-1)
            this.isDraggingFrom =
                (e.center.y - bounds.top) > this.topCard.clientHeight / 2 ? -1 : 1;

        }

        // get new coordinates
        let posX = e.deltaX + this.startPosX;
        let posY = e.deltaY + this.startPosY;

        // get ratio between swiped pixels and the axes
        let propX = e.deltaX / this.board.clientWidth;
        let propY = e.deltaY / this.board.clientHeight;

        // get swipe direction, left (-1) or right (1)
        let dirX = e.deltaX < 0 ? -1 : 1;

        // get degrees of rotation, between 0 and +/- 45
        let deg = this.isDraggingFrom * dirX * Math.abs(propX) * 45;

        // get scale ratio, between .95 and 1
        let scale = (95 + (5 * Math.abs(propX))) / 100;

        // move and rotate top card
        this.topCard.style.transform =
            'translateX(' + posX + 'px) translateY(' + posY + 'px) rotate(' + deg + 'deg) rotateY(0deg) scale(1)';

        // scale up next card
        if (this.nextCard) this.nextCard.style.transform =
            'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(' + scale + ')';

        if (e.isFinal) {

            this.isPanning = false;

            let successful = false;

            // set back transition properties
            this.topCard.style.transition = 'transform 200ms ease-out';
            if (this.nextCard) this.nextCard.style.transition = 'transform 100ms linear';

            // check threshold and movement direction
            if (propX > 0.25 && e.direction == Hammer.DIRECTION_RIGHT) {

                successful = true;
                // get right border position
                posX = this.board.clientWidth;

            } else if (propX < -0.25 && e.direction == Hammer.DIRECTION_LEFT) {

                successful = true;
                // get left border position
                posX = -(this.board.clientWidth + this.topCard.clientWidth);

            } else if (propY < -0.25 && e.direction == Hammer.DIRECTION_UP) {

                successful = true;
                // get top border position
                posY = -(this.board.clientHeight + this.topCard.clientHeight);

            }

            if (successful) {

                // throw card in the chosen direction
                this.topCard.style.transform =
                    'translateX(' + posX + 'px) translateY(' + posY + 'px) rotate(' + deg + 'deg)';

                // check if card went right for dislike
                if (e.direction === Hammer.DIRECTION_RIGHT) {
                    console.log('likeSwipe');
                    this.addLike(this.index)
                }
                //check if card went left for like
                else if (e.direction === Hammer.DIRECTION_LEFT){
                    console.log('dislikeSwipe')
                    this.addDislike(this.index)
                }
                //cehck if card went up for undicided
                else if(e.direction === Hammer.DIRECTION_UP){
                    this.returnName()
                }

                // wait transition end
                setTimeout(() => {
                    // remove swiped card
                    this.board.removeChild(this.topCard);
                    // add new card
                    this.push();
                    // handle gestures on new top card
                    this.handle();
                }, 200);

            } else {

                // reset cards position and size
                this.topCard.style.transform =
                    'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)';
                if (this.nextCard) this.nextCard.style.transform =
                    'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(0.95)';

            }

        }

    }

    //TODO:: is random naam picken nodig?
    // creates random number's until it's not the same as the last time
    randomNumber(lastNumber) {
        let randomNumber = Math.floor(Math.random() * this.array.length);
        while (lastNumber == randomNumber) {
            randomNumber = Math.floor(Math.random() * this.array.length);
        }
        this.lastNumber = randomNumber;
        return randomNumber;
    }

    //creates the card and puts it in the dom
    //need 2 cards on screen for visual effect
    push() {
        let card = document.createElement('div');

        card.classList.add('card');
        card.style.transition = 'transform 200ms ease-out';
        if (this.array.length !== 0) {
            const nameObj = this.array.splice(this.randomNumber(this.lastNumber),1)[0]
            this.index.push(nameObj)
            const gender = nameObj.gender.length > 1 ? nameObj.gender[1] : nameObj.gender 
            card.innerHTML = /*html*/`<p id='name'>${nameObj.name}</p>`;
            card.style.backgroundColor = `var(--color${gender == '?' ? 'O' : gender})`;
            if (!board) { return false; }
            this.board.prepend(card);
        } else {
            this.pushMessage();
        }
        this.updateCounter()
    }

    pushMessage() {
        const card = document.createElement('div');
        card.classList.add('emptyMessage');
        card.innerHTML = /*html*/ `<p id="empty">We couldn't find any names with your settings!</p>`;

        this.board.prepend(card);
    }

    //update the number on screen displaying the number of names left
    updateCounter(){
        const div = document.getElementById('namecounter')
        div.innerHTML = /*html*/`${this.array.length}`
        console.log(this.index)
    }

    //add name to likes
    addLike(){
        this.likeIDs.push(this.index.shift().id)
        this.updateCounter()
    }

    //add name to dislikes
    addDislike(){
        this.DisLikeIDs.push(this.index.shift().id)
        this.updateCounter()
    }

    //return name to the pool
    returnName(){
        this.array.push(this.index.shift())
    }

    //clear the list
    clearLikes(){
        this.likeIDs = []
        this.DisLikeIDs = []
    }

    //the method for the buttons so animate the card like a swipe
    swipeCard(dir = 'right'){
    let style = window.getComputedStyle(carousel.topCard);
    let mx = style.transform.match(/^matrix\((.+)\)$/);
    let posY = dir == 'up'? -carousel.board.clientHeight : mx ? parseFloat(mx[1].split(', ')[5]) : 0;
    const posX = dir == 'right'? carousel.board.clientWidth : dir == 'up'? -carousel.topCard.clientWidth/2  : -(carousel.board.clientWidth + carousel.topCard.clientWidth);
    const rotate = dir == 'right'? 60 : dir == 'up' ? 0 : -60
    
    // throw card in the chosen direction
    carousel.topCard.style.transform = 'translateX(' + posX + 'px) translateY(' + posY + 'px) rotate(' + rotate + 'deg)';

    // wait transition end
    setTimeout(() => {
        // remove swiped card
        carousel.board.removeChild(carousel.topCard);
        // add new card
        carousel.push();
        // handle gestures on new top card
        carousel.handle();
    }, 200)
    }

}
//end Carousel

const board = document.querySelector('#board');
const carousel = new Carousel(board);

//add function to like button
document.querySelector('#like').addEventListener('click', () => {
    carousel.addLike(carousel.index);
    carousel.swipeCard('right')
});

//add function to dislike button
document.querySelector('#dislike').addEventListener('click', () => {
    carousel.addDislike(carousel.index)
    carousel.swipeCard('left')
});

//add function to refresh button
document.querySelector('#refresh').addEventListener('click', () => {
    carousel.swipeCard('up')
    carousel.returnName()
});


//async setinterval
const asyncIntervals = [];

const runAsyncInterval = async (cb, interval, intervalIndex) => {
  await cb();
  if (asyncIntervals[intervalIndex]) {
    setTimeout(() => runAsyncInterval(cb, interval, intervalIndex), interval);
  }
};

const setAsyncInterval = (cb, interval) => {
  if (cb && typeof cb === "function") {
    const intervalIndex = asyncIntervals.length;
    asyncIntervals.push(true);
    runAsyncInterval(cb, interval, intervalIndex);
    return intervalIndex;
  } else {
    throw new Error('Callback must be a function');
  }
};

const clearAsyncInterval = (intervalIndex) => {
  if (asyncIntervals[intervalIndex]) {
    asyncIntervals[intervalIndex] = false;
  }
};

//check for login to then update database of the picks
if(USERLOGEDIN){
    //create interval that updates the list to api 1/min
    //interval in ms
    // TODO: opmerking van Jelle; na het verzenden van likes/dislikes de lijsten clearen.
    const interval = 60000
     setAsyncInterval(async () => {
        if(carousel.likeIDs.length > 0 || carousel.DisLikeIDs.length > 0){
            try {
                const response = await apicaller.sendPreferences(carousel.likeIDs,carousel.DisLikeIDs)
                console.log(response)
                if(response.Success) carousel.clearLikes()
                console.log(carousel.likeIDs, carousel.DisLikeIDs)
            } catch (error) {
                //TODO:
                console.log(error)
            }
        }
        else{
            console.log('No names to add')
        }
    }, interval);
}
//user not loged in no need to send to server
else console.log('user not logged in')

// send final list update when page closes
// TODO:
//! does not wait for confirmation, could lead to issues later
window.onbeforeunload = () => {
    if(USERLOGEDIN){
        if(carousel.likeIDs.length > 0 || carousel.DisLikeIDs.length > 0) apicaller.sendPreferences(carousel.likeIDs,carousel.DisLikeIDs)
    }
    return
}