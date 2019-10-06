document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn_start').addEventListener('click', droneStart);
    document.getElementById('btn_cancel').addEventListener('click', droneCancel);
    document.getElementById('btn_finish').addEventListener('click', droneFinish);
});

function droneStart() {
    const name = document.getElementById('name').value;
    if (!name) {
        alert("Please enter a name.");
    }

    const my_form = document.getElementById('frm_submission');
    const formData = new FormData(my_form);
    const data = {};
    for (let pair of formData.entries()) {
        data[pair[0]] = pair[1];
    }
    const url = '/start';
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => {
        return response.json();
    })
    .then(json => {
        console.log(json);
    })
    .catch(error => {
        console.log(error.message);
    });
}

function droneCancel() {
    const url = '/cancel';
    fetch(url)
       .then(response => {
        return response.json();
    })
    .then(json => {
        console.log(json);
    })
    .catch(error => {
        console.log(error.message);
    });
}

function droneFinish() {
    const url = '/finish';
    fetch(url)
       .then(response => {
        return response.json();
    })
    .then(json => {
        console.log(json);
    })
    .catch(error => {
        console.log(error.message);
    });
}