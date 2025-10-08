const apiCaller = new ApiCaller()

document.querySelector('#loginbutton').onclick = async() => {
    const username = document.getElementById('loginUser').value
    const key = document.getElementById('loginrecovery').value
    const password = document.getElementById('loginPass').value
    const checkPassword = document.getElementById('loginPass2').value

    //if elsif statements to check if name and Password fullfil the criteria and give responses for failed attempts
    if(username.length > 3 && password.length > 7 && checkPassword && password == checkPassword && key){
        //all the fields are filled in and password is inputted twice the same
        try {
            const response = await apiCaller.recoverAccount(username,password,key)
            console.log(response)
            //TODO: handle response
            // if(response.success) localStorage.getItem('lastpage') ? window.location.assign(`../html/${JSON.parse(localStorage.getItem('lastpage'))}.html`) : window.location.assign('../html/filter.html')
            if (response.success) {
                const lastPage = localStorage.getItem('lastpage');
                if (lastPage) {
                    window.location.assign(`../html/${JSON.parse(lastPage)}.html`);
                } else {
                    window.location.assign('../html/filter.html');
                }
            }
        } catch (error) {
            console.warn(error)
        }
    }
    else if(password.length < 8){
        createWarn('Password should have at least 8 characters')
    }
    else if(password && checkPassword && password != checkPassword){
        //create a warning that password != checkPassword
        createWarn('Password and check password are not the same')
    }
    else if(!username){
        createWarn('Please fill in the username')
    }
    else if(username.length){
        createWarn('Username should have at least 4 characters')
    }
    else if(!password){
        createWarn('Please fill in a password')
    }
    else if(!acceptEula){
        createWarn('Accepting the eula is required')
    }

}
