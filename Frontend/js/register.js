const apiCaller = new ApiCaller()
let confirmRecovery = false
let token

//add to the register button
document.getElementById('registerbutton').onclick = ( () => createAccount())
document.addEventListener('keypress', (e) => {if(e.key === 'Enter') createAccount() })
async function createAccount(){
    const username = document.querySelector('#registerUser').value
    const password = document.querySelector('#registerPass').value
    const checkPasword = document.querySelector('#registerPass2').value
    const acceptEula = document.querySelector('#accepteula').checked

    //if elsif statments to check if name and pasword fufil the criteria and give responses for failed atempts
    if(!password)createWarn('Please fill in a password')
    if(password.length > 32)createWarn('Password length needs to be shorter than 33 characters.')
    else if(password.length < 8)createWarn('Password should have at least 8 characters.')
    else if(password && checkPasword && password != checkPasword)createWarn('Password and check password are not the same')
    else if(!username)createWarn('Please fill in the username')
    else if(username.length < 4)createWarn('Username should have at least 4 characters')
    else if(username.length > 12)createWarn(`Username can't be longer than 12 characters`)
    else if(!acceptEula)createWarn('Accepting the eula is required')
    else{
        //all the fields are filled in and password is inputted twice the same
        try {
            const response = await apiCaller.newUser(username,password)
            console.log(response)
            token = response['recovery token']
            document.querySelector('#registerform').toggleAttribute('hidden',true)
            document.querySelector('#tokendiv').toggleAttribute('hidden',false)
            document.querySelector('#tokenHere').innerText = token
        } catch (error) {
            console.warn(error)
        }
    }
}

//function to give feedback to the user about the problem
function createWarn(txt){
    //TODO: make an in app visual for it
    alert(txt)
}

//function for the confirm button under the recovery token
document.querySelector('#confirmtoken').onclick = () =>{
    if(!confirmRecovery){
        confirmRecovery = true
        createWarn('Make sure you saved the recovery token. Your token is '+token+'  click again to continue.')
    }
    else{
        window.location.assign('../html/filter.html')
    }
}

