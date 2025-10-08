//want to build it so u can swap between creating group and joining group by selecting the card
// TODO: opmerking van Jelle; Deze pagina checked de cookie 2x.
// In de backend wordt de session_token alleen vernieuwd als hij ouder is dan 1 uur. Hopelijk voorkomt dit problemen.
// Er komen namelijk wel eens problemen voor met gelijktijdige requests die de cookie updaten.

const apiCaller = new ApiCaller()
apiCaller.cookyLogIn()

class Partner extends HTMLElement {
    constructor() {
        super();
        this.cookieData = getCookie()
        this.buildHTML();
    }
    #apicaller = new ApiCaller()

    get checkGroupToken(){
        //return 0 or 1 depending if the obj is filled
        return Object.keys(this.cookieData.group_codes).length
    }

    buildHTML(){
        //display the group code if one is already made
        this.innerHTML = `<h2 id='partnertitle'>Partners</h2>`
        //if there are group code loop trough m and display
        if(this.checkGroupToken){
            const obj = this.cookieData.group_codes
            for (const [code,name] of Object.entries(obj)){
                this.innerHTML += /* html */`
            <div class="wrapper" shadow>
                <div id='display${code}' class="grouptoken" shadow>Your group code : ${code}</div>
                <button id="delete${code}">X</button>
                ${ name.length > 0 ? '<p>Partner : '+name+'</p>' : ''}
            </div>
            `
            //add function to the buttons need timeout couse thers more html added below
            setTimeout(() => {
                this.querySelector('#delete'+code).onclick = async() => this.deleteGroup(code)
                //add code to clipboard for easy sharing
                this.querySelector('#display'+code).onclick = () =>{
                    navigator.clipboard.writeText(code)
                    alert('Code copied')
                }
            }, 0);
            }
        }
        // display a join / create group
        if(this.checkGroupToken < 2){
            this.innerHTML += /*html */`
            <div class="wrapper" shadow>
                <button id="creategrouptokenbutton" >Create group</button>
            </div>
            <div class="wrapper" shadow>
                <label>
                grouptoken
                <input Type='text' id='joingroup' name='grouptoken'>
                </label>
                <button id="joingroupbutton">join</button>
            </div>
            `

            //add functino to the button
            this.querySelector('#joingroupbutton').onclick = async() => this.joinGroup()
            this.querySelector('#creategrouptokenbutton').onclick = async() => this.askGroupToken()
           
        }


    }

    //send fetch to ask for a group code and display it to the user
    async askGroupToken(){
            const response = await this.#apicaller.newGroup()
            if(response.success){
                //remake the page do display the code
                this.cookieData = getCookie()
                this.buildHTML()
            }
    }

    //try to join the group thats filled in
    async joinGroup(){
        //send grouptoken to join the group then handle response
        try {
            const token = this.querySelector('#joingroup').value
            const response = await this.#apicaller.addToGroup(token)
            if(response.success || response.split(':')[0] == 'success'){
                    //remake the page do display the code
                    this.cookieData = getCookie()
                    this.buildHTML()
            }
        } catch (error) {
                alert('The supplied Group Code can not be found')
                this.querySelector('#joingroup').value = ''
        }
    }

    //remove the group and show the join/create again
    async deleteGroup(code){
        const response = await this.#apicaller.deleteGroup(code)
        if(response.success || response.split(':')[0] == 'success'){
            this.cookieData = getCookie()
            this.buildHTML()
        }
    }

}customElements.define('partner-component', Partner);