const apiCaller = new ApiCaller()
const cookieData = getCookie()
//if no valid cooky redirect to login
if(!cookieData) window.location.assign('./login.js')

document.getElementById('username').innerText += `Username: ${cookieData.username}`
let confirm = false

document.getElementById('deleteaccountbutton').onclick = async() => deleteAccount()
async function deleteAccount(){
    if (confirm){
        //send the delete account
        const response = await apiCaller.deleteAccount()
    }
    else{
        //give are u sure check
        alert('Are you sure you wish to delete the account? Click again to confirm.')
        confirm = true
    }
}

