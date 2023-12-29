async function openTicket() {
    
    let ticket_title_input = document.getElementById("ticket_title_input");
    let message_input = document.getElementById("message_input");

    const res = await (await fetch('/ticket/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        },
        redirect: 'manual',
        body: JSON.stringify({
            ticket_title: ticket_title_input.value,
            message: message_input.value
        })
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
    } else {
        window.location.href = "/ticket/" + res["ticket_id"];
    };

}

async function getTicket(ticket_id) {
    
    const res = await (await fetch('/get-ticket/' + ticket_id, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        }
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
        return false;
    } else {
        return res;
    };

}

async function getOpenTicketsByUserID(user_id) {

    const res = await (await fetch('/get-open-tickets/' + user_id, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        }
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
        return [];
    } else {
        return res["tickets"];
    };

}

async function getClosedTicketsByUserID(user_id) {

    const res = await (await fetch('/get-closed-tickets/' + user_id, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        }
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
        return [];
    } else {
        return res["tickets"];
    };

}

async function getUnclaimedTickets() {

    const res = await (await fetch('/get-unclaimed-tickets', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        }
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
        return [];
    } else {
        return res["tickets"];
    };

}

async function sendMessage(message_input=document.getElementById("message_input").value) {

    const res = await (await fetch('/ticket/' + ticketID, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        },
        body: JSON.stringify({
            message: message_input
        })
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
        return [];
    } else {
        window.location.reload();
        return res;
    }
    
}

async function getMessages(ticket_id) {
    
    const res = await (await fetch('/get-messages/' + ticket_id, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        }
    })).json();
    
    if (res["error"] != undefined) {
        alert(res["error"]);
        return [];
    } else {
        return res["message_list"];
    };

}