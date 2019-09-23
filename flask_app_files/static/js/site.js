document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn_start').addEventListener('click', droneStart);
    document.getElementById('btn_finish').addEventListener('click', droneFinish);
});

function droneStart() {
    const url = '/start';

    const form = document.getElementById('submission');
    const data = {};
    data.name = document.getElementById('name').value;
    data.group = document.getElementById('group').value;
    data.email = document.getElementById('email').value;
    data.college = document.getElementById('college').value;
    data.major = document.getElementById('major').value;

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

function droneFinish() {

}