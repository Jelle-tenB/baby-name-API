const apiCaller = new ApiCaller()
const imgPath = '../Images/country_flags/'
//check if there is a cookie otherwise go to login page

const countries = [
{key: 'Great Britain', value: 'Great_Britain', tag: 'GB'},
{key: 'Ireland', value: 'Ireland', tag: 'IE'},
{key: 'U.S.A.', value: 'USA', tag: 'US'},
{key: 'Italy', value: 'Italy', tag: 'IT'},
{key: 'Malta', value: 'Malta', tag: 'MT'},
{key: 'Portugal', value: 'Portugal', tag: 'PT'},
{key: 'Spain', value: 'Spain', tag: 'ES'},
{key: 'France', value: 'France', tag: 'FR'},
{key: 'Belgium', value: 'Belgium', tag: 'BE'},
{key: 'Luxembourg', value: 'Luxembourg', tag: 'LU'},
{key: 'the Netherlands', value: 'Netherlands', tag: 'NL'},
{key: 'East Frisia', value: 'East_Frisia', tag: 'EF'},
{key: 'Germany', value: 'Germany', tag: 'DE'},
{key: 'Austria', value: 'Austria', tag: 'AT'},
{key: 'Swiss', value: 'Swiss', tag: 'CH'},
{key: 'Iceland', value: 'Iceland', tag: 'IS'},
{key: 'Denmark', value: 'Denmark', tag: 'DK'},
{key: 'Norway', value: 'Norway', tag: 'NO'},
{key: 'Sweden', value: 'Sweden', tag: 'SE'},
{key: 'Finland', value: 'Finland', tag: 'FI'},
{key: 'Estonia', value: 'Estonia', tag: 'EE'},
{key: 'Latvia', value: 'Latvia', tag: 'LV'},
{key: 'Lithuania', value: 'Lithuania', tag: 'LT'},
{key: 'Poland', value: 'Poland', tag: 'PL'},
{key: 'Czech Republic', value: 'Czech_Republic', tag: 'CZ'},
{key: 'Slovakia', value: 'Slovakia', tag: 'SK'},
{key: 'Hungary', value: 'Hungary', tag: 'HU'},
{key: 'Romania', value: 'Romania', tag: 'RO'},
{key: 'Bulgaria', value: 'Bulgaria', tag: 'BG'},
{key: 'Bosnia and Herzegovina', value: 'Bosnia_Herzegovina', tag: 'BA'},
{key: 'Croatia', value: 'Croatia', tag: 'HR'},
{key: 'Kosovo', value: 'Kosovo', tag: 'XK'},
{key: 'Macedonia', value: 'Macedonia', tag: 'MK'},
{key: 'Montenegro', value: 'Montenegro', tag: 'ME'},
{key: 'Serbia', value: 'Serbia', tag: 'RS'},
{key: 'Slovenia', value: 'Slovenia', tag: 'SI'},
{key: 'Albania', value: 'Albania', tag: 'AL'},
{key: 'Greece', value: 'Greece', tag: 'GR'},
{key: 'Russia', value: 'Russia', tag: 'RU'},
{key: 'Belarus', value: 'Belarus', tag: 'BY'},
{key: 'Moldova', value: 'Moldova', tag: 'MD'},
{key: 'Ukraine', value: 'Ukraine', tag: 'UA'},
{key: 'Armenia', value: 'Armenia', tag: 'AM'},
{key: 'Azerbaijan', value: 'Azerbaijan', tag: 'AZ'},
{key: 'Georgia', value: 'Georgia', tag: 'GE'},
{key: 'Kazakhstan/Uzbekistan,etc.', value: 'Kazakhstan', tag: 'KZ'},
{key: 'Turkey', value: 'Turkey', tag: 'TR'},
{key: 'Arabia/Persia', value: 'Arabia', tag: 'AR'},
{key: 'Israel', value: 'Israel', tag: 'IL'},
{key: 'China', value: 'China', tag: 'CN'},
{key: 'India/Sri Lanka', value: 'India', tag: 'IN'},
{key: 'Japan', value: 'Japan', tag: 'JP'},
{key: 'Korea', value: 'Korea', tag: 'KR'},
{key: 'Vietnam', value: 'Vietnam', tag: 'VN'},
{key: 'other countries', value: 'Other_Countries', tag: 'OT'},
]

class Filter extends HTMLElement {
    constructor() {
        super();
        this.genders = [
            ['neutral','?'],
            ['male','M'],
            ['female','F'],
            ['all','']
        ] 

        if (!this.parameters){
            this.parameters = this.defaultParameters
        }
        this.buildHTML();
    }

    get parameters(){
        return JSON.parse(localStorage.getItem('parameters'))
    }
    set parameters(obj){
        //TODO: error handling
        localStorage.setItem('parameters',JSON.stringify(obj))
    }

    get gender(){
        return this.parameters.gender
    }
    set gender(value){
        const param = this.parameters
        param.gender = value
        this.parameters = param
    }

    get countries(){
        return this.parameters.country
    }
    set countries(value){
        const param = this.parameters
        param.country = value
        this.parameters = param
    }

    get letter(){
        return this.parameters.letter
    }
    set letter(value){
        const param = this.parameters
        param.letter = value
        this.parameters = param
    }

    get letterWhere(){
        return this.parameters.start
    }
    set letterWhere(value){
        const param = this.parameters
        param.start = value
        this.parameters = param
    }

    get defaultParameters(){
        return {gender : '?', country : [], letter : '',start:'' }
    }

    buildHTML(){
        this.innerHTML = /*html */`<h1 id='filtertitle'>Choose how to filter</h1>`
        this.append(this.createGenderFilter())
        this.append(this.createLetterFilter())
        this.append(this.createCountryFilter())
        this.append(this.createSwipeButton())
    }
    createGenderFilter(){
        const div = document.createElement('div')
        div.id = 'genderfilter'
        //create a head
        div.innerHTML = /*html*/`<div class='filterhead ' >Gender:</div>`
        //fill options with genders from this.genders in the constructor
        this.genders.forEach( gender => {
            const [txt,value] = gender
            const genderCard = document.createElement('div')
            genderCard.id = txt+'card'
            genderCard.setAttribute('value',value)
            genderCard.classList.add('gendercard')
            genderCard.innerText = txt
            if(this.gender == value)genderCard.toggleAttribute('selected', true)
            genderCard.onclick = (e) => this.clickGender(e)
            div.append(genderCard)
        })
        return div
    }

    createLetterFilter(){
        const currentLetter = this.letter
        const div = document.createElement('div')
        div.id = 'letterfilter'
        div.innerHTML = /*html*/`
            <div class='filterhead' >Letter:</div>
            <div id='lettertogglewrapper'>
                <div id="letterStartButton" ${this.letterWhere == '1' && 'selected'} value="1">Starting letter</div>
                <div id="letterenywhereButton" ${this.letterWhere == '0' && 'selected'} value="0">Anywhere</div>
            </div>
        `
        // onclick for the letterwhere buttons
        const startbtn = div.querySelector('#letterStartButton')
        const anywherebtn = div.querySelector('#letterenywhereButton')
        startbtn.onclick = e => this.clickWhereLetter(e,startbtn)
        anywherebtn.onclick = e => this.clickWhereLetter(e,anywherebtn)

        const lettercontainer = document.createElement('div')
        lettercontainer.id = 'letterwrapper'
        div.append(lettercontainer)
        // using 65 for fromcharcode has the A there
        for(let i = 65 ; i < 91; i++){
            const letter = String.fromCharCode(i)
            const letterdiv = document.createElement('div')
            letterdiv.classList.add('letterdiv')
            letterdiv.innerText = letter
            if(currentLetter == letter)letterdiv.toggleAttribute('selected', true)
            letterdiv.setAttribute('value', letter)
            letterdiv.onclick = (e) => this.clickLetter(e,letterdiv)
            lettercontainer.append(letterdiv)
        }
        return div
    }

    createCountryFilter(){
        //add the flags
        const currentCountries = this.countries
        const div = document.createElement('div')
        div.id = 'countryfilter'
        div.innerHTML= /*html*/`<div class="filterhead">Countries:</div>`
        const flags = document.createElement('div')
        div.append(flags)
        flags.id = 'flagwrapper'
        countries.forEach((country)=>{
            const flagDiv = document.createElement('div')
            flagDiv.classList.add('flagdiv')
            flagDiv.setAttribute('value',country.value)
            if(currentCountries.includes(country.value)) flagDiv.toggleAttribute('selected',true)
            const img = document.createElement('img')
            img.classList.add('flagimg')
            img.src = imgPath+country.tag.toLocaleLowerCase()+'.png'
            flagDiv.append(img)
            flagDiv.innerHTML += /*html*/`<p>${country.key}</p>`
            flags.append(flagDiv)
            flagDiv.onclick = (e) => this.clickCounty(e,flagDiv)
        })
        return div
    }

    createSwipeButton(){
        const button = document.createElement('button')
        button.id = 'gotoswipebutton'
        button.onclick = () => this.goSwipe()
        button.innerText = 'Go to swipen'
        button.toggleAttribute('shadow',true)
        return button
    }

    goSwipe(){
        //TODO: get swipe list ?
        window.location.assign('../html/swipen.html')
    }

    clickGender(e){
        //TODO: put gender in localstorage and swap highlight to current clicked
        const clicked = e.target
        const current = this.querySelector('.gendercard[selected]')
        if(clicked != current){
            //deselect current and select the new gender
            current?.toggleAttribute('selected',false)
            clicked.toggleAttribute('selected',true)
        }
        else if(clicked == current){
            //select all
            clicked.toggleAttribute('selected',false)
            this.querySelector('#allcard').toggleAttribute('selected')
        }
        //update the gender value
        this.gender = this.querySelector('.gendercard[selected]').getAttribute('value')
    }

    clickWhereLetter(e , div){
        const currentValue = this.letterWhere
        const clickedValue = div.getAttribute('value')
            if(currentValue != clickedValue){
                this.querySelector('#lettertogglewrapper [selected]')?.toggleAttribute('selected',false)
                this.letterWhere = clickedValue
                div.toggleAttribute('selected',true)
                //check if a letter exists otherwise default to A
                if(!this.letter){
                    this.querySelector('.letterdiv[value="A"]').toggleAttribute('selected',true)
                    this.letter = 'A'
                }
            }
            else if(currentValue == clickedValue){
                div.toggleAttribute('selected',false)
                this.letterWhere = ''
                //TODO: untoggle the letter
                this.letter = ''
                this.querySelector('.letterdiv[selected]')?.toggleAttribute('selected',false)
            }
    }

    clickLetter(e,div){
        const clickedLetter = div.getAttribute('value')
        //check if letter = current
        if(this.letter != clickedLetter){
            this.letter = clickedLetter
            this.querySelector('.letterdiv[selected]')?.toggleAttribute('selected',false)
            div.toggleAttribute('selected',true)
            //TODO: check if a where button is pressed if not then add first
            // Jelle; Is dit niet al gedaan?
            if(!this.letterWhere){
                this.letterWhere = '1'
                this.querySelector('#letterStartButton').toggleAttribute('selected',true)
            }
        }
        else if(this.letter == clickedLetter){
            //toggle of the letter
            this.letter = ''
            div.toggleAttribute('selected',false)
            //TODO: toggle of the where button
            // Jelle; Is dit niet al gedaan?
            this.letterWhere = ''
            this.querySelector('#lettertogglewrapper [selected]')?.toggleAttribute('selected',false)
        }
    }

    clickCounty(e,div){
        const clickedCountry = div.getAttribute('value')
        const currentCountries = this.countries
        //check if adding or removing the country
        if(!currentCountries.includes(clickedCountry)){
            //add country to the list
            currentCountries.push(clickedCountry)
            div.toggleAttribute('selected',true)
        }
        else{
            //remove country from the list
            currentCountries.splice(currentCountries.indexOf(clickedCountry),1)
            div.toggleAttribute('selected',false)
        }
        this.countries = currentCountries
    }

}customElements.define('filter-component', Filter);