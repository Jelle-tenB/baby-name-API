// TODO:
/*
forgot password
registration page
css update
add text
*/

const apiCaller = new ApiCaller()

try {
    if(document.cookie){
        const cookielogin = await apiCaller.cookyLogIn()
        if(cookielogin.success){
            successLogin(cookielogin)
            console.log(cookielogin)
        }
    }
} catch (error) {
    console.error(error)
}
//TODO: if cookielogin is successful redirect

//add this function to the login button
document.querySelector('#loginbutton').addEventListener('click', () => logIn());
//add login to enter key
document.addEventListener('keypress', (e) => {if(e.key === 'Enter') logIn() })

async function logIn(){
    //get user values
    const username = document.querySelector('#loginUser').value;
    const password = document.querySelector('#loginPass').value;
    //check if both fields are filled in
    if(username.length > 12)createWarn('Username or password invalid')
    else if(username.length < 4)createWarn('Username or password invalid')
    else if(password.length < 8)createWarn('Username or password invalid')
    else if(password.length > 32)createWarn('Username or password invalid')
    else if(username && password){
        try {
            //try to log in
            const response = await apiCaller.logIn(username,password)
            console.log(response)
            //if successful login go to last page or filter page depending if there is already a filter defined
            if(response.success){
                successLogin(response)
            } 
        } catch (error) {
            //something went wrong
            console.log(error)
            //TODO: give feedback on wrong name/ww
        }
    }
    else if(!username){
        alert('No username was given')
    }
    else if(!password){
        alert('No password was given')
    }
}

function successLogin(response){
    //check if a group code is attached and put in the storage
    if(response['group codes'].length > 0)localStorage.setItem('group_code',response['group codes'][0])
    // check if there is a group code that has been removed in localstorage
    else if(localStorage.getItem('group_code')) localStorage.removeItem('group_code')
    //redirect to last known page
    localStorage.getItem('parameters') ? window.location.assign(`../html/${JSON.parse(localStorage.getItem('lastpage'))}.html`) : window.location.assign('../html/filter.html')
}