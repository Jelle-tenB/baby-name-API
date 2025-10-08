// TODO: opmerking van Jelle; is de volgende todo niet al gedaan?
/*
    TODO: swap the apicaller fetches to callapi for increased oversight
globals js hier staat
    IconMenu :
    apicaller:
*/
// SVG icon website: https://uxwing.com/info-circle-line-icon/

let USERLOGEDIN = checkCred()

class ApiCaller{
    /**
     * this class will hold all the fetch request to the backend
     *  for post request credentials : include is needed to pass along the cookie
     *  when using a method always use await in front and async on the scope
     */
    constructor(){
        // swap to localhost for testing
        // this.url = 'https://apibabynamegenerator.roads-technology.nl'
        this.url = 'http://127.0.0.1:5000'
    }

    async callApi(url,method = 'get',body = {}){
        try {
            //check if post then add a body
            const response = method === 'post' ? await fetch(url , {
                method,
                credentials : 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body : JSON.stringify(body),
                keepalive : true
            }) : await fetch(url,{
                method,
                credentials : 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            })
            if (response.status != 200) throw new Error(response.json())
                return response.json()
        } catch (error) {   
            throw new Error(error)
        }
    }
    
    async getSwipeList(){
        //check the localstorage if not there make a default with just ? gender
        const parameters = localStorage.getItem('parameters') ? JSON.parse(localStorage.getItem('parameters')) : {gender:'?'}
        const search = new URLSearchParams()
        //loop trough the filter parameters in localstorage check if there not empty and add them
        for ( const [key,value] of Object.entries(parameters)){
            if(value){
                if(Array.isArray(value) && value.length > 0){
                    value.map(land => {
                        search.append('country',land)
                    })
                }
                else if(!Array.isArray(value)) {
                    search.append(key,value)
                } 
            } 
        }
        //send a get request
        const response = await this.callApi(this.url+'/search?'+search)
        //return the list of names or error that backend provided
        return response
    }

    //get a list of names similar to the name profided
    async getSimilar(nameID = 123){
        //TODO: test
        const response = await this.callApi(this.url+`/similar?name_id=${nameID}`)
        return response
    }

    // give the like ids and dislike ids and returns a sucses response
    async sendPreferences(liked,disliked){
        const body = {}
        //check if they have values
        if(liked.length >= 1) body.liked = liked
        if(disliked.length >= 1) body.disliked = disliked
        const response = await this.callApi(this.url+'/preferences', 'post',body)
        return response
    }

    //returns the liked list
    async getLikedList(){
        const response = await this.callApi(this.url+'/like_list')
        return response
    }

    async getDislikedList(){
        //TODO: test
        const response = await this.callApi(this.url+'/dislike_list')
        return response
    }

    //returns the matches between partners
    async getGroupLiked(){
        //TODO: test
        const response = await this.callApi(this.url+'/group_liked')
        return response
    }

    //returns the list of names that the partner liked but user has not 
    async PartnersLiked(group_code){
        //TODO: test, needs input of group_code
        const response = await this.callApi(this.url+`/compare_likes?group_code=${group_code}`)
        return response
    }

    //try to log in with the cookie and returns a sucsess response
    async cookyLogIn(){
        const response = await this.callApi(this.url+'/cookie')
        return response
    }

    //try to log in and returns a success response
    async logIn(username = 'string', password = 'string'){
        const response = await this.callApi(this.url+'/login','post',{username,password});
        return response;
    }

    //logout and clear cooky
    async logOut(){
        const response = await this.callApi(this.url+'/logout');
        return response;
    }

    //make a new account with the provided username and password returns success or error
    async newUser(username = 'string' , password = 'string'){
        const response = await this.callApi(this.url+'/new_user','post',{username,password} )
        return response
    }

    // give username new ww and recovery code to change the password to new password
    async recoverAccount(username,new_password,recovery_token){
        //TODO: test 
        const response = await this.callApi(this.url+'/account_recovery','post',{username,new_password,recovery_token})
        return response
    }

    //create a new group and returns group id to send to partner to hook up
    async newGroup(){
        //TODO: test 
        //TODO: needs to be a get ?
        const response = await this.callApi(this.url+'/new_group','post')
        return response
    }

    // add user to partner for the list
    async addToGroup(group_code){
        const response = await this.callApi(this.url+'/add_to_group','post',{group_code})
        return response
    }

    async deleteGroup(group_code){
        //TODO: test 
        const response = await this.callApi(this.url+`/delete_group?group_code=${group_code}`,'delete')
        return response
    }
    
    async deleteLike(name_ids = []){
        //TODO: test
        const search = new URLSearchParams()
        name_ids.forEach(id => search.append('id',id))
        const response = await this.callApi(this.url+'/unlike?'+search,'delete')
        return response
    }

    async deleteDislike(name_ids = []){
        //TODO:
        const search = new URLSearchParams()
        name_ids.forEach(id => search.append('id',id))
        const response = await this.callApi(this.url+'/undislike?'+search,'delete')
        return response
    }

    async deleteAccount(){
        //TODO:
        const response = await this.callApi(this.url+'/delete_user','delete')
        return response
    }

}

// this is the menu bar at the bottom
class IconMenu extends HTMLElement {
    /**
     * het menu dat in de footer staat voor gebruik in html <icon-menu page="huidige page"></icon-menu>
     * to add a page to the menu add the below line in this.pages
     *  ['name of the page','url to the svg']
     * in the html add page="name" so the icon wil be highlighted
     */
    constructor() {
        super();
        //ad or remove pages here first part the name second part the img path
        this.pages = [
            ['swipen','../Images/zoom.svg'],
            ['filter', '../Images/settings.svg'],
            ['likes', '../Images/likes.svg'],
            ['partners', '../Images/handshake.svg'],
            ['information-page', '../Images/information.svg']
        ]
        this.apiCaller = new ApiCaller()
        this.currentpage = this.getAttribute('page');
        //set a page in localstorage for when a user logs back in there back to the page the left
        localStorage.setItem('lastpage',JSON.stringify(this.currentpage))
        this.buildHTML();
        this.querySelector('#'+this.currentpage+'link').classList.add('activePage');

    }

    buildHTML(){
        this.innerHTML = /*html*/`
        <div id='mainnav'>
            <a href="./welcome.html">
                <img id="menulogo" src="../Images/templogo.svg" height="35" width="35" class="logoimg" alt="logo">
            </a>
        </div>
        `
        const menu = this.querySelector('#mainnav')
        this.pages.forEach(page => {
            menu.append(this.createLink(page))
        })

        //check if user is loged in and show it here
        if(USERLOGEDIN){
            menu.innerHTML += /*html*/`<button id="menulogoff">logout</button>`
            this.querySelector('#menulogoff').onclick = async() =>{
                //send query to logout
                const response = await this.apiCaller.logOut()
                if(response.success) window.location.assign('../html/login.html')
            }
        }  
        else {
            menu.innerHTML += /*html*/`<button id='menuloginbutton' onclick="window.location.assign('../html/login.html')">login</button>`
        }
    }

    createLink([txt,imgPath]){
        const link = document.createElement('a')
        const img = document.createElement('img')
        link.href = txt+'.html'
        link.id = txt+'link'
        link.classList.add('menulink')
        img.src = imgPath
        link.append(img)
        return link
    }
    
}
customElements.define('icon-menu', IconMenu);





//function to give feedback to the user about the problem
function createWarn(txt){
    //TODO: make an in app visual for it
    alert(txt)
}

function getCookie(){
    if (document.cookie){
        // 1. Get the cookie
        const cookieString = document.cookie;
        
        // 3. Unescape the JSON string
        let rawJsonStr = cookieString
            .replace(/\\054/g, ',')    // replace \054 (octal for comma)
            .replace(/\\"/g, '"')    // unescape double quotes
            .split('=')[1]          //remove the session_token=
            .replace(/^"|"$/g, '')  // remove the last and first "
        // 4. Parse the JSON
        try {
            const sessionData = JSON.parse(rawJsonStr);
            // console.log("Parsed session data:", sessionData);
            return sessionData
        } catch (e) {
            console.error("Failed to parse JSON:", e);
        }
    }
    //redirect to login page since there is no cookie
    else{
        window.location.assign('../html/login.html')
    }
}

//check if there is a valid looking cookie and returns true or false
function checkCred(){
    const sessionCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('session_token='))
    if (!sessionCookie) return false // stop execution
    return true;
}
