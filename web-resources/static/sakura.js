// https://raw.githubusercontent.com/jhammann/sakura/master/src/sakura.js
const Sakura = function (t, e) {
  if (void 0 === t) throw new Error("No selector present. Define an element.");
  this.el = document.querySelector(t);
  var i, n;
  function a(t) {
    return t[Math.floor(Math.random() * t.length)];
  }
  function s(t, e) {
    return Math.floor(Math.random() * (e - t + 1)) + t;
  }
  (this.settings =
    ((i = {
      className: "sakura",
      fallSpeed: 1,
      maxSize: 14,
      minSize: 10,
      delay: 300,
      colors: [
        {
          gradientColorStart: "rgba(255, 183, 197, 0.9)",
          gradientColorEnd: "rgba(255, 197, 208, 0.9)",
          gradientColorDegree: 120,
        },
      ],
    }),
    (n = e),
    Object.keys(i).forEach((t) => {
      n && Object.prototype.hasOwnProperty.call(n, t) && (i[t] = n[t]);
    }),
    i)),
    (this.el.style.overflowX = "hidden");
  const o = ["webkit", "moz", "MS", "o", ""];
  function r(t, e, i) {
    for (let n = 0; n < o.length; n += 1) {
      let a = e;
      o[n] || (a = e.toLowerCase()), t.addEventListener(o[n] + a, i, !1);
    }
  }
  function l(t) {
    const e = t.getBoundingClientRect();
    return (
      e.top >= 0 &&
      e.left >= 0 &&
      e.bottom <=
        (window.innerHeight || document.documentElement.clientHeight) &&
      e.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }
  (this.createPetal = () => {
    this.el.dataset.sakuraAnimId &&
      setTimeout(() => {
        window.requestAnimationFrame(this.createPetal);
      }, this.settings.delay);
    const t = [
        "sway-0",
        "sway-1",
        "sway-2",
        "sway-3",
        "sway-4",
        "sway-5",
        "sway-6",
        "sway-7",
        "sway-8",
      ],
      e = a([
        "blow-soft-left",
        "blow-medium-left",
        "blow-soft-right",
        "blow-medium-right",
      ]),
      i = a(t),
      n =
        (0.007 * document.documentElement.clientHeight +
          Math.round(5 * Math.random())) *
        this.settings.fallSpeed,
      o = [
        `fall ${n}s linear 0s 1`,
        `${e} ${(n > 30 ? n : 30) - 20 + s(0, 20)}s linear 0s infinite`,
        `${i} ${s(2, 4)}s linear 0s infinite`,
      ].join(", "),
      d = document.createElement("div");
    d.classList.add(this.settings.className);
    const m = s(this.settings.minSize, this.settings.maxSize),
      h = m - Math.floor(s(0, this.settings.minSize) / 3),
      c = a(this.settings.colors);
    (d.style.background = `linear-gradient(${c.gradientColorDegree}deg, ${c.gradientColorStart}, ${c.gradientColorEnd})`),
      (d.style.webkitAnimation = o),
      (d.style.animation = o),
      (d.style.borderRadius = `${s(
        this.settings.maxSize,
        this.settings.maxSize + Math.floor(10 * Math.random()),
      )}px ${s(1, Math.floor(h / 4))}px`),
      (d.style.height = `${m}px`),
      (d.style.left = `${
        Math.random() * document.documentElement.clientWidth - 100
      }px`),
      (d.style.marginTop = `${-(Math.floor(20 * Math.random()) + 15)}px`),
      (d.style.width = `${h}px`),
      r(d, "AnimationEnd", () => {
        l(d) || d.remove();
      }),
      r(d, "AnimationIteration", () => {
        l(d) || d.remove();
      }),
      this.el.appendChild(d);
  }),
    this.el.setAttribute(
      "data-sakura-anim-id",
      window.requestAnimationFrame(this.createPetal),
    );
};
(Sakura.prototype.start = function () {
  if (this.el.dataset.sakuraAnimId)
    throw new Error("Sakura is already running.");
  this.el.setAttribute(
    "data-sakura-anim-id",
    window.requestAnimationFrame(this.createPetal),
  );
}),
  (Sakura.prototype.stop = function (t = !1) {
    const e = this.el.dataset.sakuraAnimId;
    e &&
      (window.cancelAnimationFrame(e),
      this.el.setAttribute("data-sakura-anim-id", "")),
      t ||
        setTimeout(() => {
          const t = document.getElementsByClassName(this.settings.className);
          for (; t.length > 0; ) t[0].parentNode.removeChild(t[0]);
        }, this.settings.delay + 50);
  });
