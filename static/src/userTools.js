const getDecodedAccessToken = () => {
    return localStorage.getItem("access_token") != null ? jwt_decode(localStorage.getItem("access_token")) : null;
}

function getLoggedInUser() {
    let d_at = getDecodedAccessToken();
    if (d_at == null) return null;
    if (d_at["exp"] < (Date.now() / 1000)) {
        localStorage.removeItem("access_token");
        return null
    };
    return d_at;
}

async function register() {
    
    let username_input = document.getElementById("username_input");
    let email_input = document.getElementById("email_input");
    let password_input = document.getElementById("password_input");
    let passwordc_input = document.getElementById("passwordc_input");

    if (password_input.value != passwordc_input.value) return alert("Passwords do not match.")

    const res = await (await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        redirect: 'manual',
        body: JSON.stringify({
            username: username_input.value,
            email: email_input.value,
            password: password_input.value
        })
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
    } else {
        localStorage.setItem("access_token", res["access_token"]);
        window.location.href = "/home";
    };

}

async function login() {
    
    let username_input = document.getElementById("username_input");
    let password_input = document.getElementById("password_input");

    const res = await (await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        redirect: 'manual',
        body: JSON.stringify({
            username: username_input.value,
            password: password_input.value
        })
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
    } else {
        localStorage.setItem("access_token", res["access_token"]);
        window.location.href = "/home";
    };

}

async function logout() {
    
    localStorage.removeItem("access_token");
    alert("Successfully logged out.");
    window.location.href = "/login";
    
}

async function getProfile(user_id) {
    
    const res = await (await fetch('/get-profile/' + user_id, {
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
        return res["user"];
    };
    
}

async function updateProfile() {

    let new_password_input = document.getElementById("new_password_input");
    let new_passwordc_input = document.getElementById("new_passwordc_input");
    let old_password_input = document.getElementById("old_password_input");
    let profile_icon_select = document.getElementById("profile_icon_select");

    if (new_password_input.value != new_passwordc_input.value) return alert("Passwords do not match.");
    if (old_password_input.value == "") return alert("Old password is needed to confirm changes.");

    const res = await (await fetch('/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem("access_token")
        },
        redirect: 'manual',
        body: JSON.stringify({
            new_password: new_password_input.value,
            old_password: old_password_input.value,
            profile_icon: profile_icon_select.value
        })
    })).json();

    if (res["error"] != undefined) {
        alert(res["error"]);
    } else {
        alert("Profile updated.");
        window.location.reload();
    };

}