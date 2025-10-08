//TODO: Make each await their own async
(async () => {
    
    const apiCaller = new ApiCaller()
    var cookie;
    
    try {
        cookie = await apiCaller.cookyLogIn(); // <-- now contains your cookie info
    } catch (e) {
        window.location.assign('../html/login.html');
        return;
    }

    const likedList1 = document.getElementById("likedList1");
    const likedList2 = document.getElementById("likedList2");
    const likedList3 = document.getElementById("likedList3");

    const liked1 = await apiCaller.getGroupLiked()

    const likeList = await apiCaller.getLikedList()
    const liked2 = likeList.map(item => item.name);

    const groupKeys = cookie["group codes"];
    const groupCode1 = Object.keys(groupKeys)[0]?.toString() || null;
    const groupCode2 = Object.keys(groupKeys)[1]?.toString() || null;

    if (Object.keys(groupKeys).length > 0) {
        var mutualList = liked1.reduce((acc, item) => {
            const groupCode = item["group code"];
            if (!groupCode) return acc; // skip if groupCode is falsy
            const entry = { [item["name id"]]: item["name"] };
            if (!acc[groupCode]) acc[groupCode] = [];
            acc[groupCode].push(entry);
            return acc;
        }, {});
    }

    let partnerList1 = null;
    let partnerList2 = null;
    if (groupCode1){
        partnerList1 = await apiCaller.PartnersLiked(groupCode1)
        // console.log(partnerList1)
    }
    if (groupCode2){
        partnerList2 = await apiCaller.PartnersLiked(groupCode2)
    }

    const sortedLiked2 = liked2.slice().sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

    likedList1.innerHTML = '';

    if (mutualList && Object.keys(mutualList).length > 0) {
        Object.keys(mutualList).forEach(groupCode => {
            const li = document.createElement("li");
            li.classList.add("groupedList");
            const groupHeader = document.createElement("h3");

            let partnerName = cookie["group codes"][groupCode] || "Unknown Partner";
            groupHeader.textContent = `Group: ${groupCode} - Partner: ${partnerName}`;
            likedList1.appendChild(groupHeader);

            liked1.forEach(item => {

                const li = document.createElement("li");
                li.classList.add("list1");

                const nameSpan = document.createElement("span");
                let selectedGroup = item["group code"] === groupCode;
                if (selectedGroup) {
                    nameSpan.textContent = item.name;
                    nameSpan.classList.add("name-item");

                    const Transfer1 = document.createElement("button");
                    Transfer1.type = "button";
                    Transfer1.textContent = "Similar names";
                    Transfer1.classList.add("Transfer1");

                    const Teleport1 = document.createElement("button");
                    Teleport1.type = "button";
                    Teleport1.textContent = "heart-button";
                    Teleport1.classList.add("Teleport1");

                    li.appendChild(nameSpan);
                    li.appendChild(Transfer1);
                    li.appendChild(Teleport1);

                    likedList1.appendChild(li)};
            });
        });
    }

    sortedLiked2.forEach(item => {

        const li = document.createElement("li");
        li.classList.add("list2");

        const nameSpan2 = document.createElement("span");
        nameSpan2.textContent = item;
        nameSpan2.classList.add("name-item");

        const Transfer2 = document.createElement("button");
        Transfer2.textContent = "Similar names";  
        Transfer2.classList.add("Transfer2");  

        const Teleport2 = document.createElement("button");
        Teleport2.textContent = "heart-button";  
        Teleport2.classList.add("Teleport2"); 

        li.appendChild(nameSpan2);
        li.appendChild(Transfer2);
        li.appendChild(Teleport2);

        likedList2.appendChild(li);
    });

    function renderPartnerList(partnerList, groupCode, container, cookie) {
        if (partnerList && partnerList.length > 0) {
            const groupHeader = document.createElement("h3");
            let partnerName = cookie["group codes"][groupCode] || "Unknown Partner";
            groupHeader.textContent = `Group: ${groupCode} - Partner: ${partnerName}`;
            container.appendChild(groupHeader);

            partnerList.forEach(item => {
                const li = document.createElement("li");
                li.classList.add("list3");

                const nameSpan3 = document.createElement("span");
                nameSpan3.textContent = item.name;
                nameSpan3.classList.add("name-item");

                const Transfer3 = document.createElement("button");
                Transfer3.textContent = "Similar names";
                Transfer3.classList.add("Transfer3");

                const Teleport3 = document.createElement("button");
                Teleport3.textContent = "heart-button";
                Teleport3.classList.add("Teleport3");

                li.appendChild(nameSpan3);
                li.appendChild(Transfer3);
                li.appendChild(Teleport3);

                container.appendChild(li);
            });
        }
    }

    renderPartnerList(partnerList1, groupCode1, likedList3, cookie);
    renderPartnerList(partnerList2, groupCode2, likedList3, cookie);

    let List1 = document.getElementById("mutualList");

    List1.addEventListener("click", function() {    
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        if (panel) {
            panel.style.display = (panel.style.display === "block") ? "none" : "block";
        }
    });

    let List2 = document.getElementById("Partnerlist");

    List2.addEventListener("click", function() {    
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        if (panel) {
            panel.style.display = (panel.style.display === "block") ? "none" : "block";
        }
    });

    let List3 = document.getElementById("Userlist");

    List3.addEventListener("click", function() {    
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        if (panel) {
            panel.style.display = (panel.style.display === "block") ? "none" : "block";
        }
    });
})();