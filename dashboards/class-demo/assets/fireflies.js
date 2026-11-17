// Gold fireflies drifting behind the dashboard. Dash loads every .js file in
// assets/ automatically. The canvas sits behind the page content and ignores
// clicks, so it never covers a figure, control, or table.
(function () {
    var SPEED = 0.55;          // overall drift speed (lower is slower)
    var CELL_W = 52;           // one firefly per CELL_W x CELL_H pixels
    var CELL_H = 70;
    var MAX_FLIES = 320;
    var TAU = Math.PI * 2;

    function start() {
        if (document.getElementById('firefly-canvas')) return;
        var cv = document.createElement('canvas');
        cv.id = 'firefly-canvas';
        cv.setAttribute('aria-hidden', 'true');
        document.body.insertBefore(cv, document.body.firstChild);
        var ctx = cv.getContext('2d');
        var W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
        var flies = [];

        var seed = 7;
        function rnd() {
            seed = (seed * 16807) % 2147483647;
            return (seed - 1) / 2147483646;
        }

        function pickSize() {
            var r = rnd();
            if (r < 0.45) return 0.6 + rnd() * 0.9;
            if (r < 0.80) return 1.5 + rnd() * 1.3;
            if (r < 0.95) return 2.8 + rnd() * 1.4;
            return 4.2 + rnd() * 1.8;
        }

        function makeFlies() {
            seed = 7;
            flies = [];
            var cols = Math.max(6, Math.round(W / CELL_W));
            var rows = Math.max(4, Math.round(H / CELL_H));
            while (cols * rows > MAX_FLIES) {
                if (cols >= rows) cols--; else rows--;
            }
            for (var r = 0; r < rows; r++) {
                for (var c = 0; c < cols; c++) {
                    var size = pickSize();
                    var k = (size - 0.6) / 5.4;
                    flies.push({
                        u: (c + 0.15 + rnd() * 0.7) / cols,
                        v: (r + 0.15 + rnd() * 0.7) / rows,
                        ax: 18 + rnd() * 40, ay: 14 + rnd() * 34,
                        fx: 0.00005 + rnd() * 0.00009, fy: 0.00006 + rnd() * 0.0001,
                        fx2: 0.00013 + rnd() * 0.0002, fy2: 0.00011 + rnd() * 0.00018,
                        px: rnd() * TAU, py: rnd() * TAU, px2: rnd() * TAU, py2: rnd() * TAU,
                        drift: -(0.0015 + rnd() * 0.003),
                        size: size,
                        halo: 5 + size * 4.5,
                        bright: 0.5 + k * 0.5,
                        bf: 0.00035 + rnd() * 0.0007,
                        bp: rnd() * TAU,
                        tf: 0.0035 + rnd() * 0.005,
                        tp: rnd() * TAU,
                        glint: size > 1.6 || rnd() < 0.25,
                        rot: rnd() < 0.5 ? 0 : Math.PI / 4
                    });
                }
            }
        }

        function resize() {
            W = window.innerWidth;
            H = window.innerHeight;
            cv.width = Math.round(W * dpr);
            cv.height = Math.round(H * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            makeFlies();
        }

        function wrap(v, m) { return ((v % m) + m) % m; }

        function ray(x, y, len, ang, a, w) {
            var dx = Math.cos(ang) * len, dy = Math.sin(ang) * len;
            var g = ctx.createLinearGradient(x - dx, y - dy, x + dx, y + dy);
            g.addColorStop(0, 'rgba(255,236,170,0)');
            g.addColorStop(0.5, 'rgba(255,252,232,' + a + ')');
            g.addColorStop(1, 'rgba(255,236,170,0)');
            ctx.strokeStyle = g;
            ctx.lineWidth = w;
            ctx.beginPath();
            ctx.moveTo(x - dx, y - dy);
            ctx.lineTo(x + dx, y + dy);
            ctx.stroke();
        }

        function draw(t, rt) {
            ctx.clearRect(0, 0, W, H);
            var pad = 40;
            ctx.lineCap = 'round';
            for (var i = 0; i < flies.length; i++) {
                var f = flies[i];
                var x = f.u * W + f.ax * Math.sin(t * f.fx * TAU + f.px) + f.ax * 0.4 * Math.sin(t * f.fx2 * TAU + f.px2);
                var y = f.v * H + f.ay * Math.sin(t * f.fy * TAU + f.py) + f.ay * 0.4 * Math.sin(t * f.fy2 * TAU + f.py2) + f.drift * t;
                x = wrap(x + pad, W + pad * 2) - pad;
                y = wrap(y + pad, H + pad * 2) - pad;
                var s = Math.sin(t * f.bf * TAU + f.bp);
                var glow = 0.2 + 0.8 * Math.pow(Math.max(0, s), 2);
                var twinkle = 0.7 + 0.3 * Math.sin(rt * f.tf + f.tp) * Math.sin(rt * f.tf * 1.7 + f.tp * 2);
                var a = Math.min(1, f.bright * glow * twinkle * 1.1);
                var hr = f.halo * (0.75 + glow * 0.5);

                var g = ctx.createRadialGradient(x, y, 0, x, y, hr);
                g.addColorStop(0, 'rgba(255,214,110,' + (0.55 * a) + ')');
                g.addColorStop(0.35, 'rgba(240,186,60,' + (0.26 * a) + ')');
                g.addColorStop(1, 'rgba(240,186,60,0)');
                ctx.fillStyle = g;
                ctx.beginPath(); ctx.arc(x, y, hr, 0, TAU); ctx.fill();

                var cg = ctx.createRadialGradient(x, y, 0, x, y, f.size * 1.7);
                cg.addColorStop(0, 'rgba(255,254,242,' + Math.min(1, a * 1.15) + ')');
                cg.addColorStop(0.55, 'rgba(255,226,135,' + (0.85 * a) + ')');
                cg.addColorStop(1, 'rgba(230,170,50,0)');
                ctx.fillStyle = cg;
                ctx.beginPath(); ctx.arc(x, y, f.size * 1.7, 0, TAU); ctx.fill();

                if (f.glint && glow > 0.45) {
                    var ga = Math.min(1, (glow - 0.45) / 0.55) * twinkle * f.bright;
                    var len = f.size * (3.5 + 3 * glow);
                    ray(x, y, len, f.rot, ga * 0.95, Math.max(0.6, f.size * 0.28));
                    ray(x, y, len, f.rot + Math.PI / 2, ga * 0.95, Math.max(0.6, f.size * 0.28));
                    if (f.size > 2.6) {
                        ray(x, y, len * 0.55, f.rot + Math.PI / 4, ga * 0.55, 0.6);
                        ray(x, y, len * 0.55, f.rot + 3 * Math.PI / 4, ga * 0.55, 0.6);
                    }
                }
            }
        }

        resize();
        window.addEventListener('resize', resize);
        var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (still) { draw(3000, 3000); return; }
        function loop(t) { draw(t * SPEED, t); requestAnimationFrame(loop); }
        requestAnimationFrame(loop);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
