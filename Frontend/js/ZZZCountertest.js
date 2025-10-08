// TODO: Delete this whole file?

let allNamesData = [];

async function loadNamesData(filepath) {
  const response = await fetch(filepath);
  if (!response.ok) throw new Error('Failed to fetch JSON');
  const json = await response.json();
  return json;
}

let transferCounters = {
  Transfer1: 0,
  Transfer2: 0,
  Transfer3: 0
};

function addTransferButtonListeners(transferClass) {
  const buttons = document.querySelectorAll(`button.${transferClass}`);
  buttons.forEach(button => {
    button.addEventListener('click', () => {
      transferCounters[transferClass]++;
      const nameSpan = button.parentElement.querySelector('.name-item');
      const name = nameSpan ? nameSpan.textContent : 'Unknown';

      const fullItem = allNamesData.find(item => item.name === name);

      if (fullItem) {
        console.log(`${transferClass} button clicked ${transferCounters[transferClass]} times for item:`, fullItem);
      } else {
        console.log(`Item with name "${name}" not found in data.`);
      }
    });
  });
}

function populateList(listElement, names, transferClass, teleportClass) {
  listElement.innerHTML = '';
  const sortedNames = names.slice().sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

  sortedNames.forEach(item => {
    const li = document.createElement("li");
    li.classList.add("list-item-wrapper");

    const nameSpan = document.createElement("span");
    nameSpan.textContent = item;
    nameSpan.classList.add("name-item");

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

  addTransferButtonListeners(transferClass);
}

const likedList1 = document.getElementById("likedList1");

const mutualHeader = document.getElementById("mutualList");

let mutualLoaded = false;

loadNamesData('../swipeTest.json')
  .then(data => {
    allNamesData = data;

    mutualHeader.addEventListener("click", () => {
      mutualHeader.classList.toggle("active");
      const panel = mutualHeader.nextElementSibling;
      if (!panel) return;
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";

        if (!mutualLoaded) {
          const allNames = allNamesData.map(item => item.name);
          populateList(likedList1, allNames, "Transfer1", "Teleport1");
          mutualLoaded = true;
        }
      }
    });
  })
  .catch(err => {
    console.error("Error loading names data:", err);
  });

