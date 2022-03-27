function okteto() {
    fetch("/okteto", {
        method: "POST",
        credentials: "include",
        body: window.location.href
    })
    .then(response => response.text())
    .then((response) => {
        if(response == "WAIT") {
            setTimeout(() => {okteto();}, 5000);
        }
    })
}

okteto()
