$(document).ready(function () {
    $(".mountains")
        .hide()
        .delay(2000)
        .fadeIn(500);
});

// Adapted from https://codepen.io/sinthetyc/pen/kazPzY
var canvas, c, w, h,
    twoPI = Math.PI * 2,
    mX, mY,
    resize = true,
    mousemove = true,
    per = {
        x: 0,
        y: 0
    },
    mtn, trackmouse = false;

function animate() {
    if (!trackmouse) {
        per.x += per.step;
        if (per.x > w)
            per.step = -per.step;
        if (per.x < 0)
            per.step = -per.step;
    }

    c.globalCompositeOperation = "source-over";
    c.fillStyle = "rgba(20,20,20,0.2)";
    c.fillRect(0, 0, w, h);
    mtn.draw();
}

function Mountains(peaks, seed) {
    var points = [];
    this.init = function () {
        var step = w / peaks,
            y = 0;

        points.push({
            x: 0,
            y: y
        });
        for (var i = 1; i <= peaks; i++) {
            y = y + (Math.random() * 20) - 10;
            points.push({
                x: i * step,
                y: y
            });
        }
    };
    this.draw = function () {
        c.save();
        c.fillStyle = "rgba(20,20,20,1)";
        c.beginPath();
        c.moveTo(points[0].x, h / 2 - points[0].y);
        for (var p = 1; p < points.length; p++) {
            c.lineTo(points[p].x, h / 2 - points[p].y);
        }
        c.lineTo(w, h);
        c.lineTo(0, h);
        c.closePath();
        c.fill();
        c.restore();

        c.globalCompositeOperation = "lighter";
        c.fillStyle = "rgba(30, 5, 30, 0.1)";
        for (var p = 0; p < points.length - 1; p++) {
            var va1 = Math.atan2(h / 2 - points[p].y - per.y, points[p].x - per.x),
                va2 = Math.atan2(h / 2 - points[p + 1].y - per.y, points[p + 1].x - per.x);

            c.beginPath();
            c.moveTo(points[p].x, h / 2 - points[p].y);
            c.lineTo(points[p + 1].x, h / 2 - points[p + 1].y);
            c.lineTo(points[p + 1].x + Math.cos(va2) * w, h / 2 - points[p + 1].y + Math.sin(va2) * w);
            c.lineTo(points[p].x + Math.cos(va1) * w, h / 2 - points[p].y + Math.sin(va1) * w);
            c.closePath();
            c.fill();
        }
    };

    this.init();
}

canvas = document.querySelector('.mountains')
w = canvas.width = window.innerWidth;
h = canvas.height = window.innerHeight;
c = canvas.getContext('2d');
document.body.appendChild(canvas);

per = {
    x: w / 2,
    y: h / 2,
    step: 1
}

mtn = new Mountains(100, "10");
window.setInterval(animate, 30);
