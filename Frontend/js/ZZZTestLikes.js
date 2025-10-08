// TODO: Delete this whole file?

let allNamesData = [];  // will hold JSON data after loading

async function loadNamesData(filepath) {
  const response = await fetch(filepath);
  if (!response.ok) throw new Error('Failed to fetch JSON');
  const json = await response.json();
  return json;
}

function populateList(listElement, names, transferClass, teleportClass) {
  listElement.innerHTML = ''; // clear existing items
  const sortedNames = names.slice().sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

  sortedNames.forEach(item => {
    const li = document.createElement("li");
    li.classList.add("list-item-wrapper");

    const nameSpan = document.createElement("span");
    nameSpan.textContent = item;
    nameSpan.classList.add("name-item", transferClass);

    const TransferBtn = document.createElement("button");
    TransferBtn.textContent = "Similar names";
    TransferBtn.classList.add(transferClass);

    const TeleportBtn = document.createElement("button");
    TeleportBtn.textContent = "heart-button";
    TeleportBtn.classList.add(teleportClass);

    li.appendChild(nameSpan);
    li.appendChild(TransferBtn);
    li.appendChild(TeleportBtn);

    listElement.appendChild(li);
  });
}

const likedList1 = document.getElementById("likedList1");
const likedList2 = document.getElementById("likedList2");
const likedList3 = document.getElementById("likedList3");

const mutualHeader = document.getElementById("mutualList");
const partnerHeader = document.getElementById("Partnerlist");
const userHeader = document.getElementById("Userlist");

let mutualLoaded = false;
let partnerLoaded = false;
let userLoaded = false;

loadNamesData('../swipeTest.json')
  .then(data => {
    allNamesData = data;
    // Now data is ready, but don't populate yet — wait for clicks

    mutualHeader.addEventListener("click", () => {
      mutualHeader.classList.toggle("active");
      const panel = mutualHeader.nextElementSibling;
      if (!panel) return;
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";

        if (!mutualLoaded) {
          // For example, show all names that are "mutual" liked
          // Here just showing all names as example:
          const allNames = allNamesData.map(item => item.name);
          populateList(likedList1, allNames, "Transfer1", "Teleport1");
          mutualLoaded = true;
        }
      }
    });

    partnerHeader.addEventListener("click", () => {
      partnerHeader.classList.toggle("active");
      const panel = partnerHeader.nextElementSibling;
      if (!panel) return;
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";

        if (!partnerLoaded) {
          // Filter or pick data relevant to partner list here
          const partnerNames = allNamesData.filter(item => /* your filter logic */ false)
            .map(item => item.name);
          populateList(likedList2, partnerNames, "Transfer2", "Teleport2");
          partnerLoaded = true;
        }
      }
    });

    userHeader.addEventListener("click", () => {
      userHeader.classList.toggle("active");
      const panel = userHeader.nextElementSibling;
      if (!panel) return;
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";

        if (!userLoaded) {
          // Filter or pick data relevant to user list here
          const userNames = allNamesData.filter(item => /* your filter logic */ false)
            .map(item => item.name);
          populateList(likedList3, userNames, "Transfer3", "Teleport3");
          userLoaded = true;
        }
      }
    });

  })
  .catch(err => {
    console.error('Error loading JSON:', err);
  });
