$("#get_started")
    .click(() => {
        $("#enter_api").fadeOut(500);
        $("#get_started")
            .fadeOut(500, () => {
                $("#continue_btn")
                    .hide()
                    .fadeIn(500);

                switch_block(_current_block);
            });
    });

$("#enter_api")
    .click(() => {
        $("#get_started").fadeOut(500);
        $("#enter_api")
            .fadeOut(500, () => {
                $("#continue_btn")
                    .hide()
                    .fadeIn(500);

                switch_block("api_id");
            });
    });

function isInt(value) {
    var x = parseFloat(value);
    return !isNaN(value) && (x | 0) === x;
}

function isValidPhone(p) {
    var phoneRe = /^[+]?\d{11,13}$/;
    return phoneRe.test(p);
}

function finish_login() {
    fetch("/finishLogin", {
            method: "POST",
            credentials: "include"
        })
        .then(function (response) {
            if (!response.ok) {
                error_state();
                error_message("Login confirmation error");
            } else {
                Swal.fire({
                    "icon": "success",
                    "text": "Auth successful!",
                    "timer": 1000
                });
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        })
        .catch(function (response) {
            error_state();
            error_message("Login confirmation error");
        });
}

function tg_code() {
    fetch("/tgCode", {
            method: "POST",
            body: _tg_pass + "\n" + _phone + "\n" + _2fa_pass
        })
        .then(function (response) {
            if (!response.ok) {
                console.log(response);
                if (response.status == 403) {
                    error_state();
                    Swal.showValidationMessage("Code is incorrect!");
                } else if (response.status == 401) {
                    switch_block("2fa");
                } else if (response.status == 404) {
                    error_state();
                    Swal.showValidationMessage("Code is expired!");
                } else {
                    error_state();
                    Swal.showValidationMessage("Internal server error");
                }
            } else {
                finish_login();
            }
        })
        .catch(error => {
            Swal.showValidationMessage(
                "Auth failed: " + error.toString()
            )
        })
}

function switch_block(block) {
    cnt_btn.setAttribute("current-step", block);
   try {
        $("#block_" + _current_block)
            .fadeOut(() => {
                $("#block_" + block)
                    .hide()
                    .fadeIn();
            });
    } catch {
        $("#block_" + block)
            .hide()
            .fadeIn();
    }

    _current_block = block;
}

function error_message(message) {
    Swal.fire({
        "icon": "error",
        "title": message
    });
}

function error_state() {
    $(".bg").addClass("red_state");
    cnt_btn.disabled = true;
    setTimeout(() => {
        cnt_btn.disabled = false;
        $(".bg").removeClass("red_state");
    }, 1000);
}

var _api_id = "",
    _api_hash = "",
    _phone = "",
    _2fa_pass = "",
    _tg_pass = "",
_current_block = skip_creds ? "phone" : "api_id";

const cnt_btn = document.querySelector("#continue_btn");
cnt_btn.onclick = (e) => {
    if (cnt_btn.disabled) return;

    let step = cnt_btn.getAttribute("current-step");
    if (step == "api_id") {
        let api_id = document.querySelector("#api_id")
            .value;
        if (api_id.length < 4 || !isInt(api_id)) {
            error_state();
            return;
        }

        _api_id = parseInt(api_id);
        switch_block("api_hash");

        return;
    }

    if (step == "api_hash") {
        let api_hash = document.querySelector("#api_hash")
            .value;
        if (api_hash.length != 32) {
            error_state();
            return;
        }

        _api_hash = api_hash;
        fetch("/setApi", {
                method: "PUT",
                body: _api_hash + _api_id,
                credentials: "include"
            })
            .then(function (response) {
                if (!response.ok) {
                    error_state();
                    error_message("Error occured while saving credentials")
                } else {
                    switch_block("phone");
                }
            })
            .catch(function (response) {

            });

        return;
    }

    if (step == "phone") {
        let phone = document.querySelector("#phone").value;
        if (!isValidPhone(phone)) {
            error_state();
            return;
        }

        _phone = phone;
        fetch("/sendTgCode", {
                method: "POST",
                body: _phone,
                credentials: "include"
            })
            .then(function (response) {
                if (!response.ok) {
                    error_state();
                    error_message("Code send failed");
                } else {
                    Swal.fire({
                        title: "Enter received code",
                        input: "text",
                        inputAttributes: {
                            autocapitalize: "off"
                        },
                        showCancelButton: false,
                        confirmButtonText: "Confirm",
                        showLoaderOnConfirm: true,
                        preConfirm: (login) => {
                            _tg_pass = login
                            tg_code();
                        },
                        allowOutsideClick: () => !Swal.isLoading()
                    })
                }
            })
            .catch(function (error) {
                error_state();
                error_message("Code send failed");
            });
    }

    if (step == "2fa") {
        let _2fa = document.querySelector("#_2fa")
            .value;
        _2fa_pass = _2fa;
        tg_code();
        return
    }

    if (step == "config") {

    }
}