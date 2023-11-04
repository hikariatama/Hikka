function auth(c) {
  $(".main").fadeOut(250),
    setTimeout(() => {
      $(".auth")
        .hide()
        .fadeIn(250, () => {
          $("#tg_icon").html(""),
            bodymovin.loadAnimation({
              container: document.getElementById("tg_icon"),
              renderer: "canvas",
              loop: !0,
              autoplay: !0,
              path: "https://assets9.lottiefiles.com/packages/lf20_bgqoyj8l.json",
              rendererSettings: { clearCanvas: !0 },
            });
        }),
        fetch("/web_auth", {
          method: "POST",
          credentials: "include",
          timeout: 25e4,
        })
          .then((b) => b.text())
          .then((a) =>
            "TIMEOUT" == a
              ? (error_message(
                  "Code waiting timeout exceeded. Reload page and try again.",
                ),
                void $(".auth").fadeOut(250))
              : a.startsWith("huikka_")
              ? ($.cookie("session", a),
                (auth_required = !1),
                $(".authorized").hide().fadeIn(100),
                $(".auth").fadeOut(250, () => {
                  $(".installation").fadeIn(250);
                }),
                void c())
              : void 0,
          );
    }, 250);
}
var qr_interval = null,
  qr_login = !1,
  old_qr_sizes = [
    document.querySelector(".qr_inner").style.width,
    document.querySelector(".qr_inner").style.height,
  ];
(document.querySelector(".qr_inner").style.width = "100px"),
  (document.querySelector(".qr_inner").style.height = "100px");
function login_qr() {
  $("#continue_btn").fadeOut(100),
    $("#denyqr").hide().fadeIn(250),
    $(".title, .description").fadeOut(250),
    fetch("/init_qr_login", { method: "POST", credentials: "include" })
      .then((b) => b.text())
      .then((c) => {
        const d = new QRCodeStyling({
          width: window.innerHeight / 3,
          height: window.innerHeight / 3,
          type: "svg",
          data: c,
          dotsOptions: { type: "rounded" },
          cornersSquareOptions: { type: "extra-rounded" },
          backgroundOptions: { color: "transparent" },
          imageOptions: { imageSize: 0.4, margin: 8 },
          qrOptions: { errorCorrectionLevel: "M" },
        });
        (document.querySelector(".qr_inner").innerHTML = ""),
          (document.querySelector(".qr_inner").style.width = old_qr_sizes[0]),
          (document.querySelector(".qr_inner").style.height = old_qr_sizes[1]),
          d.append(document.querySelector(".qr_inner")),
          (qr_interval = setInterval(() => {
            fetch("/get_qr_url", { method: "POST", credentials: "include" })
              .then((b) => b.text())
              .then((b) =>
                "SUCCESS" == b || "2FA" == b
                  ? ($("#block_qr_login").fadeOut(250),
                    $("#denyqr").fadeOut(250),
                    $("#continue_btn, .title, .description").hide().fadeIn(250),
                    "SUCCESS" == b && switch_block("custom_bot"),
                    "2FA" == b && (show_2fa(), (qr_login = !0)),
                    void clearInterval(qr_interval))
                  : void d.update({ data: b }),
              );
          }, 1250));
      });
}
$("#get_started").click(() => {
  fetch("/can_add", { method: "POST", credentials: "include" }).then((b) =>
    b.ok
      ? auth_required
        ? auth(() => {
            $("#get_started").click();
          })
        : void ($("#continue_btn").hide().fadeIn(250),
          $("#denyqr").hide(),
          $("#enter_api").fadeOut(250),
          $("#get_started").fadeOut(250, () => {
            switch_block(_current_block);
          }))
      : void show_eula(),
  );
}),
  $("#enter_api").click(() =>
    auth_required
      ? auth(() => {
          $("#enter_api").click();
        })
      : void ($("#get_started").fadeOut(250),
        $("#enter_api").fadeOut(250, () => {
          $("#continue_btn").hide().fadeIn(250), switch_block("api_id");
        })),
  );
function isInt(c) {
  var a = parseFloat(c);
  return !isNaN(c) && (0 | a) === a;
}
function isValidPhone(b) {
  return /^[+]?\d{11,13}$/.test(b);
}
function finish_login() {
  fetch("/finish_login", { method: "POST", credentials: "include" })
    .then(() => {
      $(".installation").fadeOut(2e3),
        setTimeout(() => {
          $("#installation_icon").html(""),
            bodymovin.loadAnimation({
              container: document.getElementById("installation_icon"),
              renderer: "canvas",
              loop: !0,
              autoplay: !0,
              path: "https://assets1.lottiefiles.com/packages/lf20_n3jgitst.json",
              rendererSettings: { clearCanvas: !0 },
            }),
            $(".finish_block").fadeIn(250);
        }, 2e3);
    })
    .catch((b) => {
      error_state(), error_message("Login confirmation error: " + b.toString());
    });
}
function show_2fa() {
  $(".auth-code-form")
    .hide()
    .fadeIn(250, () => {
      $("#monkey-close").html(""),
        (anim = bodymovin.loadAnimation({
          container: document.getElementById("monkey-close"),
          renderer: "canvas",
          loop: !0,
          autoplay: !0,
          path: "https://assets1.lottiefiles.com/packages/lf20_eg88dyk9.json",
          rendererSettings: { clearCanvas: !0 },
        })),
        anim.addEventListener("complete", () => {
          setTimeout(() => {
            anim.goToAndPlay(0);
          }, 2e3);
        });
    }),
    $(".code-input").removeAttr("disabled"),
    $(".code-input").attr("inputmode", "text"),
    $(".code-input").attr("autocomplete", "off"),
    $(".code-input").attr("autocorrect", "off"),
    $(".code-input").attr("autocapitalize", "off"),
    $(".code-input").attr("spellcheck", "false"),
    $(".code-input").attr("type", "password"),
    $(".enter").hasClass("tgcode") && $(".enter").removeClass("tgcode"),
    $(".code-caption").html(
      "Enter your Telegram 2FA password, then press <span style='color: #dc137b;'>Enter</span>",
    ),
    cnt_btn.setAttribute("current-step", "2fa"),
    $("#monkey").hide(),
    $("#monkey-close").hide().fadeIn(100),
    (_current_block = "2fa");
}
function show_eula() {
  $(".main").fadeOut(250),
    $(".eula-form")
      .hide()
      .fadeIn(250, () => {
        $("#law").html(""),
          (anim = bodymovin.loadAnimation({
            container: document.getElementById("law"),
            renderer: "canvas",
            loop: !0,
            autoplay: !0,
            path: "https://static.dan.tatar/forbidden.json",
            rendererSettings: { clearCanvas: !0 },
          }));
      });
}
function tg_code(b = !1) {
  return b && qr_login
    ? void fetch("/qr_2fa", {
        method: "POST",
        credentials: "include",
        body: _2fa_pass,
      }).then((b) => {
        b.ok
          ? ($(".auth-code-form").fadeOut(),
            $("#block_phone").fadeOut(),
            switch_block("custom_bot"))
          : ($(".code-input").removeAttr("disabled"),
            b.text().then((b) => {
              error_state(), Swal.fire("Error", b, "error");
            }));
      })
    : void fetch("/tg_code", {
        method: "POST",
        body: `${_tg_pass}\n${_phone}\n${_2fa_pass}`,
      })
        .then((b) => {
          b.ok
            ? ($(".auth-code-form").fadeOut(),
              $("#block_phone").fadeOut(),
              switch_block("custom_bot"))
            : 401 == b.status
            ? show_2fa()
            : ($(".code-input").removeAttr("disabled"),
              b.text().then((b) => {
                error_state(), Swal.fire("Error", b, "error");
              }));
        })
        .catch((b) => {
          Swal.showValidationMessage(`Auth failed: ${b.toString()}`);
        });
}
function switch_block(b) {
  cnt_btn.setAttribute("current-step", b);
  try {
    $(`#block_${_current_block}`).fadeOut(() => {
      $(`#block_${b}`).hide().fadeIn();
    });
  } catch {
    $(`#block_${b}`).hide().fadeIn();
  }
  (_current_block = b), "qr_login" == _current_block && login_qr();
}
function error_message(b) {
  Swal.fire({ icon: "error", title: b });
}
function error_state() {
  $("body").addClass("red_state"),
    (cnt_btn.disabled = !0),
    setTimeout(() => {
      (cnt_btn.disabled = !1), $("body").removeClass("red_state");
    }, 1e3);
}
var _api_id = "",
  _api_hash = "",
  _phone = "",
  _2fa_pass = "",
  _tg_pass = "",
  _current_block = skip_creds ? "qr_login" : "api_id";
function is_phone() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|BB|PlayBook|IEMobile|Windows Phone|Kindle|Silk|Opera Mini/i.test(
    navigator.userAgent,
  );
}
is_phone() && "qr_login" == _current_block && (_current_block = "phone");
const cnt_btn = document.querySelector("#continue_btn");
function process_next() {
  let b = cnt_btn.getAttribute("current-step");
  if ("api_id" == b) {
    let b = document.querySelector("#api_id").value;
    return 4 > b.length || !isInt(b)
      ? void error_state()
      : ((_api_id = parseInt(b, 10)), void switch_block("api_hash"));
  }
  if ("api_hash" == b) {
    let b = document.querySelector("#api_hash").value;
    return 32 == b.length
      ? ((_api_hash = b),
        void fetch("/set_api", {
          method: "PUT",
          body: _api_hash + _api_id,
          credentials: "include",
        })
          .then((b) => b.text())
          .then((b) => {
            "ok" == b
              ? switch_block(is_phone() ? "phone" : "qr_login")
              : (error_state(), error_message(b));
          })
          .catch((b) => {
            error_state(),
              error_message(
                "Error occured while saving credentials: " + b.toString(),
              );
          }))
      : void error_state();
  }
  if ("phone" == b) {
    let b = document.querySelector("#phone").value;
    if (!isValidPhone(b)) return void error_state();
    (_phone = b),
      fetch("/send_tg_code", {
        method: "POST",
        body: _phone,
        credentials: "include",
      })
        .then((b) => {
          b.ok
            ? ($(".auth-code-form")
                .hide()
                .fadeIn(250, () => {
                  $("#monkey").html(""),
                    (anim2 = bodymovin.loadAnimation({
                      container: document.getElementById("monkey"),
                      renderer: "canvas",
                      loop: !1,
                      autoplay: !0,
                      path: "https://assets8.lottiefiles.com/private_files/lf30_t52znxni.json",
                      rendererSettings: { clearCanvas: !0 },
                    })),
                    anim2.addEventListener("complete", () => {
                      setTimeout(() => {
                        anim2.goToAndPlay(0);
                      }, 2e3);
                    });
                }),
              $(".code-input").removeAttr("disabled"),
              $(".enter").addClass("tgcode"),
              $(".code-caption").text(
                "Enter the code you recieved in Telegram",
              ),
              $(".code-input").attr("autocomplete", "off"),
              $(".code-input").attr("autocorrect", "off"),
              $(".code-input").attr("autocapitalize", "off"),
              $(".code-input").attr("spellcheck", "false"),
              $(".code-input").attr("type", "number"),
              cnt_btn.setAttribute("current-step", "code"),
              (_current_block = "code"))
            : 403 == b.status
            ? show_eula()
            : b.text().then((b) => {
                error_state(), error_message(b);
              });
        })
        .catch((b) => {
          error_state(), error_message("Code send failed: " + b.toString());
        });
  }
  if ("2fa" == b) {
    let b = document.querySelector("#_2fa").value;
    return (_2fa_pass = b), void tg_code();
  }
  if ("custom_bot" == b) {
    let b = document.querySelector("#custom_bot").value;
    return "" != b && (!b.toLowerCase().endsWith("bot") || 5 > b.length)
      ? void Swal.fire({
          icon: "error",
          title: "Bot username invalid",
          text: "It must end with `bot` and be at least 5 symbols in length",
        })
      : "" == b
      ? void finish_login()
      : void fetch("/custom_bot", {
          method: "POST",
          credentials: "include",
          body: b,
        })
          .then((b) => b.text())
          .then((b) =>
            "OCCUPIED" == b
              ? void Swal.fire({
                  icon: "error",
                  title: "This bot username is already occupied!",
                })
              : void finish_login(),
          )
          .catch((b) => {
            error_state(),
              error_message("Custom bot setting error: " + b.toString());
          });
  }
}
(cnt_btn.onclick = () =>
  cnt_btn.disabled
    ? void 0
    : auth_required
    ? auth(() => {
        cnt_btn.click();
      })
    : void process_next()),
  $("#denyqr").on("click", () => {
    qr_interval && clearInterval(qr_interval),
      $("#denyqr").fadeOut(250),
      $("#continue_btn, .title, .description").hide().fadeIn(250),
      switch_block("phone");
  }),
  $(".installation input").on("keyup", (b) =>
    cnt_btn.disabled
      ? void 0
      : auth_required
      ? auth(() => {
          cnt_btn.click();
        })
      : void (("Enter" === b.key || 13 === b.keyCode) && process_next()),
  ),
  $(".code-input").on("keyup", (b) => {
    if ("code" == _current_block && 5 == $(".code-input").val().length)
      (_tg_pass = $(".code-input").val()),
        $(".code-input").attr("disabled", "true"),
        $(".code-input").val(""),
        tg_code();
    else if (
      "2fa" == _current_block &&
      ("Enter" === b.key || 13 === b.keyCode)
    ) {
      let b = $(".code-input").val();
      (_2fa_pass = b),
        $(".code-input").attr("disabled", "true"),
        $(".code-input").val(""),
        tg_code(!0);
    }
  }),
  $(".enter").on("click", () => {
    if ("2fa" == _current_block) {
      let b = $(".code-input").val();
      (_2fa_pass = b),
        $(".code-input").attr("disabled", "true"),
        $(".code-input").val(""),
        tg_code(!0);
    }
  }),
  $(document).ready(() => {
    new Sakura("body");
  });
